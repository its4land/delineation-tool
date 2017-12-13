"""
!/bin/python
-*- coding: utf-8 -*
QGIS Version: QGIS 2.16

### Author ###
 S. Crommelinck, 2017

### Description ###
 This script resamples all input UAV images in a given directory to rasters of a predefined amount of pixels in
 width and height. Each resampled raster is then tiled to multiple rasters of 1000 pixels in width and height. The
 resulting raster files can be used as input to gPb, which is designed to work on images of 1000 x 1000 pixels.

### Requirements ###
 Input UAV images should have 3 bands (RGB). If the original data has more bands, they can be cropped in the
 OSGeo4W Shell with gdal_translate -b 1 -b 2 -b 3 input.tif output.tif. The input images should then be cropped to a
 quadratic polygon, which is created with 'Improved Polygon Capturing plugin' with gdalwarp -crop_to_cutline -cutline
 input.shp input.tif output.tif. Watch out that both have the same CRS and the shapefile only contains one attribute.
 To create a tfw file use: gdal_translate -co "TFW=YES" in.tif out.tif
 Executing the following gPb_ucm_final.m script, sometimes causes Matlab to crash, here what I found out in this
 context: The RGB seems to require less downsampling than the DSM. The no-data value has no influence.
"""

### Import script in QGIS Python console ###
"""
# add directory with script to Python search path
import sys
sys.path.append(r"D:\path to script")

# import own module
import A1_resizing

# rerun module after changing the source code
reload(A1_resizing)
"""

### Predefine variables ###
# Data directory of input UVA imagery (RGB)
data_dir = r"D:\path to directory"

# Initial width/height of output raster in pixels
pix_min = 1000

# Final width/height of output raster in pixels
pix_max = 1000

# Increment steps in width/height of output raster in pixels
pix_step = 1000

# Resampling method, available methods in gdalogr:translate {nearest(default),bilinear,cubic,cubicspline,lanczos,
# average,mode}
res_method = "nearest"

# (Re)initialize counter for number of tiles, number needs to be multiplied by itself for final number of tiles (e.g.
#  tiles = 2 results in 4 final tiles, tiles = 3 results in 9 final tiles)
tiles = 2

### Import required QGIS modules ###
# noinspection PyUnresolvedReferences
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.utils import *
from qgis.analysis import *
import processing
import os

### Main processing part ###
# Change into data directory
os.chdir(data_dir)
files = os.listdir(os.curdir)

# Loop over all .tif files in input directory
for f in files:
    # Check if file extension is .tif
    if os.path.splitext(f)[1] == '.tif':

        # Load UAV image as raster layer
        fileInfo = QFileInfo(f)
        baseName = fileInfo.baseName()
        filePath = str(os.path.abspath(f))
        rlayer = QgsRasterLayer(filePath, baseName)

        # Check validity of raster layer and print user message
        print "%s is loaded as a valid input raster.\n" % f
        if not rlayer.isValid():
            print "%s failed to load!\n" % f

        # Read, save and print raster layer extent
        extent = rlayer.extent()
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()
        x_range = xmax - xmin
        y_range = ymax - ymin
        print "The extent (xmin, xmax, ymin, ymax) of %s is: %f, %f, %f, %f\n" % (f, xmin, xmax, ymin, ymax)
        print "The range of %s is %i in x-direction and %i in y-direction.\n" % (f, x_range, y_range)

        # Check if directory to store output files exists and create if not
        directory = "Resizing_" + str(os.path.splitext(f)[0])
        if os.path.exists(directory):
            print "The directory %s has already been created.\n" % directory
        else:
            print "The directory %s has been created.\n" % directory
            os.mkdir(directory)

        # Change into (newly) created directory
        os.chdir(directory)

        # (Re)initialize minimum width/height of output raster in pixels
        j = pix_min

        ### Resample rasters of width/height from pix_min to pix_max at increment steps of pix_step ###
        while j <= pix_max:
            print "### Resampling input of %i pixels ###\n" % j
            # Define name of resampled raster
            resampled = str(os.path.splitext(f)[0] + "_" + str(j) + "pixels_" + res_method + ".tif")

            # Run resampling of raster
            processing.runalg('gdalogr:translate', {"INPUT": rlayer, "OUTSIZE": j, "OUTSIZE_PERC": False, "EXPAND": 0,
                                                    "EXTRA": "-r {%s}" % res_method,
                                                    "PROJWIN": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                                                    "OUTPUT": resampled})
            print "--> %s has been resampled to a raster of %i pixels in width/height and saved as %s in %s\n" % (
                f, j, resampled, directory)

            ### Create tiles of 1000 pixels in width/height from downsampled rasters ###
            print "### Tiling input of %i pixels ###\n" % j
            # Description:
            # The image is tiled as follows:
            # First, the bottom left tile is created (first loop)
            # Then, all tiles in that bottom row (all in x direction) are created (second loop)
            # Then, the tiling restarts at the left side but moves up one tiling window (+1 in y direction) (first loop)
            # Then, all tiles in that row (all in x direction are created (second loop)
            # This iteration continues, until all tiles are created

            # Load resampled raster layer
            fileInfo = QFileInfo(resampled)
            baseName = fileInfo.baseName()
            filePath = str(os.path.abspath(resampled))
            reslayer = QgsRasterLayer(filePath, baseName)

            # Check validity of raster layer and print user message
            print "%s is loaded as a valid resampled raster.\n" % resampled
            if not reslayer.isValid():
                print "%s failed to load!\n" % resampled

            print "%s will now be tiled in %i raster(s) of 1000 pixels in width/height...\n" % (
                resampled, tiles * tiles)

            # Create tiles
            for k in range(0, tiles):
                # Set extent for tiling
                t_xmin = xmin
                t_xmax = xmin + (x_range / tiles)
                t_ymin = ymin + k * (y_range / tiles)
                t_ymax = ymin + (k + 1) * (y_range / tiles)

                # Define name of tiled raster
                tiled = str(
                    os.path.splitext(f)[0] + "_" + str(j) + "pixels_" + res_method + "_tiling_x0y" + str(k) + ".tif")

                # Uncomment the next line if the raster should only be tiled without being resampled
                # reslayer = rlayer

                # Run tiling of raster and save TIF and TFW File
                processing.runalg('gdalogr:cliprasterbyextent',
                                  {"INPUT": reslayer, "PROJWIN": "%f,%f,%f,%f" % (t_xmin, t_xmax, t_ymin, t_ymax),
                                   "TFW": True, "OUTPUT": tiled})
                print "--> %s has been tiled and saved as %s in %s\n" % (resampled, tiled, directory)

                # Create all tiles of specific row in x direction
                for l in range(0, tiles - 1):
                    t_xmin = t_xmax
                    t_xmax = t_xmin + (x_range / tiles)

                    # Define name of tiled raster
                    tiled = str(os.path.splitext(f)[0] + "_" + str(j) + "pixels_" + res_method + "_tiling_x" + str(
                        l + 1) + "y" + str(k) + ".tif")

                    # Run tiling of raster save TIF and TFW File
                    processing.runalg('gdalogr:cliprasterbyextent',
                                      {"INPUT": reslayer, "PROJWIN": "%f,%f,%f,%f" % (t_xmin, t_xmax, t_ymin, t_ymax),
                                       "TFW": True, "OUTPUT": tiled})
                    print "--> %s has been tiled and saved as %s in %s\n" % (resampled, tiled, directory)

            # Increment width/height of output raster in pixels
            j += pix_step

            # Print final tiling message
            print "Tiling of %s finished.\n" % resampled

# Change into initial working directory
os.chdir("..")

# Print final overall message
print "All processing has been finished."


"""
### Notes ###
# QGIS help
processing.alghelp("gdalogr:translate")
processing.alghelp("gdalogr:cliprasterbyextent")
processing.alghelp("gdalogr:warpreproject")

# Websites:
http://docs.qgis.org/2.6/de/docs/user_manual/processing_algs/gdalogr/gdal_conversion/translate.html
http://www.gdal.org/gdal_translate.html
"""


