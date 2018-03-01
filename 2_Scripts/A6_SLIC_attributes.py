# coding=utf-8
"""
!/bin/python
-*- coding: utf-8 -*
QGIS Version: QGIS 2.16

### Author ###
 S. Crommelinck, 2017

### Description ###
 This script calculates attributes per SLIC line by taking into account information of each line’s geometry and
 topology as well as information from the UAV data (RGB and DSM) and the ucm and gPb maps.
"""

### Import script in QGIS Python console ###
"""
# add directory with script to Python search path
import sys
sys.path.append(r"D:\path to script")

#import module
import A6_SLIC_attributes

# rerun module after changing the source code
reload(A6_SLIC_attributes)
"""

### Predefine variables ###
input_dir = r"D:\path to directory"
SLIC_l = input_dir + r"\SLIC_lines.shp"
gPb = input_dir + r"\gPb_centerlines.shp"
ucm_RGB = input_dir + r"\ucm.tif"
RGB = input_dir + r"\RGB.tif"
DSM = input_dir + r"\DSM.tif"
output_dir = r"D:\path to directory"

### Attributes calculated in this script ###
"""
ID:                 unique number per SLIC segment        

length [m]:         length per SLIC segment along the line

ucm_rgb:            median of all ucm_rgb pixels underlying a SLIC segment with a 0.4m buffer around each SLIC segment

lap_dsm:            median of all pixels from DSM laplacian filter underlying a SLIC segment with a 0.4m buffer around 
each SLIC segment

dist_to_gPb [m]:    distance between SLIC segment and gPb lines (overall shortest distance)
    
azimuth [°]:        horizontal angle measured clockwise from north per SLIC segment
    
sinuosity:          ratio of distance between start and end point along SLIC segment (line length) and their 
                    direct euclidean distance

azi_gPb [°]:        horizontal angle measured clockwise from north per gPb segment closest to a SLIC segment (aims 
                    to indicate line parallelism/collinearity)
   
r_dsm_medi:         median of all DSM values lying with a 0.2m buffer right of each SLIC segment

l_dsm_medi:         median of all DSM values lying with a 0.2m buffer left of each SLIC segment

r_red_medi:         median of all red values lying with a 0.2m buffer right of each SLIC segment

l_red_medi:         median of all red values lying with a 0.2m buffer left of each SLIC segment

r_gre_medi:         median of all green values lying with a 0.2m buffer right of each SLIC segment

l_gre_medi:         median of all green values lying with a 0.2m buffer left of each SLIC segment

r_blu_medi:         median of all blue values lying with a 0.2m buffer right of each SLIC segment

l_blu_medi:         median of all blue values lying with a 0.2m buffer left of each SLIC segment

red_grad:           absolute value of difference between r_red_medi and l_red_medi

green_grad:         absolute value of difference between r_green_medi and l_green_medi

blue_grad:          absolute value of difference between r_blue_medi and l_blue_medi

dsm_grad:           absolute value of difference between r_dsm_medi and l_dsm_medi
"""

### Import required modules ###
import qgis
import os
from qgis.core import *
from qgis.utils import *
from qgis.analysis import *
import processing
from osgeo import ogr

### Main processing part ###
#######################
### Load input data ###
#######################
# Change into data directory
os.chdir(output_dir)

# Open all input data
# gPb
gPb_vlayer = QgsVectorLayer(gPb, "gPb_vlayer", "ogr")
if not gPb_vlayer.isValid():
    print "--> ERROR: gPb layer failed to load."
else:
    print "--> gPb layer successfully loaded.\n"

# ucm_RGB
fileInfo = QFileInfo(ucm_RGB)
baseName = fileInfo.baseName()
ucm_RGB_rlayer = QgsRasterLayer(ucm_RGB, baseName)
if not ucm_RGB_rlayer.isValid():
    print "--> ERROR: ucm RGB layer failed to load."
else:
    print "--> ucm RGB layer successfully loaded.\n"

# RGB
fileInfo = QFileInfo(RGB)
baseName = fileInfo.baseName()
RGB_rlayer = QgsRasterLayer(RGB, baseName)
if not RGB_rlayer.isValid():
    print "--> ERROR: RGB layer failed to load."
else:
    print "--> RGB layer successfully loaded.\n"

# DSM
fileInfo = QFileInfo(DSM)
baseName = fileInfo.baseName()
DSM_rlayer = QgsRasterLayer(DSM, baseName)
if not DSM_rlayer.isValid():
    print "--> ERROR: DSM layer failed to load."
else:
    print "--> DSM layer successfully loaded.\n"

# SLIC_lines
SLIC_lines = QgsVectorLayer(SLIC_l, SLIC_l, "ogr")
if not SLIC_lines.isValid():
    print "--> ERROR: SLIC layer failed to load."
else:
    print "--> SLIC layer successfully loaded.\n"

# Define extent
extent = RGB_rlayer.extent()
xmin = extent.xMinimum()
xmax = extent.xMaximum()
ymin = extent.yMinimum()
ymax = extent.yMaximum()

# Add ID per line segment
bpol_ID = os.getcwd() + r"\1_SLIC_bpol_ID.shp"
if not os.path.isfile(bpol_ID):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": SLIC_lines,
                       "FIELD_NAME": "ID",
                       "FIELD_TYPE": 1,
                       "FORMULA": '$id',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": bpol_ID})
    print "--> Added ID per line segment.\n"

############################
### Length of SLIC lines ###
############################
# Calculate length per line segment
bpol_length = os.getcwd() + r"\2_SLIC_length.shp"
if not os.path.isfile(bpol_length):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": bpol_ID,
                       "FIELD_NAME": "length",
                       "FIELD_TYPE": 0,
                       "FORMULA": 'length($geometry)',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": bpol_length})
    print "--> Calculate length per line segment.\n"

##################################
### Median value of UCM raster ###
##################################
# Convert ucm raster to points
ucm_RGB_points = os.getcwd() + r"\3_ucm_RGB_points.shp"
if not os.path.isfile(ucm_RGB_points):
    processing.runalg('grass7:r.to.vect',
                      {"input": ucm_RGB_rlayer,
                       "type": 1,
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "GRASS_OUTPUT_TYPE_PARAMETER": 1,
                       "output": ucm_RGB_points})
    print "--> ucm RGB raster converted to point vector.\n"

# Join attributes by location
SLIC_ucm_RGB = os.getcwd() + r"\4_SLIC_ucm_RGB.shp"
if not os.path.isfile(SLIC_ucm_RGB):
    processing.runalg('qgis:joinattributesbylocation',
                      {"TARGET": bpol_length,
                       "JOIN": ucm_RGB_points,
                       "PREDICATE": u'intersects',
                       "PRECISION": 1,  # searches for all points in a 1m radius
                       "SUMMARY": 1,  # takes the summary (=avg?) of all points in the radius
                       "STATS": 'median',
                       "KEEP": 1,  # all records are kept
                       "OUTPUT": SLIC_ucm_RGB})
    print "--> Joined attributes by location.\n"

# Rename attributes
layer = QgsVectorLayer(SLIC_ucm_RGB, "SLIC_ucm_RGB", "ogr")
with edit(layer):
    idx = layer.fieldNameIndex('medianvalu')
    layer.renameAttribute(idx, 'ucm_rgb')

#####################################
### Apply Laplacian filter on DSM ###
#####################################
lap_DSM = os.getcwd() + r"\5_lap_DSM.tif"
if not os.path.isfile(lap_DSM):
    processing.runalg('saga:laplacianfilter',
                      {"INPUT": DSM_rlayer,
                       "METHOD": 0,
                       "RADIUS": 1,
                       "SIGMA": 0,
                       "MODE": 0,
                       "RESULT": lap_DSM})
    print "--> Laplacian filter applied to DSM.\n"

# Normalize filtered DSM
lap_DSM_normalized = os.getcwd() + r"\6_lap_DSM_normalized.tif"
if not os.path.isfile(lap_DSM_normalized):
    processing.runalg('saga:gridnormalisation',
                      {"INPUT": lap_DSM,
                       "RANGE_MIN": 0,
                       "RANGE_MAX": 1,
                       "OUTPUT": lap_DSM_normalized})
    print "--> Normalized Laplacian filtered DSM.\n"

######################################
### Median value of DSM_lap raster ###
######################################
lap_DSM_points = os.getcwd() + r"\7_lap_DSM_points.shp"
if not os.path.isfile(lap_DSM_points):
    processing.runalg('grass7:r.to.vect',
                      {"input": lap_DSM_normalized,
                       "type": 1,
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "GRASS_OUTPUT_TYPE_PARAMETER": 1,
                       "output": lap_DSM_points})
    print "--> Laplacian DSM raster converted to point vector.\n"

SLIC_lap_DSM = os.getcwd() + r"\8_SLIC_lap_DSM.shp"
if not os.path.isfile(SLIC_lap_DSM):
    processing.runalg('qgis:joinattributesbylocation',
                      {"TARGET": SLIC_ucm_RGB,
                       "JOIN": lap_DSM_points,
                       "PREDICATE": u'intersects',
                       "PRECISION": 1,  # searches for all points in a 1m radius
                       "SUMMARY": 1,  # takes the summary (=avg?) of all points in the radius
                       "STATS": 'median',
                       "KEEP": 1,  # all records are kept
                       "OUTPUT": SLIC_lap_DSM})
    print "--> Joined attributes by location.\n"

# Rename attributes
layer = QgsVectorLayer(SLIC_lap_DSM, "SLIC_lap_DSM", "ogr")
with edit(layer):
    idx = layer.fieldNameIndex('medianvalu')
    layer.renameAttribute(idx, 'lap_dsm')

############################
### Distance to gPb line ###
############################
# Add distance column to SLIC lines (type: float, precision = 2)
SLIC_update = os.getcwd() + r"\9_SLIC_update.shp"
if not os.path.isfile(SLIC_update):
    processing.runalg('qgis:addfieldtoattributestable',
                      {"INPUT_LAYER": SLIC_lap_DSM,
                       "FIELD_NAME": 'dist',
                       "FIELD_TYPE": 1,
                       "FIELD_LENGTH": 10,
                       "FIELD_PRECISION": 2,
                       "OUTPUT_LAYER": SLIC_update})
    print "--> Added distance column to SLIC lines.\n"

#########################################################
# Calculate distance to gPb line
dist2gPb = os.getcwd() + r"\10_dist2gPb.shp"
if not os.path.isfile(dist2gPb):
    processing.runalg('grass7:v.distance',
                      {"from": SLIC_update,
                       "to": gPb_vlayer,
                       "dmax": '-1',
                       "dmin": '-1',
                       "upload": 'dist',
                       "column": 'dist',
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "from_output": dist2gPb})
    print "--> Added distance column to SLIC lines.\n"

#########################################################
### SLIC line characteristics (azimuth and sinuosity) ###
#########################################################
# Calculate azimuth per line segment
SLIC_azimuth = os.getcwd() + r"\11_SLIC_azimuth.shp"
if not os.path.isfile(SLIC_azimuth):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": dist2gPb,
                       "FIELD_NAME": "azimuth",
                       "FIELD_TYPE": 0,
                       "FORMULA": 'case when yat(-1)-yat(0) < 0 or yat(-1)-yat(0) > 0 then (atan((xat(-1)-xat('
                                  '0))/(yat(-1)-yat(0)))) * 180/3.14159 +(180 * (((yat(-1)-yat(0)) < 0) + (((xat('
                                  '-1)-xat(0)) < 0 AND (yat(-1) - yat(0)) >0)*2))) when ((yat(-1)-yat(0)) = 0 and ('
                                  'xat(-1) - xat(0)) >0) then 90 when ((yat(-1)-yat(0)) = 0 and (xat(-1) - xat(0)) '
                                  '<0) then 270 end',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": SLIC_azimuth})
    print "--> Calculated azimuth per line segment.\n"
# source: https://gis.stackexchange.com/questions/24260/how-to-add-direction-and-distance-to-attribute-table/24430#24430
# Azimuth and sinuosity can also be added via GRASS -> v.to.db map= option=sinuous,azimuth columns=sinuous,
# azimuth (algorithmm v.to.db not availabe in QGIS processing)

#########################################################
# Load layer for feature selection
layer = iface.addVectorLayer(SLIC_azimuth, "SLIC_azimuth", "ogr")

# Rename attributes
with edit(layer):
    idx = layer.fieldNameIndex('dist')
    layer.renameAttribute(idx, 'dist_to_gPb')

#########################################################
# Filter out unconnected segments (small dead-end segments resulting from snapping)
# Select all lines having an azimuth value = NULL
processing.runalg('qgis:selectbyexpression',
                  {"LAYERNAME": SLIC_azimuth,
                   "EXPRESSION": '"azimuth" IS NULL',
                   "METHOD": 0})
print "--> Filtered out unwanted line segments.\n"

# Invert selection for SLIC lines with azimuth value
layer.invertSelection()

# Save selected features
SLIC_filtered = os.getcwd() + r"\12_SLIC_filtered.shp"
if not os.path.isfile(SLIC_filtered):
    processing.runalg('qgis:saveselectedfeatures',
                      {"INPUT_LAYER": SLIC_azimuth,
                       "OUTPUT_LAYER": SLIC_filtered})
    print "--> Deleted out unwanted line segments.\n"

# unload layer
QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])

#########################################################
# Calculate sinuosity per line segment
SLIC_sinuosity = os.getcwd() + r"\13_SLIC_sinuosity.shp"
if not os.path.isfile(SLIC_sinuosity):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": SLIC_filtered,
                       "FIELD_NAME": "sinuosity",
                       "FIELD_TYPE": 0,
                       "FORMULA": 'length($geometry)/distance(start_point($geometry), end_point($geometry))',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": SLIC_sinuosity})
    print "--> Calculated azimuth per line segment.\n"

####################################
### Azimuth of closest gPb line  ###
####################################
# Calculate azimuth per gPb line segment
# #?# might be an option to break the gPb vector line layer before into smaller segments
gPb_azimuth = os.getcwd() + r"\14_gPb_azimuth.shp"
if not os.path.isfile(gPb_azimuth):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": gPb_vlayer,
                       "FIELD_NAME": "azimuth",
                       "FIELD_TYPE": 0,
                       "FORMULA": 'case when yat(-1)-yat(0) < 0 or yat(-1)-yat(0) > 0 then (atan((xat(-1)-xat('
                                  '0))/(yat(-1)-yat(0)))) * 180/3.14159 +(180 * (((yat(-1)-yat(0)) < 0) + (((xat('
                                  '-1)-xat(0)) < 0 AND (yat(-1) - yat(0)) >0)*2))) when ((yat(-1)-yat(0)) = 0 and ('
                                  'xat(-1) - xat(0)) >0) then 90 when ((yat(-1)-yat(0)) = 0 and (xat(-1) - xat(0)) '
                                  '<0) then 270 end',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": gPb_azimuth})
    print "--> Calculated azimuth per gPb line segment.\n"

# Add azimuth column to SLIC lines (type: float, precision = 3)
SLIC_gPB_azimuth = os.getcwd() + r"\15_SLIC_gPB_azimuth.shp"
if not os.path.isfile(SLIC_gPB_azimuth):
    processing.runalg('qgis:addfieldtoattributestable',
                      {"INPUT_LAYER": SLIC_sinuosity,
                       "FIELD_NAME": 'azi_gPb',
                       "FIELD_TYPE": 1,
                       "FIELD_LENGTH": 10,
                       "FIELD_PRECISION": 3,
                       "OUTPUT_LAYER": SLIC_gPB_azimuth})
    print "--> Added azimuth_gPb column to SLIC lines.\n"

# Append azimuth of gPb line to closest SLIC line
SLIC_gPB_azimuth_update = os.getcwd() + r"\16_SLIC_gPB_azimuth_update.shp"
if not os.path.isfile(SLIC_gPB_azimuth_update):
    processing.runalg('grass7:v.distance',
                      {"from": SLIC_gPB_azimuth,
                       "to": gPb_azimuth,
                       "dmax": '-1',
                       "dmin": '-1',
                       "upload": 'to_attr',
                       "column": 'azi_gPb',
                       "to_column": 'azimuth',
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "from_output": SLIC_gPB_azimuth_update})
    print "--> Added azimuth of gPb line to closest SLIC lines.\n"

####################################################
### DSM values left and right of each SLIC line  ###
####################################################
# Create one-sided buffer (left/right) of 0.2m for each SLIC line
SLIC_rside_buffer = os.getcwd() + r"\17_SLIC_rside_buffer.shp"
if not os.path.isfile(SLIC_rside_buffer):
    processing.runalg('gdalogr:singlesidedbuffersandoffsetlinesforlines',
                      {"INPUT_LAYER": SLIC_gPB_azimuth_update,
                       "OPERATION": 0,
                       "GEOMETRY": 'geometry',
                       "RADIUS": 0.2,
                       "LEFTRIGHT": 0,
                       "DISSOLVEALL": False,
                       "FIELD": None,
                       "MULTI": False,
                       "OUTPUT_LAYER": SLIC_rside_buffer})
    print "--> Added one-sided buffer (right) of 0.2m to SLIC lines.\n"

SLIC_lside_buffer = os.getcwd() + r"\18_SLIC_lside_buffer.shp"
if not os.path.isfile(SLIC_lside_buffer):
    processing.runalg('gdalogr:singlesidedbuffersandoffsetlinesforlines',
                      {"INPUT_LAYER": SLIC_gPB_azimuth_update,
                       "OPERATION": 0,
                       "GEOMETRY": 'geometry',
                       "RADIUS": 0.2,
                       "LEFTRIGHT": 1,
                       "DISSOLVEALL": False,
                       "FIELD": None,
                       "MULTI": False,
                       "OUTPUT_LAYER": SLIC_lside_buffer})
    print "--> Added one-sided buffer (left) of 0.2m to SLIC lines.\n"

# Calculate zonal statistics per buffer (left/right)
rbuffer_stats = os.getcwd() + r"\19_rbuffer_stats.shp"
if not os.path.isfile(rbuffer_stats):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": DSM_rlayer,
                       "RASTER_BAND": 1,
                       "INPUT_VECTOR": SLIC_rside_buffer,
                       "COLUMN_PREFIX": 'r_dsm_',
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": rbuffer_stats})
    print "--> Calculated zonal statistics for one-sided buffer (right).\n"

lbuffer_stats = os.getcwd() + r"\20_lbuffer_stats.shp"
if not os.path.isfile(lbuffer_stats):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": DSM_rlayer,
                       "RASTER_BAND": 1,
                       "INPUT_VECTOR": SLIC_lside_buffer,
                       "COLUMN_PREFIX": 'l_dsm_',
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": lbuffer_stats})
    print "--> Calculated zonal statistics for one-sided buffer (left).\n"

# Join attribute table of buffer statistics with SLIC lines
SLIC_rbuffer_stats = os.getcwd() + r"\21_SLIC_rbuffer_stats.shp"
if not os.path.isfile(SLIC_rbuffer_stats):
    processing.runalg('qgis:joinattributestable',
                      {"INPUT_LAYER": SLIC_gPB_azimuth_update,
                       "INPUT_LAYER_2": rbuffer_stats,
                       "TABLE_FIELD": 'ID',
                       "TABLE_FIELD_2": 'ID',
                       "OUTPUT_LAYER": SLIC_rbuffer_stats})
    print "--> Join attribute table of buffer statistics (right) with SLIC lines.\n"

SLIC_lbuffer_stats = os.getcwd() + r"\22_SLIC_lbuffer_stats.shp"
if not os.path.isfile(SLIC_lbuffer_stats):
    processing.runalg('qgis:joinattributestable',
                      {"INPUT_LAYER": SLIC_rbuffer_stats,
                       "INPUT_LAYER_2": lbuffer_stats,
                       "TABLE_FIELD": 'ID',
                       "TABLE_FIELD_2": 'ID',
                       "OUTPUT_LAYER": SLIC_lbuffer_stats})
    print "--> Join attribute table of buffer statistics (left) with SLIC lines.\n"

####################################################
### RGB values left and right of each SLIC line  ###
####################################################
# Calculate zonal statistics per buffer (left/right)
# red
rbuffer_stats_red = os.getcwd() + r"\23_rbuffer_stats_red.shp"
if not os.path.isfile(rbuffer_stats_red):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": RGB_rlayer,
                       "RASTER_BAND": 1,
                       "INPUT_VECTOR": SLIC_rside_buffer,
                       "COLUMN_PREFIX": 'r_red_',
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": rbuffer_stats_red})
    print "--> Calculated zonal statistics for one-sided buffer (right).\n"

lbuffer_stats_red = os.getcwd() + r"\24_lbuffer_stats_red.shp"
if not os.path.isfile(lbuffer_stats_red):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": RGB_rlayer,
                       "RASTER_BAND": 1,
                       "INPUT_VECTOR": SLIC_lside_buffer,
                       "COLUMN_PREFIX": 'l_red_',
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": lbuffer_stats_red})
    print "--> Calculated zonal statistics for one-sided buffer (left).\n"

# green
rbuffer_stats_green = os.getcwd() + r"\25_rbuffer_stats_green.shp"
if not os.path.isfile(rbuffer_stats_green):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": RGB_rlayer,
                       "RASTER_BAND": 2,
                       "INPUT_VECTOR": SLIC_rside_buffer,
                       "COLUMN_PREFIX": 'r_gre_',
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": rbuffer_stats_green})
    print "--> Calculated zonal statistics for one-sided buffer (right).\n"

lbuffer_stats_green = os.getcwd() + r"\26_lbuffer_stats_green.shp"
if not os.path.isfile(lbuffer_stats_green):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": RGB_rlayer,
                       "RASTER_BAND": 2,
                       "INPUT_VECTOR": SLIC_lside_buffer,
                       "COLUMN_PREFIX": 'l_gre_',
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": lbuffer_stats_green})
    print "--> Calculated zonal statistics for one-sided buffer (left).\n"

# blue
rbuffer_stats_blue = os.getcwd() + r"\27_rbuffer_stats_blue.shp"
if not os.path.isfile(rbuffer_stats_blue):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": RGB_rlayer,
                       "RASTER_BAND": 3,
                       "INPUT_VECTOR": SLIC_rside_buffer,
                       "COLUMN_PREFIX": 'r_blu_',
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": rbuffer_stats_blue})
    print "--> Calculated zonal statistics for one-sided buffer (right).\n"

lbuffer_stats_blue = os.getcwd() + r"\28_lbuffer_stats_blue.shp"
if not os.path.isfile(lbuffer_stats_blue):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": RGB_rlayer,
                       "RASTER_BAND": 3,
                       "INPUT_VECTOR": SLIC_lside_buffer,
                       "COLUMN_PREFIX": 'l_blu_',
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": lbuffer_stats_blue})
    print "--> Calculated zonal statistics for one-sided buffer (left).\n"

# Delete unwanted fields in attribute table
layer = iface.addVectorLayer(SLIC_lbuffer_stats, "SLIC_lbuffer_stats", "ogr")

accepted_attributes = {"ID", "length", "ucm_rgb", "lap_dsm", "dist_to_gP", "azimuth", "sinuosity", "azi_gPb",
                       "r_dsm_medi", "l_dsm_medi", "r_red_medi", "l_red_medi", "r_gre_medi", "l_gre_medi", "r_blu_medi",
                       "l_blu_medi", "boundary"}
field_names = [field.name() for field in layer.fields()]

with edit(layer):
    # Assign count in reverse order for each field which will be used as index
    for i, j in reversed(list(enumerate(field_names))):
        if j not in accepted_attributes:
            layer.deleteAttribute(i)
print "--> Columns deleted.\n"

# Join attribute table of buffer statistics with SLIC lines
# red
SLIC_rbuffer_stats_red = os.getcwd() + r"\29_SLIC_rbuffer_stats_red.shp"
if not os.path.isfile(SLIC_rbuffer_stats_red):
    processing.runalg('qgis:joinattributestable',
                      {"INPUT_LAYER": SLIC_lbuffer_stats,
                       "INPUT_LAYER_2": rbuffer_stats_red,
                       "TABLE_FIELD": 'ID',
                       "TABLE_FIELD_2": 'ID',
                       "OUTPUT_LAYER": SLIC_rbuffer_stats_red})
    print "--> Join attribute table of buffer statistics (right) with SLIC lines.\n"

SLIC_lbuffer_stats_red = os.getcwd() + r"\30_SLIC_lbuffer_stats_red.shp"
if not os.path.isfile(SLIC_lbuffer_stats_red):
    processing.runalg('qgis:joinattributestable',
                      {"INPUT_LAYER": SLIC_rbuffer_stats_red,
                       "INPUT_LAYER_2": lbuffer_stats_red,
                       "TABLE_FIELD": 'ID',
                       "TABLE_FIELD_2": 'ID',
                       "OUTPUT_LAYER": SLIC_lbuffer_stats_red})
    print "--> Join attribute table of buffer statistics (left) with SLIC lines.\n"

# green
SLIC_rbuffer_stats_green = os.getcwd() + r"\31_SLIC_rbuffer_stats_green.shp"
if not os.path.isfile(SLIC_rbuffer_stats_green):
    processing.runalg('qgis:joinattributestable',
                      {"INPUT_LAYER": SLIC_lbuffer_stats_red,
                       "INPUT_LAYER_2": rbuffer_stats_green,
                       "TABLE_FIELD": 'ID',
                       "TABLE_FIELD_2": 'ID',
                       "OUTPUT_LAYER": SLIC_rbuffer_stats_green})
    print "--> Join attribute table of buffer statistics (right) with SLIC lines.\n"

SLIC_lbuffer_stats_green = os.getcwd() + r"\32_SLIC_lbuffer_stats_green.shp"
if not os.path.isfile(SLIC_lbuffer_stats_green):
    processing.runalg('qgis:joinattributestable',
                      {"INPUT_LAYER": SLIC_rbuffer_stats_green,
                       "INPUT_LAYER_2": lbuffer_stats_green,
                       "TABLE_FIELD": 'ID',
                       "TABLE_FIELD_2": 'ID',
                       "OUTPUT_LAYER": SLIC_lbuffer_stats_green})
    print "--> Join attribute table of buffer statistics (left) with SLIC lines.\n"

# blue
SLIC_rbuffer_stats_blue = os.getcwd() + r"\33_SLIC_rbuffer_stats_blue.shp"
if not os.path.isfile(SLIC_rbuffer_stats_blue):
    processing.runalg('qgis:joinattributestable',
                      {"INPUT_LAYER": SLIC_lbuffer_stats_green,
                       "INPUT_LAYER_2": rbuffer_stats_blue,
                       "TABLE_FIELD": 'ID',
                       "TABLE_FIELD_2": 'ID',
                       "OUTPUT_LAYER": SLIC_rbuffer_stats_blue})
    print "--> Join attribute table of buffer statistics (right) with SLIC lines.\n"

SLIC_lbuffer_stats_blue = os.getcwd() + r"\34_SLIC_lbuffer_stats_blue.shp"
if not os.path.isfile(SLIC_lbuffer_stats_blue):
    processing.runalg('qgis:joinattributestable',
                      {"INPUT_LAYER": SLIC_rbuffer_stats_blue,
                       "INPUT_LAYER_2": lbuffer_stats_blue,
                       "TABLE_FIELD": 'ID',
                       "TABLE_FIELD_2": 'ID',
                       "OUTPUT_LAYER": SLIC_lbuffer_stats_blue})
    print "--> Join attribute table of buffer statistics (left) with SLIC lines.\n"

#########################
### Gradient measures ###
#########################
SLIC_red_gradient = os.getcwd() + r"\35_SLIC_red_gradient.shp"
if not os.path.isfile(SLIC_red_gradient):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": SLIC_lbuffer_stats_blue,
                       "FIELD_NAME": "red_grad",
                       "FIELD_TYPE": 0,
                       "FORMULA": 'abs("r_red_medi" - "l_red_medi")',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": SLIC_red_gradient})
    print "--> Calculated gradient measure.\n"

SLIC_green_gradient = os.getcwd() + r"\36_SLIC_green_gradient.shp"
if not os.path.isfile(SLIC_green_gradient):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": SLIC_red_gradient,
                       "FIELD_NAME": "green_grad",
                       "FIELD_TYPE": 0,
                       "FORMULA": 'abs("r_gre_medi" - "l_gre_medi")',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": SLIC_green_gradient})
    print "--> Calculated gradient measure.\n"

SLIC_blue_gradient = os.getcwd() + r"\37_SLIC_blue_gradient.shp"
if not os.path.isfile(SLIC_blue_gradient):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": SLIC_green_gradient,
                       "FIELD_NAME": "blue_grad",
                       "FIELD_TYPE": 0,
                       "FORMULA": 'abs("r_blu_medi" - "l_blu_medi")',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": SLIC_blue_gradient})
    print "--> Calculated gradient measure.\n"

SLIC_dsm_gradient = os.getcwd() + r"\38_SLIC_dsm_gradient.shp"
if not os.path.isfile(SLIC_dsm_gradient):
    processing.runalg('qgis:fieldcalculator',
                      {"INPUT_LAYER": SLIC_blue_gradient,
                       "FIELD_NAME": "dsm_grad",
                       "FIELD_TYPE": 0,
                       "FORMULA": 'abs("r_dsm_medi" - "l_dsm_medi")',
                       "NEW_FIELD": True,
                       "OUTPUT_LAYER": SLIC_dsm_gradient})
    print "--> Calculated gradient measure.\n"

######################
### Prepare export ###
######################
# Delete unwanted fields in attribute table
layer = iface.addVectorLayer(SLIC_dsm_gradient, "SLIC_final", "ogr")

accepted_attributes = {"ID", "length", "ucm_rgb", "lap_dsm", "dist_to_gP", "azimuth", "sinuosity", "azi_gPb",
                       "r_dsm_medi", "l_dsm_medi", "r_red_medi", "l_red_medi", "r_gre_medi", "l_gre_medi",
                       "r_blu_medi", "l_blu_medi", "red_grad", "green_grad", "blue_grad", "dsm_grad", "boundary"}
field_names = [field.name() for field in layer.fields()]

with edit(layer):
    # Assign count in reverse order for each field which will be used as index
    for i, j in reversed(list(enumerate(field_names))):
        if j not in accepted_attributes:
            layer.deleteAttribute(i)
print "--> Columns deleted.\n"

# Export attribute table as csv file
SLIC_attr = os.getcwd() + r"\39_SLIC_attr.csv"
if not os.path.isfile(SLIC_attr):
    QgsVectorFileWriter.writeAsVectorFormat(layer, SLIC_attr, "utf-8", None, "CSV")
    print "--> Attribute table exported.\n"

QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])

print "All processing finished."

"""
### Notes ###
# QGIS help

import processing
processing.alghelp("qgis:fieldcalculator")
processing.alghelp("grass7:v.clean")
processing.alglist("g.extension")

# Code Snippets
# Add boundary field per line segment
SLIC_boundary = os.getcwd() + r"\24_SLIC_final.shp"
if not os.path.isfile(SLIC_boundary):
    processing.runalg('qgis:addfieldtoattributestable',
                      {"INPUT_LAYER": SLIC_dsm_gradient,
                       "FIELD_NAME": "boundary",
                       "FIELD_TYPE": 0,
                       "FIELD_LENGTH": 1,
                       "OUTPUT_LAYER": SLIC_boundary})
    print "--> Added boundary filed to attribute table.\n"

Alternative to filter out certain lines by expression with GRASS instead of QGIS (here more files are created)
# Filter out unconnected segments (small dead-end segments resulting from snapping)
SLIC_unwanted = os.getcwd() + r"\11_SLIC_unwanted.shp"
if not os.path.isfile(SLIC_unwanted):
    processing.runalg('grass7:v.extract',
                      {"input": SLIC_azimuth,
                       "where": 'azimuth is NULL',
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "GRASS_OUTPUT_TYPE_PARAMETER": 2,
                       "output": SLIC_unwanted})
    print "--> Filtered out unwanted line segments.\n"

SLIC_filtered = os.getcwd() + r"\12_SLIC_filtered.shp"
if not os.path.isfile(SLIC_filtered):
    processing.runalg('grass7:v.select',
                      {"ainput": SLIC_azimuth,
                       "atype": 1,
                       "binput": SLIC_unwanted,
                       "btype":1,
                       "operator":0,
                       "-r": True,
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "GRASS_OUTPUT_TYPE_PARAMETER": 2,
                       "output": SLIC_filtered})
    print "--> Deleted out unwanted line segments.\n"


# Alternative to capture mean ucm value per line that does not work
# Buffer SLIC lines with 0.05m radius
buffer = os.getcwd() + r"\5_SLIC_buffer.shp"
buff_dist = 0.05
if not os.path.isfile(buffer):
    processing.runalg('qgis:fixeddistancebuffer',
                      {"INPUT": bpol_length,
                       "DISTANCE": buff_dist,
                       "DISSOLVE": False,
                       "OUTPUT": buffer})
    print "--> Buffered SLIC lines with 0.05m radius.\n"

# Calculate zonal statistics per buffer feature
# ?# Seems to have a bug: https://issues.qgis.org/issues/17161, this step only works when done manualy in QGOS 2.14
zonalstats = os.getcwd() + r"\6_SLIC_zonalstats.shp"
if not os.path.isfile(zonalstats):
    processing.runalg('qgis:zonalstatistics',
                      {"INPUT_RASTER": ucm_rlayer,
                       "INPUT_VECTOR": buffer,
                       "COLUMN_PREFIX": "ucm_",
                       "GLOBAL_EXTENT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "OUTPUT_LAYER": zonalstats})
    print "--> Calculated zonal statistics per buffer feature.\n"
# Join attributes by location
SLIC_update = os.getcwd() + r"\7_SLIC_zonalstats.shp"
if not os.path.isfile(SLIC_update):
    processing.runalg('qgis:joinattributesbylocation',
                      {"TARGET": bpol_length,
                       "JOIN": zonalstats,
                       "PREDICATE": 'touches',
                       "STATS": 'median',
                       "SUMMARY": 1,
                       "KEEP": 1,
                       "OUTPUT": SLIC_update})
    print "--> Joined attributes by location.\n"

# Calculate zonal statistics per buffer feature
zonalstats = os.getcwd() + r"\5_SLIC_ucm.shp"
if not os.path.isfile(zonalstats):
    processing.runalg('grass7:v.rast.stats',
                      {"map": bpol_length,
                       "raster": ucm_rlayer,
                       "column_prefix": "ucm",
                       # "method": 'average',
                       "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                       "GRASS_OUTPUT_TYPE_PARAMETER": 3,
                       "output": zonalstats})
    print "--> Calculated zonal statistics per buffer feature.\n"

# To identify wanted field name index: 
layer.fieldNameIndex('r_red_med')

### Removed parts of code 
# Snap all SLIC lines to close gaps and to smooth the outlines
snap = os.getcwd() + r"\1_SLIC_snap.shp"
if not os.path.isfile(snap):
    processing.runalg('grass7:v.clean', {"input": SLIC_lines,
                                         "tool": 1,
                                         "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                                         "output": snap})
    print "--> Snapped all SLIC lines to close gaps and to smooth the outlines.\n"

# Break each line at each point shared between 2 and more lines (vertices)
bpol = os.getcwd() + r"\2_SLIC_bpol.shp"
if not os.path.isfile(bpol):
    processing.runalg('grass7:v.clean', {"input": snap,
                                         "tool": 0,
                                         "GRASS_REGION_PARAMETER": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                                         "output": bpol})
    print "--> Broke each line at each point shared between 2 and more lines (vertices).\n"

# Delete count column
# RGB
SLIC_ucm_RGB_update = os.getcwd() + r"\7_SLIC_ucm_RGB_update.shp"
if not os.path.isfile(SLIC_ucm_RGB_update):
    processing.runalg('qgis:deletecolumn',
                      {"INPUT": SLIC_ucm_DSM,
                       "COLUMN": 'count',
                       "OUTPUT": SLIC_ucm_RGB_update})
    print "--> Column deleted.\n"

# DSM
SLIC_ucm_DSM_update = os.getcwd() + r"\7_SLIC_ucm_DSM_update.shp"
if not os.path.isfile(SLIC_ucm_DSM_update):
    processing.runalg('qgis:deletecolumn',
                      {"INPUT": SLIC_ucm_RGB_update,
                       "COLUMN": 'count_1',
                       "OUTPUT": SLIC_ucm_DSM_update})
    print "--> Column deleted.\n"

# Delete columns
layer = iface.addVectorLayer(SLIC_lbuffer_stats, "SLIC_lbuffer_stats", "ogr")
layer.dataProvider().deleteAttributes([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26,
                                       27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 43])
layer.updateFields()
QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])
"""
