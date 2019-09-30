Image segmentation is based on Multiscale Combinatorial Grouping (MCG).

Instructions on how to apply image segmentation can be found in the wiki:
https://github.com/SCrommelinck/Delineation-Tool/wiki/1)-Image-Segmentation

The MCG source code has been made available under:
https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/mcg/#code

We have modified the follwoing scripts:
\MCG\pre-trained\demos\mcg.m -> to call MCG image segmentation
\MCG\pre-trained\scripts\geotiffwrapper.m -> to define EPSG code in input raster data
\MCG\pre-trained\scripts\geotiffwrite.m -> to write EPSG code from input to output raster

