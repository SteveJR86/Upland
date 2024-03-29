import json
import requests
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from time import sleep

def getNeighbourhoods(headers):
    # function returns all neighbourhoods as dictionary
    try:
        neighbourhoods = json.loads(requests.get('https://api.upland.me/neighborhood', headers=headers).text)
    except:
        try:
            sleep(1)
            neighbourhoods = json.loads(requests.get('https://api.upland.me/neighborhood', headers=headers).text)
        except:
            sleep(10)
            neighbourhoods = json.loads(requests.get('https://api.upland.me/neighborhood', headers=headers).text)
    return neighbourhoods

def getCities(headers):
    # function returns all neighbourhoods as dictionary
    try:
        cities = json.loads(requests.get('https://api.upland.me/feature/city', headers=headers).text)['cities']
    except:
        try:
            sleep(1)
            cities = json.loads(requests.get('https://api.upland.me/feature/city', headers=headers).text)['cities']
        except:
            sleep(10)
            cities = json.loads(requests.get('https://api.upland.me/feature/city', headers=headers).text)['cities']
    # cities = [  {'name': 'Detroit', 'id': 33}, 
    #             {'name': 'Los Angeles', 'id': 32},
    #             {'name': 'Kansas City', 'id': 14},
    #             {'name': 'Nashville', 'id': 16},
    #             {'name': 'Oakland', 'id': 7}]

    return cities

def getNeighbourhood(headers, searchCity, searchNeighbourhood = None):
    # function returns specific neighbourhoods as list based on a search city and search neighbourhood
    result = []
    if type(searchNeighbourhood) == dict:
        searchNeighbourhood = searchNeighbourhood['name'].upper()
    elif searchNeighbourhood:
        searchNeighbourhood = searchNeighbourhood.upper()
    searchCity = searchCity.title()
    cities = getCities(headers)
    for city in cities:
        if searchCity == city['city_name']:
            cityID = city['city_id']
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
            if neighbourhood['boundaries']:
                neighbourhoodPolys.append(makePoly(neighbourhood['boundaries']))
    return neighbourhoodPolys

def getNeighbourhoodProperties(headers, searchCity, searchNeighbourhood = None, models = False):
    # returns list of lists (one per neighbourhood) of properties
    neighbourhoodPolys = getNeighbourhoodPoly(headers, searchCity, searchNeighbourhood)
    properties = []
    for neighbourhoodPoly in neighbourhoodPolys:
        properties.append(checkInNeighbourhood(neighbourhoodPoly, getProperties(headers, neighbourhoodPoly, models)))
    return properties

def getNeighbourhoodSends(headers, searchCity, searchNeighbourhood = None):
    # returns list of lists (one per neighbourhood) of sends
    neighbourhoodPolys = getNeighbourhoodPoly(headers, searchCity, searchNeighbourhood)
    sends = []
    for neighbourhoodPoly in neighbourhoodPolys:
        sends.append(getSends(headers, neighbourhoodPoly))
    return sends

def checkInNeighbourhood(searchPoly, properties):
    try:
        properties[:] = [x for x in properties if Point(float(x['centerlng']), float(x['centerlat'])).within(searchPoly)]
    except:
        properties = [0]
    return properties

def getProperties(headers, searchPoly, models = False):
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
                    try:
                        sleep(1)
                        tempProps = json.loads(requests.get('https://api.upland.me/map?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)) + '&marker=true', headers=headers).text)
                    except:
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
    try:
        for prop in properties:
            if not prop['prop_id'] in prop_ids:
                prop_ids.append(prop['prop_id'])
                uniqueProps.append(prop)
    except:
        uniqueProps = getProperties(headers, searchPoly, models)
    return uniqueProps

def getSends(headers, searchPoly):
    north = searchPoly.bounds[3]
    south = searchPoly.bounds[1]
    east = searchPoly.bounds[2]
    west = searchPoly.bounds[0]
    step = 1
    maxStepSize = 0.01
    runFlag = True
    while runFlag:
        sends = []
        for nsstep in range(0, step):
            for ewstep in range(0, step):
                try:
                    tempSends = json.loads(requests.get('https://api.prod.upland.me/treasures/sends/discovery?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)), headers=headers).text)
                except:
                    try:
                        sleep(1)
                        tempSends = json.loads(requests.get('https://api.prod.upland.me/treasures/sends/discovery?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)), headers=headers).text)
                    except:
                        sleep(10)
                        tempSends = json.loads(requests.get('https://api.prod.upland.me/treasures/sends/discovery?north=' + str(north - ((north-south)/step)*nsstep) + '&south=' + str(north - ((north-south)/step)*(nsstep+1)) + '&east=' + str(east - ((east-west)/step)*ewstep) + '&west=' + str(east - ((east-west)/step)*(ewstep+1)), headers=headers).text)
                sends.extend(tempSends)
        if (((north-south)/step) < (maxStepSize) or len(sends) != 0):
            runFlag = False
        step = step*2
    return sends

def getPropertyDetails(headers, propID):
    # retrieves specific property details from Upland API
    try:
        propDetails = json.loads(requests.get('https://api.upland.me/properties/' + str(propID), headers=headers).text)
    except:
        try:
            sleep(1)
            propDetails = json.loads(requests.get('https://api.upland.me/properties/' + str(propID), headers=headers).text)
        except:
            sleep(10)
            propDetails = json.loads(requests.get('https://api.upland.me/properties/' + str(propID), headers=headers).text)
    return propDetails

def matchCollections(headers, propID):
    # returns collections that a specific property can be part of from Upland API
    try:
        collectionRaw = requests.get('https://api.upland.me/properties/match/' + str(propID), headers=headers).text
    except:
        try:
            sleep(1)
            collectionRaw = requests.get('https://api.upland.me/properties/match/' + str(propID), headers=headers).text
        except:
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
        try:
            sleep(1)
            saleProperties = json.loads(requests.get('https://api.upland.me/properties/list-view?north=' + str(searchPoly.bounds[3]) + '&south=' + str(searchPoly.bounds[1]) + '&east=' + str(searchPoly.bounds[2]) + '&west=' + str(searchPoly.bounds[0]) + '&offset=0&limit=20&sort=asc', headers=headers).text)
        except:
            sleep(10)
            saleProperties = json.loads(requests.get('https://api.upland.me/properties/list-view?north=' + str(searchPoly.bounds[3]) + '&south=' + str(searchPoly.bounds[1]) + '&east=' + str(searchPoly.bounds[2]) + '&west=' + str(searchPoly.bounds[0]) + '&offset=0&limit=20&sort=asc', headers=headers).text)
    return saleProperties


def makePoly(boundaries):
    # function takes boundaries either dictionary or string and converts to
    # dictionary if needed then checks if polygon or multi polygon in ['type']
    # before making a suitable polygon/multipolygon from ['coordinates']
    if not type(boundaries) == dict:
        try:
            boundaries = json.loads(boundaries)
        except:
            boundaries = {'type': None}
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
