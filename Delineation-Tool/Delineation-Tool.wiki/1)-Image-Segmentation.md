### Description:
Image segmentation groups similar pixels into segments. The segmentation delivers closed contours capturing the outlines of visible objects ([Figure 1](#Figure1)). In this wiki, the use of [Multiscale Combinatorial Grouping (MCG)](https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/mcg/#) is described. MCG is a free and open source method developed by Berkley University that we have modified for georeferenced remote sensing imagery. The [source code](https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/mcg/#code) is pre-complied to be used in [Matlab](https://mathworks.com/products/matlab.html) under Linux.
<p align="center">
  <img src="https://user-images.githubusercontent.com/28596024/60792796-a0526000-a166-11e9-9b8e-dc6b8966ecbc.png" title="Image segmentation" width="600">
<p align="center">
<a name="Figure1"><font size="1">Figure 1:</a> Image segmentation delivers closed contours (right) capturing the outlines of visible objects in a remote sensing image (left). </font>

After applying MGC image segmentation, we convert the MCG raster to vector lines ([Figure 2](#Figure2)) and apply line filtering ([Figure 3](#Figure3)). These steps can be conducted in any GIS such as the free and open source [QGIS](https://qgis.org/en/site/) or the commercial [ESRI ArcGIS](https://www.esri.com/en-us/arcgis/about-arcgis/overview).

<p align="center">
  <img src="https://user-images.githubusercontent.com/28596024/60800965-66895580-a176-11e9-9070-63793fe0e9fe.png" title="Raster to vector conversion" width="600">
<p align="center">
<a name="Figure2"><font size="1">Figure 2:</a> Remote sensing image (left). MCG image segmentation result in raster format (middle). MCG lines derived from raster to vector conversion (right). </font>


<p align="center">
  <img src="https://user-images.githubusercontent.com/28596024/60966792-5a89c900-a319-11e9-862f-3f59bb9a26e3.png" title="MCG line filtering" width="600">
<p align="center">
<a name="Figure3"><font size="1">Figure 3:</a> MCG line filtering reducing the line count by 80%. </font>




### Input:
* RGB orthoimage **raster** `.tif`
* Word file `.tfw`

### Output:
* image segmentation **lines** without attributes `.shp`

### Steps:
1. [**Install Matlab & MCG image segmentation**](#Install-MCG)
2. [**Prepare input orthoimage**](#Prepare-input)
3. [**Run MCG**](#Run-MCG)
4. [**Raster to vector conversion**](#Postprocess-MCG1)
5. [**Line filtering**](#Postprocess-MCG2)

* [**General notes**](#General-notes)
* [**References**](#References)

See below for details on each step.
***
***
## <a name="Install-MCG"></a>1. Install Matlab & MCG image segmentation
* Install [Matlab](https://mathworks.com/products/matlab.html) 
    *  instructions on how to install the software are provided on the [Matlab website](https://mathworks.com/help/install/ug/install-mathworks-software.html)
* Download our [modified MCG version](https://github.com/SCrommelinck/Delineation-Tool/tree/master/v3.0/1_image_segmentation/MCG) from GitHub to your Linux computer and save in a `MCG` folder

    <p> <img src="https://user-images.githubusercontent.com/28596024/60793718-8ca7f900-a168-11e9-942f-4f71b6c5115f.png"   title="Change working directory" width="500">
            
## <a name="Prepare-input"></a>2. Prepare input orthoimage
Depending on the memory capacity of your computer, you might have to clip your RGB orthoimage **raster** (`.tif`) into tiles that do not exceed 10,000 x 10,000 pixels.
* Open your orthoimage in QGIS
    * Right click your orthoimage | `Export` | `Save As...` | Enable `Create VRT`| Define a file name with `...` | Set VRT Tiles `max columns` and `max rows` to `10000 ` or lower | Click `OK`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60668380-19526e80-9e6c-11e9-95c2-ee00173bd958.png" width="500">  
         
         * Alternatively, you can clip your orthoimage in the `OSGeo4W` shell with `gdalwarp -crop_to_cutline -cutline clip.shp orthoimage.tif orthoimage_clipped.tif`

Create a world file for each tiled orthoimage
* Open `OSGeo4W` shell 
     * Select the Windows start button > type `OSGeo4W`
     * Change the shells's working directory to your tiled orthoimages
        * `cd path_to_folder`
            <p> <img src="https://user-images.githubusercontent.com/28596024/60669427-941c8900-9e6e-11e9-8be8-846de5266ae0.png"   title="Change working directory" width="500">
     * Create a `.tfw` file describing the georeference of your orthoimage. The orthoimage will not be changed.
        * `gdal_translate -co "TFW=YES" orthoimage.tif orthoimage_translated.tif`
            <p> <img src="https://user-images.githubusercontent.com/28596024/60669544-dcd44200-9e6e-11e9-8cfb-62f069ce6515.png"   title="gdal_translate" width="500">        
 
## <a name="Run-MCG"></a>3. Run MCG
* Save your RGB orthoimage **raster** (`.tif`) and the corresponding world file (`.tfw`) both having the same name to `\MCG\pre-trained\demos\data`
* Open Matlab
* Add the path of the downloaded MCG folder in Matlab
    * right click on the MCG folder | `Add to Path` | `Selected Folders and Subfolders`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60666618-bc54b980-9e67-11e9-941d-633581434880.png" title="Add path in Matlab" width="700">  
* change the EPSG code in `\MCG\pre-trained\scripts\geotiffwrapper.m` to that of your orthoimage
    * `A.ProjectedCSTypeGeoKey` = your EPSG code
            <p> <img src="https://user-images.githubusercontent.com/28596024/60794074-3d15fd00-a169-11e9-880c-000bde0af389.png" title="Set EPSG code" width="700">
    * You can check the EPSG code of your orthoimage by opening it in QGIS and reading the EPSG code from the bottom right corner 
        <p> <img src="https://user-images.githubusercontent.com/28596024/60670084-1c4f5e00-9e70-11e9-8db0-cd52ae942545.png" title="Check EPSG code in QGIS" width="700"> 
        
        or by right clicking your orthoimage | `Properties` | `Information`
* set all parameters under `%%Predefine variables%%` in `\MCG\pre-trained\demos\mcg.m`

    * `k`: value between 0 and 1 that regulates over- and under-segmentations. 
        * Low values produce more boundaries and thus more over-segmentation. For our test data of 0.25 m GSD, we set `k = 0.1` to produce over-segmentation. This setting creates outlines around the majority of visible objects. Tests with higher values (`k = 0.3` and `k = 0.5`) resulting in less over-segmentation show that visible object outlines are partly missed, while irrelevant lines around small objects are still produced. For high-resolution imagery of 0.05 cm GSD, we set `k = 0.3` or `k = 0.4`. 
    * `ext`: appendix added to output boundary map files. You could chose any text you like to later identify your results.
    * `myDir`: path to input data directory
    * `outDir`: path to store output data
 
        <p> <img src="https://user-images.githubusercontent.com/28596024/60795130-633c9c80-a16b-11e9-933e-ae2d40472913.png" title="Set variables in mcg.m" width="700"> 
 
 
 * run `\MCG\pre-trained\demos\mcg.m`
    * right click on `mcg.m` | `run`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60671321-21fa7300-9e73-11e9-8e79-fd6e1cddeae6.png" title="run mcg.m" width="700"> 
    * MCG will be applied to each orthoimage stored in `myDir`
***
***
## <a name="Postprocess-MCG1"></a>4. Raster to vector conversion   
The result of `mcg.m` are binary rasters, in which the value **1** is assigned to _boundary_ pixels and **0** to _not boundary_ pixels. These rasters need to converted to a vector line format ([Figure 2](Figure 2) and [Figure 4](Figure 4)).
     
<p align="center">
  <img src="https://user-images.githubusercontent.com/28596024/60967103-24007e00-a31a-11e9-974d-79d9745855c2.png" title="Raster to vector conversion" width="600">
<p align="center">
<a name="Figure4"><font size="1">Figure 4:</a> Raster to vector conversion, which converts the binary MCG boundary map (black and white pixels) to a vector line layer (red lines). </font>

**Convert raster to vector**
* Open ArcGIS
* Open Search (Ctrl + F) and search for `Raster to Polyline`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60801970-3478f300-a178-11e9-8a12-8cdc9494d825.png" title="Set variables in mcg.m" width="700"> 

* Run `Raster to Polyline`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60801749-d6e4a680-a177-11e9-8c13-b385cd9b7364.png" title="Raster to polyline in ArcGIS" width="700"> 


## <a name="Postprocess-MCG2"></a>4. Line filtering (optional)
To reduce the number of irrelevant lines produced through over-segmentation, lines can be simplified through filtering: lines around areas smaller than 30 m<sup>2</sup> are merged to the neighboring segments, which reduces the line count by roughly 80%. According to our visual inspections, this post-processing removes artefacts in the segmentation results and keeps outlines of large objects being more relevant for cadastral mapping.

**Simplify segment lines**
* Download the toolbox from [Github](https://github.com/SCrommelinck/Delineation-Tool/blob/master/v3.0/3_interactive_delineation/SimplifySegmentation.tbx) that contains our tool `SimplifySegmentation`
    * `SimplifySegmentation` is a tool created with the `Model Builder` that combines different ArcGIS toolbox functionalities:
        <p> <img src="https://user-images.githubusercontent.com/28596024/61037770-fbd15780-a3cb-11e9-89a6-03b00226bde5.png" title="SimplifySegmentation ArcGIS" width="700"> 
* Add the downloaded toolbox in ArcMap
    * right click in `ArcToolbox` window | `Add Toolbox...`
            <p> <img src="https://user-images.githubusercontent.com/28596024/61208564-fd668c80-a6f7-11e9-9ad4-2cff8d6ab498.png" title="Add toolbox in ArcMap" width="700"> 
    * Load the downloaded toolbox
            <p> <img src="https://user-images.githubusercontent.com/28596024/61208832-8e3d6800-a6f8-11e9-8f1b-150586cf12fd.png" title="Add toolbox in ArcMap" width="700">
* Open the tool `SimplifySegmentation`, which should now appear as a new toolbox in your `ArcToolbox`
    <p> <img src="https://user-images.githubusercontent.com/28596024/61208880-ac0acd00-a6f8-11e9-88ba-29afd46201f1.png" width="500">
* Run `SimplifySegmentation`    
    * select lines to be simplified as `Input Lines` 
    * set path to store simplified lines as `Output Lines`
        <p> <img src="https://user-images.githubusercontent.com/28596024/61038806-eeb56800-a3cd-11e9-982a-667d3f40c7a9.png" title="SimplifySegmentation ArcGIS" width="700"> 

        <p> <img src="https://user-images.githubusercontent.com/28596024/61038928-27554180-a3ce-11e9-8073-f4b582b2766e.png" title="SimplifySegmentation ArcGIS" width="300">



***
***
**Post-processing in QGIS**
The post-processing steps described in ArcGIS can also be performed in QGIS 

**Convert raster to vector**
* refer to instructions on [Stack Exchange](https://gis.stackexchange.com/questions/251360/converting-raster-to-vector-by-generating-center-lines)

**Simplify segment lines**
* the same 
        <p> <img src="https://user-images.githubusercontent.com/28596024/61209358-d1e4a180-a6f9-11e9-97f4-a40d88990f5b.png" title="SimplifySegmentation QGIS" width="500">
***
***
### General notes:
* In comparison to the original [MGC source code](https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/mcg/#code), we have modified the following scripts:
    * `\MCG\pre-trained\demos\mcg.m` -> to call MCG image segmentation
    * `\MCG\pre-trained\scripts\geotiffwrapper.m` -> to define EPSG code in input raster data
    * `\MCG\pre-trained\scripts\geotiffwrite.m` -> to write EPSG code from input to output raster

***
***
### References:
*  the MCG source code developed by Berkley University that we have modified for georeferenced remote sensing imagery is publically available [here](https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/mcg/#code)