"""
!/bin/python
-*- coding: utf-8 -*
QGIS Version: QGIS 2.16

### Author ###
 S. Crommelinck, 2017

### Description ###
 This script converts a (SLIC) raster to a vector file containing the lines of each SLIC segment outline
"""

### Import script in QGIS Python console ###
"""
# add directory with script to Python search path
import sys
sys.path.append(r"D:\path to script")

# import module
import A5_SLIC_raster_to_lines

# rerun module after changing the source code
reload(A5_SLIC_raster_to_lines)
"""

### Predefine variables ###
SLIC_raster = r"D:\path to file"
data_dir = r"D:\path to directory"

### Import required modules ###
import os
import processing
from qgis.analysis import *
from qgis.core import *
from qgis.utils import *

### Main processing part ###
# Change into data directory
os.chdir(data_dir)

# Load raster
fileInfo = QFileInfo(SLIC_raster)
path = fileInfo.filePath()
baseName = fileInfo.baseName()
SLIC_rlayer = QgsRasterLayer(path, baseName)
if not SLIC_rlayer.isValid():
    print "--> ERROR: SLIC layer failed to load."
else:
    print "--> SLIC layer successfully loaded.\n"

# Define extent
extent = SLIC_rlayer.extent()
xmin = extent.xMinimum()
xmax = extent.xMaximum()
ymin = extent.yMinimum()
ymax = extent.yMaximum()

# Raster to polygons
polygons = data_dir + r"\1_SLIC_polygons.shp"
if not os.path.isfile(polygons):
    processing.runalg('grass7:r.to.vect',
                      {"input": SLIC_raster,
                       "type": 2,
                       "GRASS_OUTPUT_TYPE_PARAMETER": 3,
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "output": polygons})
    print "--> successfully converted raster to polygons.\n"

lines = data_dir + r"\2_SLIC_lines.shp"
if not os.path.isfile(lines):
    processing.runalg('grass7:v.to.lines',
                      {"input": polygons,
                       "method": 0,
                       "GRASS_OUTPUT_TYPE_PARAMETER": 2,
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "output": lines})
    print "--> successfully converted polygons to lines.\n"

# Print final overall message
print "All processing has been finished."


"""
### Notes ###
# QGIS help
processing.alghelp("grass7:r.to.vect")
processing.alghelp('gdalogr:polygonize')
processing.alghelp('g.extension')
processing.alglist("g.extension")

# Code Snippets
### Duplicating Implementaion ###
-> qgis:polygonstolines + qgis:singlepartstomultipart + grass7:v.clean 

# Raster to polygons
polygons = data_dir + r"\1_SLIC_polygons.shp"
if not os.path.isfile(polygons):
    processing.runalg('gdalogr:polygonize',
                      {"INPUT": SLIC_raster,
                       "OUTPUT": polygons})
    print "--> successfully converted raster to polygons.\n"

# Load polygon layer
polygons_vlayer = QgsVectorLayer(polygons, "polygons", "ogr")
if not polygons_vlayer.isValid():
  print "--> ERROR: polygon layer failed to load."
else:
    print "--> polygon layer successfully loaded.\n"

# Define extent
extent = polygons_vlayer.extent()
xmin = extent.xMinimum()
xmax = extent.xMaximum()
ymin = extent.yMinimum()
ymax = extent.yMaximum()

# Polygons to lines
lines = data_dir + r"\2_SLIC_polylines.shp"
if not os.path.isfile(lines):
    processing.runalg('qgis:polygonstolines',           # saga:convertpolygonstolines seems to do the same
                      {"INPUT": polygons,
                       "OUTPUT": lines})
    print "--> successfully converted polygons to lines.\n"

# Change DN values to 1 for all features
layer = QgsVectorLayer(lines,"lines", "ogr")
for feature in layer.getFeatures():
    layer.startEditing()
    feature['DN'] = 1
    layer.updateFeature(feature)
    layer.commitChanges()

# Merge all features to one
lines_multipart = data_dir + r"\3_SLIC_polylines_multipart.shp"
if not os.path.isfile(lines_multipart):
    processing.runalg('qgis:singlepartstomultipart',
                      {"INPUT": lines,
                       "FIELD": 'DN',
                       "OUTPUT": lines_multipart})
    print "--> successfully converted multiparts to one feature.\n"

# Break lines at intersections
lines_cleaned = data_dir + r"\4_SLIC_lines_break.shp"
if not os.path.isfile(lines_cleaned):
    processing.runalg('grass7:v.clean',
                      {"input": lines,
                        "tool": 0,
                        "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                        "output": lines_cleaned})
    print "--> successfully broke lines at intersections.\n"

# Remove duplicate lines
lines_rmdpl = data_dir + r"\5_SLIC_lines_rmdpl.shp"
if not os.path.isfile(lines_rmdpl):
    processing.runalg('qgis:deleteduplicategeometries',
                      {"INPUT": lines_cleaned,
                        "OUTPUT": lines_rmdpl})
    print "--> successfully removed duplicate lines.\n"
"""
