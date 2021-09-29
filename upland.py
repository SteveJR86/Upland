import json
import requests
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
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
    # function returns specific neighbourhoods as list based on a search city and search neighbourhood
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
    # function returns neighbourhood polygons as list of shapely polygons
    neighbourhoods = getNeighbourhood(headers, searchCity, searchNeighbourhood)
    neighbourhoodPolys = []
    if neighbourhoods == None:
        neighbourhoodPolys = None
    else:
        for neighbourhood in neighbourhoods:
            neighbourhoodPolys.append(makePoly(neighbourhood['boundaries']))
    return neighbourhoodPolys

def getNeighbourhoodProperties(headers, searchCity, searchNeighbourhood = None, models = False):
    # returns list of lists (one per neighbourhood) of properties
    neighbourhoodPolys = getNeighbourhoodPoly(headers, searchCity, searchNeighbourhood)
    properties = []
    for neighbourhoodPoly in neighbourhoodPolys:
        properties.append(checkInNeighbourhood(neighbourhoodPoly, getProperties(headers, neighbourhoodPoly, models)))
    return properties

def checkInNeighbourhood(searchPoly, properties):
    properties[:] = [x for x in properties if Point(float(x['centerlng']), float(x['centerlat'])).within(searchPoly)]
    return properties

def getProperties(headers, searchPoly, models = False):
    properties = []
    north = searchPoly.bounds[3]
    south = searchPoly.bounds[1]
    east = searchPoly.bounds[2]
    west = searchPoly.bounds[0]
    step = 1
    maxStepSize = 0.01
    runFlag = True
    while runFlag:
        properties = []
        for nsstep in range(0, step):
            for ewstep in range(0, step):
                try:
                    tempProps = json.loads(requests.get('https://api.upland.me/map?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)) + '&marker=true', headers=headers).text)
                except:
                    sleep(1)
                    tempProps = json.loads(requests.get('https://api.upland.me/map?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)) + '&marker=true', headers=headers).text)
                else:
                    sleep(10)
                    tempProps = json.loads(requests.get('https://api.upland.me/map?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)) + '&marker=true', headers=headers).text)
                properties.extend(tempProps)
        if models and ((north-south)/step) < (maxStepSize):
            runFlag = False
        elif models == False and (((north-south)/step) < maxStepSize or len(properties) != 0):
            runFlag = False
        step = step*2
        
    prop_ids = []
    uniqueProps = []
    for prop in properties:
        try:
            if not prop['prop_id'] in prop_ids:
                prop_ids.append(prop['prop_id'])
                uniqueProps.append(prop)
        except:
            print(prop)
    return uniqueProps

def getPropertyDetails(headers, propID):
    # retrieves specific property details from Upland API
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
    # returns collections that a specific property can be part of from Upland API
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
    # returns properties that are for sale within a polygon search area
    try:
        saleProperties = json.loads(requests.get('https://api.upland.me/properties/list-view?north=' + str(searchPoly.bounds[3]) + '&south=' + str(searchPoly.bounds[1]) + '&east=' + str(searchPoly.bounds[2]) + '&west=' + str(searchPoly.bounds[0]) + '&offset=0&limit=20&sort=asc', headers=headers).text)
    except:
        sleep(1)
        saleProperties = json.loads(requests.get('https://api.upland.me/properties/list-view?north=' + str(searchPoly.bounds[3]) + '&south=' + str(searchPoly.bounds[1]) + '&east=' + str(searchPoly.bounds[2]) + '&west=' + str(searchPoly.bounds[0]) + '&offset=0&limit=20&sort=asc', headers=headers).text)
    else:
        sleep(10)
        saleProperties = json.loads(requests.get('https://api.upland.me/properties/list-view?north=' + str(searchPoly.bounds[3]) + '&south=' + str(searchPoly.bounds[1]) + '&east=' + str(searchPoly.bounds[2]) + '&west=' + str(searchPoly.bounds[0]) + '&offset=0&limit=20&sort=asc', headers=headers).text)
    return saleProperties

def makeCanvas(objectsToPlot, mapHeight = 3000):
    # creates a cairo canvas 200pixels taller and 50 pixels wider than the extent of the objects to plot on the canvas
    # allowing space for two lines of text at the top of the image
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
    surface = cairo.ImageSurface(cairo.Format.ARGB32, int(mapWidth + 50), int(mapHeight + 200))
    canvas = cairo.Context(surface)
    canvas.set_source_rgb(1, 1, 1)
    canvas.paint()
    canvas.set_source_rgb(0, 0, 0)
    return (surface, canvas, mapFactor, minLat, maxLong, mapWidth)

def plotObject(canvas, mapFactor, objectToPlot, minLat, maxLong, fillColour = (1, 1, 1), heightoffset = 200, widthoffset = 25):
    # plot shapely Polygon/MultiPolygon to cairo canvas and extracts polygon if its in a list
    if type(objectToPlot) == list:
        objectToPlot = objectToPlot[0]
    if isinstance(objectToPlot, MultiPolygon):
        for poly in objectToPlot:
            for num, point in enumerate(poly.exterior.coords):
                if num == 0:
                    canvas.move_to((((point[0] - minLat) * mapFactor) + widthoffset), (((maxLong - point[1]) * mapFactor) + heightoffset))
                else:
                    canvas.line_to((((point[0] - minLat) * mapFactor) + widthoffset), (((maxLong - point[1]) * mapFactor) + heightoffset))
            canvas.set_source_rgb(fillColour[0], fillColour[1], fillColour[2])
            canvas.close_path()
            for coords in poly.interiors:
                for num, point in enumerate(coords.coords):
                    if num == 0:
                        canvas.move_to((((point[0] - minLat) * mapFactor)+ widthoffset), (((maxLong - point[1]) * mapFactor) + heightoffset))
                    else:
                        canvas.line_to((((point[0] - minLat) * mapFactor) + widthoffset), (((maxLong - point[1]) * mapFactor) + heightoffset))
                canvas.close_path()
            canvas.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            canvas.fill_preserve()
            canvas.set_source_rgb(0, 0, 0)
            canvas.stroke()
    else:
        try:
            for num, point in enumerate(objectToPlot.exterior.coords):
                if num == 0:
                    canvas.move_to((((point[0] - minLat) * mapFactor) + widthoffset), (((maxLong - point[1]) * mapFactor) + heightoffset))
                else:
                    canvas.line_to((((point[0] - minLat) * mapFactor) + widthoffset), (((maxLong - point[1]) * mapFactor) + heightoffset))
            canvas.set_source_rgb(fillColour[0], fillColour[1], fillColour[2])
            canvas.close_path()
            for coords in objectToPlot.interiors:
                for num, point in enumerate(coords.coords):
                    if num == 0:
                        canvas.move_to(((point[0] - minLat) * mapFactor)+25, (((maxLong - point[1]) * mapFactor) + heightoffset))
                    else:
                        canvas.line_to(((point[0] - minLat) * mapFactor)+25, (((maxLong - point[1]) * mapFactor) + heightoffset))
                canvas.close_path()
            canvas.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            canvas.fill_preserve()
            canvas.set_source_rgb(0, 0, 0)
            canvas.stroke()
        except:
            print(objectToPlot)
    return

def makePoly(boundaries):
    # function takes boundaries either dictionary or string and converts to
    # dictionary if needed then checks if polygon or multi polygon in ['type']
    # before making a suitable polygon/multipolygon from ['coordinates']
    if not type(boundaries) == dict:
        boundaries = json.loads(boundaries)
    if boundaries['type'] == 'Polygon':
        if len(boundaries['coordinates']) == 1:
            poly = Polygon(boundaries['coordinates'][0])
        else:
            poly = Polygon(boundaries['coordinates'][0], (((boundaries['coordinates'][1])), ))
    elif boundaries['type'] == 'MultiPolygon':
        tempPolys = []
        for polyCoords in boundaries['coordinates']:
            if len(polyCoords) == 1:
                tempPolys.append(Polygon(polyCoords[0]))
            else:
                tempPolys.append(Polygon(polyCoords[0], (((polyCoords[1])), )))
        poly = MultiPolygon(tempPolys)
    else:
        poly = None
    return poly
