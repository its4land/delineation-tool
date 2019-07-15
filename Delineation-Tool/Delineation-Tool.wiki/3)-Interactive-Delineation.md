### Description:
Interactive delineation supports the creation of final cadastral boundaries. The interactive delineation is implemented in the open source geographic information system QGIS as _BoundaryDelineation_ plugin. The plugin contains different functionalities to delineate parcels from imagery ([Table 1](#Table1), [Figure 1](#Figure1)).

<p align="center">
  <img src="https://user-images.githubusercontent.com/28596024/60505943-0b161e00-9cc5-11e9-8e44-035b46085dcd.png" title="Delineation functionalities of BoundaryDelineation QGIS plugin." width="600">

<p align="center">
<a name="Table1"><font size="1">Table 1:</a> Delineation functionalities of BoundaryDelineation QGIS plugin.</font>

<p align="center">
<img src="https://user-images.githubusercontent.com/28596024/60505997-2bde7380-9cc5-11e9-9126-ed5b95924361.png"   title="Interactive delineation functionalities: (a) connect lines surrounding a click, or (b) a selection of lines. (c) Close endpoints of selected lines to a polygon. (d) Connect lines along least-cost-path." width="500">

<p align="center">
<a name="Figure1"><font size="1">Figure 1:</a> Interactive delineation functionalities: (a) connect lines surrounding a click, or (b) a selection of lines. (c) Close endpoints of selected lines to a polygon. (d) Connect lines along least-cost-path..
</p>

### Input:
* image segmentation **lines** (`.shp`) 
    * with boundary likelihood as attribute (optional) 
* RGB orthoimage **raster** (`.tif`)

### Output:
* final cadastral boundary **lines** (`.shp`) 

### Steps:
1. [**Install QGIS & BoundaryDelineation plugin**](#Install-QGIS)
2. [**Load input data**](#StepI)
3. [**Delineate and save boundaries**](#StepII)
* [**Get help**](#Get-help)
* [**General notes**](#General-notes)
* [**References**](#References)

See below for details on each step.
***
***
## <a name="Install-QGIS"></a>1. Install QGIS & BoundaryDelineation plugin
* Install `QGIS3`, which is a free and open source GIS on your computer by downloading the [QGIS installer](https://qgis.org/en/site/forusers/download.html)
    *  instructions on how to install the software are provided on the [QGIS website](https://www.qgis.org/en/site/forusers/alldownloads.html?highlight=install)
* Install `BoundaryDelineation` plugin from the `QGIS Plugin Manager` 
    *  instructions on how to install the a plugin are provided on the [QGIS website](https://docs.qgis.org/2.8/en/docs/training_manual/qgis_plugins/fetching_plugins.html) and in the [Get help](#Get-help) section of this wiki
    * the plugin's source can be downloaded from the  [QGIS plugin repository](https://plugins.qgis.org/plugins/BoundaryDelineation/)
      <p> <img src="https://user-images.githubusercontent.com/28596024/60661077-755fc780-9e59-11e9-9fb2-300f74d5366c.png" width="700"> 
***
***
## <a name="StepI"></a>2. Load input data
### Goal:
To load input data to be used during the interactive delineation.

### Input:
* image segmentation **lines** (`.shp`) 
    * with boundary likelihood as attribute (optional) 
* RGB orthoimage **raster** (`.tif`)

### Output:
* final cadastral boundary **lines** (`.shp`) 

### Steps:
* `Raster base map`: load RGB orthoimage **raster** (`.tif`) 
    * select file from drop-down list if it is already opened in QGIS or load file by clicking on `...`
* `Segments layer`: load image segmentation **lines** (`.shp`)
    * select file from drop-down list if it is already opened in QGIS or load file by clicking on `...`
    * simplify the input lines to remove zig-zagging along pixels by setting a desired _simplification tolerance_
        * _simplification tolerance_ is a value in meters by which the line is simplified based on douglas-peuker (example: if the value is 1m, the simplified lines are straight for at least 1m before changing direction)
        * _simplification tolerance_ should align with local (cadastral accuracy) requirements and the resolution of the input image (see tooltip in plugin for example values)
      <p> <img src="https://user-images.githubusercontent.com/28596024/60510668-436f2980-9cd0-11e9-85fd-9a74c9a82ef3.png" title="Step I in BoundaryDelineation plugin" width="900">      
* `Output`: save output final cadastral boundary **lines** (`.shp`) 
    * leave empty to create temporary layer (which can be saved later) or define path to save final cadastral boundary layer by clicking on `...` 
* `Its4land Proejct`: load input data saved on the its4land platform
    * Load test data by clicking `Connect`|`Ensoka`|`Ensoka`|`Load as segments layer`
* `Add length attribute`: enable to add a length attribute to the `segments layer`, which can be used for least-cost-path calculation of the `Vertices` functionality in `StepII` 
    <p> <img src="https://user-images.githubusercontent.com/28596024/60509438-284eea80-9ccd-11e9-8a97-0ae775e59949.png" title="Step I in BoundaryDelineation plugin" width="500">  
* `Process`: simplifies `Segments layer` into `Simplified Segments` ( **lines**) based on _simplification tolerance_ and creates `Vertices` (**points**) at intersections of lines in `Segments layer`
    <p> <img src="https://user-images.githubusercontent.com/28596024/60509506-5c2a1000-9ccd-11e9-93fd-473dbea5f6dc.png" title="Step I in BoundaryDelineation plugin" width="500"> 

You now have all required layers displayed in the layer panel:
* `Simplified Segments`: simplified **lines** loaded as `Segments layer` (`.shp`)
* `Vertices`: **points** at intersections of `Simplified Segments` (`.shp`)
* `Candidates`: boundary **lines** that you are currently delineating (`.shp`)
* `Final`: boundary **lines** that you would like to save (`.shp`)
* RGB orthoimage **raster** (`.tif`) you loaded as `Raster base map` 
* image segmentation **lines** (`.shp`)  you loaded as `Segments layer`
      <p> <img src="https://user-images.githubusercontent.com/28596024/60509713-ebcfbe80-9ccd-11e9-8e29-296400405458.png" title="Step I in BoundaryDelineation plugin" width="900"> 
    
***
***

## <a name="StepII"></a>3. Delineate and save boundaries
### Goal:
To interactively delineate final cadastral boundaries.

### Input:
* simplified image segmentation **lines** (`.shp`)
* vertices at intersections of image segmentation **lines** (`.shp`)

### Output:
* final cadastral boundary **lines** (`.shp`) 
* final cadastral boundary **polygons** (`.shp`) (optional)

### Steps:
The plugin offers four functionalities to delineate boundaries ([Table 1](#Table1)).

**Note:**
* Select multiple lines or points by holding `Shift`
* Unselect selected features by  holding `Ctrl`
1. **Polygons**
    * **What:** Connect lines surrounding a click or selection of lines 
    * **How:** Click inside polygon or select lines around which to create a polygon
    * **Shortcut:** `Ctrl + Alt + 1`
      <p> <img src="https://user-images.githubusercontent.com/28596024/60513840-79181080-9cd8-11e9-9f53-d640de26fe89.png" title="Polygons functionality - click inside polygon" width="700">  
      <p> <img src="https://user-images.githubusercontent.com/28596024/60514416-bb8e1d00-9cd9-11e9-99dd-e64d284892ce.png" title="Polygons functionality - select lines" width="700"> 
    
2. **Lines** 
    * **What:** Connect endpoints of selected lines to a polygon regardless of `Simplified Segments` 
    * **How:** Select lines for which endpoints should be closed to a polygon
    * **Shortcut:** `Ctrl + Alt + 2`
      <p> <img src="https://user-images.githubusercontent.com/28596024/60514536-f85a1400-9cd9-11e9-8a6a-2777581b8310.png" title="Lines functionality - select lines" width="700"> 
      
3. **Vertices**
    * **What:** Connect vertices along least-cost-path based on a selected attribute, e.g., boundary likelihood or line length
    * **How:** Select vertices to be connected along least-cost-path based attribute selected in drop-down menu (selected vertices appear yellow)
    * **Shortcut:** `Ctrl + Alt + 3`
      <p> <img src="https://user-images.githubusercontent.com/28596024/60514769-74545c00-9cda-11e9-9fac-059cbad96b85.png" title="Vertices functionality - select vertices" width="700"> 
          
4. **Manual**
    * **What:** Manual delineation with the option to snap to input lines and vertices
    * **How:** Connect manual clicks (enable snapping to snap your manual lines to existing layers)
    * **Shortcut:** `Ctrl + Alt + 4`
          <p> <img src="https://user-images.githubusercontent.com/28596024/60515253-82ef4300-9cdb-11e9-8a19-f360fa7d6307.png" title="Manual functionality - create lines manually " width="700"> 
    

***

After creating a `Candidates` boundary with one of the functionalities, chosen one of the following options:
* `Reject`: Reject feature in candidates layer. Deletes feature and restarts delineation.
* `Accept`: Accept feature in candidates layer. Moves feature to final layer and restarts delineation.
    * **Note**: if `Update edits` is enabled before clicking `Accept`, `Simplified Segments` will be updated according to edits you made in `Candidates` (e.g. `Manual` edits)
* `Edit`: Edit feature in `Candidates` layer. Enables `Toggle Editing`.
    * `Toggle Editing` enables all [QGIS editing functionalites](https://docs.qgis.org/2.18/en/docs/user_manual/working_with_vector/editing_geometry_attributes.html) (e.g. add, move, delete vertices or lines)
***
To save the lines you added to `Final`, click:
* `Finish`: Finish boundary delineation. Removes `Candidates` layer and displays `Final` layer only.
   * **Note**: if `Polygonize final layer` is enabled, `Final` **lines** will be transformed to **polygons** and displayed as `Final Polygons`

***
***
## <a name="Get-help"></a>Get help
The help tab in the plugin provides links to:
* the  <a href="https://its4land.com/automate-it-wp5/">project website </a> and 
* a <a href="https://www.youtube.com/watch?v=GrDv8fW53Fs">YouToube manual </a> showing how to install and use the plugin
    <p> <img src="https://user-images.githubusercontent.com/28596024/60507426-6f86ac80-9cc8-11e9-9315-810eca7309e0.png" title="Help tab in BoundaryDelineation plugin" width="500">  
    
***
***
### General notes:
* Most of the explanations in this wiki are provided in message boxes in QGIS and tooltips in the plugin
    * tooltips are little text boxes that appear when you hover with the mouse over a plugin button.

***
***
### References:
* The plugin's source can be downloaded from the  [QGIS plugin repository](https://plugins.qgis.org/plugins/BoundaryDelineation/)
