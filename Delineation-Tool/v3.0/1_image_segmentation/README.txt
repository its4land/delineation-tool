the source code has been made available under:
https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/mcg/#code

We have modified the follwoing scripts:
\MCG\pre-trained\demos\mcg.m -> to call MCG image segmentation
\MCG\pre-trained\scripts\geotiffwrapper.m -> to define EPSG code in input raster data
\MCG\pre-trained\scripts\geotiffwrite.m -> to write EPSG code from input to output raster

How to run MCG image segmentation:
- save data to be processed in \MCG\pre-trained\demos\data
- change EPSG code in \MCG\pre-trained\scripts\geotiffwrapper.m to that of your data -> A.ProjectedCSTypeGeoKey = EPSG_Code
- set parameters ks , myDir, outDir in \MCG\pre-trained\demos\mcg.m
- run \MCG\pre-trained\demos\mcg.m