import json
import requests
from shapely.geometry import Polygon
from shapely.geometry import Point
import cairo
from time import sleep

def getNeighbourhoods(headers):
    # function returns all neighbourhoods as dictionary
    try:
        neighbourhoods = json.loads(requests.get('https://api.upland.me/neighborhood', headers=headers).text)
    except:
        sleep(1)
        neighbourhoods = json.loads(requests.get('https://api.upland.me/neighborhood', headers=headers).text)
    else:
        sleep(10)
        neighbourhoods = json.loads(requests.get('https://api.upland.me/neighborhood', headers=headers).text)
    return neighbourhoods

def getNeighbourhood(headers, searchCity, searchNeighbourhood = None):
    # function returns specific neighbourhood as list based on a search neighbourhood and search city
    result = []
    if type(searchNeighbourhood) == dict:
        searchNeighbourhood = searchNeighbourhood['name'].upper()
    elif searchNeighbourhood:
        searchNeighbourhood = searchNeighbourhood.upper()
    searchCity = searchCity.title()
    try:
        cities = json.loads(requests.get('https://api.upland.me/city', headers=headers).text)
    except:
        sleep(1)
        cities = json.loads(requests.get('https://api.upland.me/city', headers=headers).text)
    else:
        sleep(10)
        cities = json.loads(requests.get('https://api.upland.me/city', headers=headers).text)
    for city in cities:
        if searchCity == city['name']:
            cityID = city['id']
            break
    neighbourhoods = getNeighbourhoods(headers)
    for neighbourhood in neighbourhoods:
        if (searchNeighbourhood == neighbourhood['name'] or searchNeighbourhood == None) and neighbourhood['city_id'] == cityID:
            result.append(neighbourhood)
            if not searchNeighbourhood == None:
                break
    return result

def getNeighbourhoodPoly(headers, searchCity, searchNeighbourhood = None):
    # function returns neighbourhood polygon as shapely polygon
    neighbourhoods = getNeighbourhood(headers, searchCity, searchNeighbourhood)
    neighbourhoodPoly = []
    if neighbourhoods == None:
        neighbourhoodPoly = None
    else:
        for neighbourhood in neighbourhoods:
            try:
                neighbourhoodPoly.append(Polygon(neighbourhood['boundaries']['coordinates'][0]))
            except:
                neighbourhoodPoly.append(Polygon(neighbourhood['boundaries']['coordinates'][0][0]))
    return neighbourhoodPoly

def getNeighbourhoodProperties(headers, searchCity, searchNeighbourhood = None):
    neighbourhoodPolys = getNeighbourhoodPoly(headers, searchCity, searchNeighbourhood)
    properties = []
    for neighbourhoodPoly in neighbourhoodPolys:
        properties.append(checkInNeighbourhood(neighbourhoodPoly, getProperties(headers, neighbourhoodPoly)))
    if not searchNeighbourhood == None:
        properties = properties[0]
    return properties

def checkInNeighbourhood(searchPoly, properties):    
    properties[:] = [x for x in properties if Point(float(x['centerlng']), float(x['centerlat'])).within(searchPoly)]
    return properties

def getProperties(headers, searchPoly):
    properties = []
    north = searchPoly.bounds[3]
    south = searchPoly.bounds[1]
    east = searchPoly.bounds[2]
    west = searchPoly.bounds[0]
    step = 1
    while len(properties)==0 and step < (2**4):
        for nsstep in range(0, step):
            for ewstep in range(0, step):
                try:
                    tempProps = json.loads(requests.get('https://api.upland.me/map?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)) + '&marker=true', headers=headers).text)
                except:
                    sleep(1)
                    tempProps = json.loads(requests.get('https://api.upland.me/map?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)) + '&marker=true', headers=headers).text)
                properties.extend(tempProps)
        step = step*2
        if ((north-south)/step) < 0.0001:
            step = 2**5
    prop_ids = []
    uniqueProps = []
    for prop in properties:
        if not prop['prop_id'] in prop_ids:
            prop_ids.append(prop['prop_id'])
            uniqueProps.append(prop)
    return uniqueProps

def getPropertyDetails(headers, propID):
    try:
        propDetails = json.loads(requests.get('https://api.upland.me/properties/' + str(propID), headers=headers).text)
    except:
        sleep(1)
        propDetails = json.loads(requests.get('https://api.upland.me/properties/' + str(propID), headers=headers).text)
    else:
        sleep(10)
        propDetails = json.loads(requests.get('https://api.upland.me/properties/' + str(propID), headers=headers).text)
    return propDetails

def matchCollections(headers, propID):
    try:
        collectionRaw = requests.get('https://api.upland.me/properties/match/' + str(propID), headers=headers).text
    except:
        sleep(1)
        collectionRaw = requests.get('https://api.upland.me/properties/match/' + str(propID), headers=headers).text
    else:
        sleep(10)
        collectionRaw = requests.get('https://api.upland.me/properties/match/' + str(propID), headers=headers).text
    try:
        collections = json.loads(collectionRaw)
    except:
        collections = None
    return collections

def getSaleProperties(headers, searchPoly):
    saleProperties = json.loads(requests.get('https://api.upland.me/properties/list-view?north=' + str(searchPoly.bounds[3]) + '&south=' + str(searchPoly.bounds[1]) + '&east=' + str(searchPoly.bounds[2]) + '&west=' + str(searchPoly.bounds[0]) + '&offset=0&limit=20&sort=asc', headers=headers).text)
    return saleProperties

def makeCanvas(objectsToPlot, mapHeight = 3000):
    minLat = 1000
    maxLat = -1000
    minLong = 1000
    maxLong = -1000

    for x in objectsToPlot:
        minLat = min(minLat, x.bounds[0])
        maxLat = max(maxLat, x.bounds[2])
        minLong = min(minLong, x.bounds[1])
        maxLong = max(maxLong, x.bounds[3])

    mapRatio = (maxLong - minLong) / (maxLat - minLat)
    mapWidth = mapHeight / mapRatio
    heightRatio = mapHeight / (maxLong - minLong)
    widthRatio = mapWidth / (maxLat - minLat)
    mapFactor = min(heightRatio, widthRatio)
    surface = cairo.ImageSurface(cairo.Format.ARGB32, int(mapWidth + 50), int(mapHeight + 150))
    canvas = cairo.Context(surface)
    canvas.set_source_rgb(1, 1, 1)
    canvas.paint()
    canvas.set_source_rgb(0, 0, 0)
    return (surface, canvas, mapFactor, minLat, maxLong, mapWidth)

def plotObject(canvas, mapFactor, objectToPlot, minLat, maxLong, fillColour = (1, 1, 1)):
    if type(objectToPlot) == list:
        objectToPlot = objectToPlot[0]
    for num, point in enumerate(objectToPlot.exterior.coords):
        if num == 0:
            canvas.move_to(((point[0] - minLat) * mapFactor), ((maxLong - point[1]) * mapFactor) + 100)
        else:
            canvas.line_to(((point[0] - minLat) * mapFactor), ((maxLong - point[1]) * mapFactor) + 100)
    canvas.set_source_rgb(fillColour[0], fillColour[1], fillColour[2])
    canvas.close_path()
    canvas.fill_preserve()
    canvas.set_source_rgb(0, 0, 0)
    canvas.stroke()
    return
