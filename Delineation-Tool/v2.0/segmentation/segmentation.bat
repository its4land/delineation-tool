@echo off
:gdal-segment [-help] src_raster1 src_raster2 .. src_rasterN -out dst_vector
:    [-of <output_format> 'ESRI Shapefile' is default]
:    [-b R B (N-th band from R-th raster)] [-algo <LSC, SLICO, SLIC, SEEDS>]
:    [-niter <1..500>] [-region <pixels>]
:    [-blur (apply 3x3 gaussian blur)]
:gdal-segment Muhoza_RGB_GSD_5cm_250x250.tif -out Muhoza_RGB_GSD_5cm_250x250_slic_iter10.shp -algo SLIC -niter 10
:gdal-segment Muhoza_RGB_GSD_5cm_250x250.tif -out Muhoza_RGB_GSD_5cm_250x250_slic_iter100.shp -algo SLIC -niter 100
:gdal-segment Muhoza_RGB_GSD_5cm_250x250.tif -out Muhoza_RGB_GSD_5cm_250x250_slic_iter100_blur.shp -algo SLIC -niter 100 -blur
gdal-segment Muhoza_RGB_GSD_5cm_250x250.tif -out Muhoza_RGB_GSD_5cm_250x250_slico_iter50_region25_blur.shp -algo SLICO -niter 50 -region 25 -blur
pause
