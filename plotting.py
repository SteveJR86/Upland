from shapely.geometry import Point, Polygon, MultiPolygon
import cairo
import math
from datetime import date

def makeCanvas(objectsToPlot, mapHeight = 3000):
  # creates a cairo canvas 200pixels taller and 50 pixels wider than the extent of the objects to plot on the canvas
  # allowing space for two lines of text at the top of the image
  minLat = 1000
  maxLat = -1000
  minLong = 1000
  maxLong = -1000
  today = date.today()
  todayFormat = today.strftime('%d/%b/%y')

  for x in objectsToPlot:
    if x:
      minLat = min(minLat, x.bounds[0])
      maxLat = max(maxLat, x.bounds[2])
      minLong = min(minLong, x.bounds[1])
      maxLong = max(maxLong, x.bounds[3])

  mapRatio = (maxLong - minLong) / (maxLat - minLat)
  mapWidth = mapHeight / mapRatio
  heightRatio = mapHeight / (maxLong - minLong)
  widthRatio = mapWidth / (maxLat - minLat)
  mapFactor = min(heightRatio, widthRatio)
  surface = cairo.ImageSurface(cairo.Format.ARGB32, int(mapWidth + 50), int(mapHeight + 225))
  canvas = cairo.Context(surface)
  canvas.set_source_rgb(1, 1, 1)
  canvas.paint()
  canvas.set_source_rgb(0, 0, 0)
  canvas.set_font_size(50)
  canvas.move_to((mapWidth - 600), 75)
  canvas.show_text("Map created by Steve (sjr86)")
  canvas.move_to((mapWidth - 600), 125)
  canvas.show_text(f"Produced on {todayFormat}")
  return (surface, canvas, mapFactor, minLat, maxLong, mapWidth)

def plotKey(canvas, surface, keyFile, position):
  height = surface.get_height()
  width = surface.get_width()
  keyToPlot = cairo.ImageSurface.create_from_png(keyFile)
  keyWidth = keyToPlot.get_width()
  keyHeight = keyToPlot.get_height()
  if position == "TopRight":
    xLocation = width - keyWidth - 25
    yLocation = 225
  elif position == "TopLeft":
    xLocation = 25
    yLocation = 225
  elif position == "BottomRight":
    xLocation = width - keyWidth - 25
    yLocation = height - keyHeight - 25
  elif position == "BottomLeft":
    xLocation = 25
    yLocation = height - keyHeight - 25
  
  canvas.set_source_surface(keyToPlot, xLocation, yLocation)
  canvas.paint()
  canvas.set_source_rgb(0, 0, 0)

  return

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
  elif isinstance(objectToPlot, Polygon):
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
          canvas.move_to(((point[0] - minLat) * mapFactor) + widthoffset, (((maxLong - point[1]) * mapFactor) + heightoffset))
        else:
          canvas.line_to(((point[0] - minLat) * mapFactor) + widthoffset, (((maxLong - point[1]) * mapFactor) + heightoffset))
      canvas.close_path()
    canvas.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    canvas.fill_preserve()
    canvas.set_source_rgb(0, 0, 0)
    canvas.stroke()
  else:
    print(objectToPlot)
  return

def plotCircle(canvas, surface, mapFactor, radius, minLat, maxLong, fillColour = (1, 1, 1, 1), heightoffset = 200, widthoffset = 25):
  height = surface.get_height()
  width = surface.get_width()
  canvas.arc(width / 2, height / 2, (radius / 111139) * mapFactor, 0, 2*math.pi)
  canvas.set_source_rgba(fillColour[0], fillColour[1], fillColour[2], fillColour[3])
  canvas.fill_preserve()
  canvas.set_source_rgba(0, 0, 0, 1)
  canvas.stroke()

  return
