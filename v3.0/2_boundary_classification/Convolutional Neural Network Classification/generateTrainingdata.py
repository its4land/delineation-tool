#!/bin/python
# -*- coding: utf-8 -*-
# Description: this script loops over all features of given shapefile and saves clipped rasters around each line's
# pixel according to its boundary label in a specific folder.
# Author: Sophie Crommelinck
#######################################################

# Import modules
from numpy import *
import sys
from osgeo import gdal, ogr, osr
import os
import time

# Define input params
boundaryDict = r"path_to_boundary_tiles_folder"
noboundaryDict = r"path_to_no_boundary_tiles_folder"
MCGpointsFile = "path_to_MCG_points_shapefile"
FiveBandRasterFile = "path_to_5bandraster"
tileDimension = 224

# Start timing
start = time.time()

# Change to working directory
os.chdir(dict)

# Open MCG points
driver = ogr.GetDriverByName('ESRI Shapefile')
datasource = driver.Open(MCGpointsFile, 0)
if datasource is None:
	print('Could not open %s' % MCGpointsFile)
	sys.exit(1)
layer = datasource.GetLayer()
points = layer.GetFeatureCount()


# Open raster
ds = gdal.Open(FiveBandRasterFile)
if ds is None:
	print('Could not open %s' % FiveBandRasterFile)
	sys.exit(1)

# Read raster content
cols = ds.RasterXSize
rows = ds.RasterYSize
geotransform = ds.GetGeoTransform()
originX = geotransform[0]
originY = geotransform[3]
pixelWidth = geotransform[1]
pixelHeight = geotransform[5]

# Print info
print("%i points to be processed for a raster of %i rows and %i cols..." % (points, rows, cols))

# Read data
band1 = ds.GetRasterBand(1)
red = band1.ReadAsArray(0, 0, cols, rows).astype(int)

band2 = ds.GetRasterBand(2)
green = band2.ReadAsArray(0, 0, cols, rows).astype(int)

band3 = ds.GetRasterBand(3)
blue = band3.ReadAsArray(0, 0, cols, rows).astype(int)

band4 = ds.GetRasterBand(4)
cad = band4.ReadAsArray(0, 0, cols, rows).astype(int)

band5 = ds.GetRasterBand(5)
mcg = band5.ReadAsArray(0, 0, cols, rows).astype(int)

# Prepare output rasters
driver = gdal.GetDriverByName('GTiff')
rasterSRS = osr.SpatialReference()
rasterSRS.ImportFromWkt(ds.GetProjectionRef())

# Initialize counters
bTileCount = 0
nbTileCount = 0
outboundFail = 0
createRasterFail = 0
loop = 0

# Loop over all features in input
for feature in layer:
    loop += 1
    # Get geometry of feature
    geometry = feature.GetGeometryRef()

    # Get coordinates of point
    x = geometry.GetX()
    y = geometry.GetY()

    # Compute column index and row index for coordinates (X,Y)
    xOffset = int((x - originX) / pixelWidth)
    yOffset = int((y - originY) / pixelHeight)

    if (xOffset < 0) or (yOffset < 0) or (xOffset - tileDimension / 2 < 0) or (xOffset > cols - tileDimension/2) or (yOffset - tileDimension / 2 < 0) or (yOffset > rows - tileDimension/2):
        outboundFail+=1
        continue

    try:
        # Check if cad and mcg are 1 and define output file name
        featID = feature.GetField('ID')
        if ((cad[yOffset, xOffset] == 1) and (mcg[yOffset, xOffset] == 1)):
            bTileCount += 1
            outrasterFilename = boundaryDict + r"\b1_" + str(featID) + "_" + str(bTileCount) + ".tif"

        else:
            nbTileCount += 1
            outrasterFilename = noboundaryDict + r"\b0_" + str(featID) + "_" + str(nbTileCount) + ".tif"

        # Create 3-band raster with dimension 224 x 224 around point
        xOffsetClip = int(xOffset-tileDimension/2)
        yOffsetClip = int(yOffset-tileDimension/2)
        originXClip = x - tileDimension/2*pixelWidth
        originYClip = y - tileDimension/2*pixelHeight

        outRaster = driver.Create(outrasterFilename, tileDimension, tileDimension, 3, gdal.GDT_Byte)
        outRaster.SetGeoTransform((originXClip, pixelWidth, 0, originYClip, 0, pixelHeight))
        outRaster.SetProjection(rasterSRS.ExportToWkt())

        redClip = band1.ReadAsArray(xOffsetClip, yOffsetClip, tileDimension, tileDimension).astype(int)
        greenClip = band2.ReadAsArray(xOffsetClip, yOffsetClip, tileDimension, tileDimension).astype(int)
        blueClip = band3.ReadAsArray(xOffsetClip, yOffsetClip, tileDimension, tileDimension).astype(int)

        outBandRed = outRaster.GetRasterBand(1)
        outBandRed.WriteArray(redClip)

        outBandGreen = outRaster.GetRasterBand(2)
        outBandGreen.WriteArray(greenClip)

        outBandBlue = outRaster.GetRasterBand(3)
        outBandBlue.WriteArray(blueClip)

        outRaster.FlushCache()
        del outRaster
        redClip = None
        greenClip = None
        blueClip = None


        if loop % 10000 == 0:
            print("Processing ongoing (%i%%)" % (loop/points*100))

    except:
        createRasterFail+=1
        print("Error in tile handling.")

# Clean up
datasource = None
ds = None
red = None
green = None
blue = None
cad = None
mcg = None
end = time.time()
runtime = end - start

# print("%i points processed for a raster of %i rows and %i cols." % (layer.GetFeatureCount(), rows, cols))
print("%i tiles of %i x %i created." % (bTileCount+nbTileCount, tileDimension, tileDimension))
print("%i (%i%%) tiles identified as boundary tiles." % (bTileCount, bTileCount/(bTileCount+nbTileCount)*100))
print("%i (%i%%) tiles identified as no boundary tiles." % (nbTileCount, nbTileCount/(bTileCount+nbTileCount)*100))
print("%i tiles failed (outboundFail)." % outboundFail)
print("%i tiles failed (createRasterFail)." % createRasterFail)
print("All processing finished. Processing took %i minutes" % int(runtime/60))
