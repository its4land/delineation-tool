### Description:
A set of features is calculated per line capturing its geometry and its spatial context. [Table 1](#Table1) shows all features being calculated, of which the first two are not used for the classification. Together with a boundary label, the features  are used to train a Random Forest (RF) classifier. The boundary label refers to a line being a _boundary_ (**1**) or _not boundary_ (**0**). This label is assigned manually or  derived from reference data. The trained classifier predicts boundary likelihoods for unseen testing data without a boundary label ([Figure 1](#Figure1)). The classification is based on the open-source [Scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html) RF implementation.

<p align="center">
  <img src="https://user-images.githubusercontent.com/28596024/59846890-534a4d80-9361-11e9-8102-cb30fd12c06c.PNG" title="Features calculated per line used by the Random Forest (RF) classifier for boundary classification." width="600">

<p align="center">
<a name="Table1"><font size="1">Table 1:</a> Features calculated per line used by the Random Forest (RF) classifier for boundary classification.</font>

<p align="center">
<img src="https://user-images.githubusercontent.com/28596024/59845182-0bc1c280-935d-11e9-9b29-39a06f714cd4.png"   title="Boundary line classification based on Random Forest (RF) to derive boundary likelihoods for MCG lines." width="500">

<p align="center">
<a name="Figure1"><font size="1">Figure 1:</a> Boundary line classification based on Random Forest (RF) to derive boundary likelihoods for MCG lines.
</p>

### Input:
* image segmentation **lines** without attributes (`.shp`)
* cadastral reference **lines** (`.shp`) (optional)
* RGB orthoimage **raster** (`.tif`)
* DSM orthoimage **raster** (`.tif`) (optional)

### Output:
* image segmentation **lines** with boundary likelihood as attribute (`.shp`) 

### Steps:
1. [**Label lines**](#Label-lines)
2. [**Calculate attributes**](#Calculate-attributes)
3. [**Train classifier**](#Train-classifier)
4. [**Predict boundary likelihoods**](#Predict-boundary-likelihood)
* [**General notes**](#General-notes)
* [**References**](#References)

See below for details on each step.
***
***
## <a name="Label-lines"></a>1. Label lines
### Goal:
To assign a value of **0** or **1** for each line as _boundary_ attribute in the training data. 
* _boundary_ = **1** : line is useful for boundary delineation
* _boundary_ = **0**: lines is not useful for boundary delineation

The _boundary_ value can be assigned either 
* [**manually**](#manually) by selecting lines and setting their value accordingly or 
* [**semi-automatically**](#semi-automatically) by comparing the overlap of the image segmentation lines with cadastral reference lines

### Input:
* image segmentation **lines** without _boundary_ label (`.shp`)
* cadastral reference **lines** (`.shp`) (optional)

### Output:
* image segmentation **lines** with _boundary_ label (`.shp`)

### Steps:
<a name="manually">**Manual line labelling**</a>    
* Create the _boundary_ attribute for your input lines. `Open Attribute Table` | `New Field`
    <p> <img src="https://user-images.githubusercontent.com/28596024/60023092-63ca3300-9695-11e9-8cf6-3c76821a3645.png" title="Add boundary attribute" width="200">

* Select lines to be labelled with _boundary_= **1** by clicking on features while pressing _Ctrl_
    <p> <img src="https://user-images.githubusercontent.com/28596024/60018416-95d69780-968b-11e9-989c-58867da7fd63.png"   title="Select features" width="500">

* `Open Attribute Table` | `Toggle editing mode` | set _boundary_ = 1 for all selected features with `Update Selected`
    <p> <img src="https://user-images.githubusercontent.com/28596024/60018682-42b11480-968c-11e9-82a7-b26a67137c0d.png" title="Set boundary value for selected features" width="500">

* `Save edits` | `Toggle editing mode` 
***
<a name="semi-automatically">**Semi-automatic line labelling (part 1/2)**</a>
<br>**Note:** This requires cadastral reference data. An additional attribute ([bound_ref](#bound_ref)) is calculated that captures the overlap between each line and the buffered cadastral reference.
* Buffer the cadastral reference by a radius distance of e.g. 0.4m
    <p> <img src="https://user-images.githubusercontent.com/28596024/60020348-26af7200-9690-11e9-9960-229dd342bc9c.png" title="Buffer cadastral reference" width="500">

    <p> <img src="https://user-images.githubusercontent.com/28596024/60021290-0a143980-9692-11e9-9052-832208b7edac.png" title="Buffer cadastral reference" width="500">

* Convert the cadastral reference data to a raster format. The raster should have the value 1 at locations of the cadastral reference buffer. Make sure that the resolution (pixel size) of your output raster is smaller than the buffer size you have chosen.
    <p> <img src="https://user-images.githubusercontent.com/28596024/60020654-b8b77a80-9690-11e9-859c-8c6b493f8d8f.png" title="Convert vector to raster" width="500">

    <p> <img src="https://user-images.githubusercontent.com/28596024/60021374-316b0680-9692-11e9-9098-af58160a6b4e.png" title="Convert vector to raster" width="500">

* Save the raster to `\share\input`
    <p> <img src="https://user-images.githubusercontent.com/28596024/60021040-7cd0e500-9691-11e9-884c-8ba88322b1e5.png" width="200">

* Set `"Ref_RasterFile"` in `config\config.json` to the name of your raster file
    <p> <img src="https://user-images.githubusercontent.com/28596024/60022561-5c565a00-9694-11e9-84e6-50de24afa9ac.png" width="500">
    
* Continue with [**2. Calculate attributes**](#Calculate-attributes) and label lines [thereafter](#Continuation)

***
***
## <a name="Calculate-attributes"></a>2. Calculate attributes
### Goal:
To calculate features required to train the classifier and to save them as attributes for the image segmentation lines.
### Input:
* image segmentation **lines** without attributes (`.shp`)
* RGB orthoimage **raster** (`.tif`)
* DSM orthoimage **raster** (`.tif`) (optional)

### Output:
* image segmentation **lines** with attributes (`.shp`) 

### Steps:
* Download all folders from [GitHub](https://github.com/SCrommelinck/Delineation-Tool/tree/master/v3.0/2_boundary_classification/Random%20Forest%20Classification)
    <p> <img src='https://user-images.githubusercontent.com/28596024/60014975-8dc62a00-9682-11e9-9fc4-e22f6e03050c.png'  title="Downloaded folders" width="200"/>

* Save your input data to `\share\input`
    <p> <img src="https://user-images.githubusercontent.com/28596024/60016263-fe227a80-9685-11e9-9f5a-f7a02b0841ac.png"   title="Saved input data" width="200">

* Set the following parameters in `config\config.json` according to your input data file names :
    * `"SegmentShapeFile"`: name of your image segmentation **lines** without attributes (`.shp`)
    * `"RGB_RasterFile"`: name of your RGB orthoimage **raster** (`.tif`)
    * `"DSM_RasterFile"`: name of your DSM orthoimage **raster** (`.tif`) (optional)
        <p> <img src="https://user-images.githubusercontent.com/28596024/60023240-b60b5400-9695-11e9-8e08-b460289d7a6c.png"   title="config.json" width="700">


* open _Command Prompt_
    * Select the Windows start button > type `cmd`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60076237-565d8900-9727-11e9-852f-c7527c6d3e3d.png"   title="Command Prompt" width="700">

* change the command promt's working directory to `\scripts`
    * copy the path to the `\scripts` folder
    * `cd path_to_folder\scripts`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60076292-78efa200-9727-11e9-9e87-196d79013f2f.png"   title="Change working directory" width="700">

* start `main.py` with [Python](https://www.python.org/)
    * `python main.py`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60076319-8efd6280-9727-11e9-90db-538c49aa73b0.png"   title="python main.py" width="700">

* start `test` modus
    * `--test`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60076366-a9374080-9727-11e9-9f7a-ff173ce69177.png"   title="--test" width="700">

* calculate attributes
    * `-a`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60076606-44c8b100-9728-11e9-9d6e-5ddf8628df6b.png"   title="-a" width="700">

If you now open the input shapefile  (`.shp`) you saved to `\share\input` in a GIS and check out the attribute table, each line should have new attributes.
        <p> <img src="https://user-images.githubusercontent.com/28596024/60084842-8feac000-9738-11e9-99be-3a317ca1332b.png"   title="Calculated attributes" width="700">

Attribute description:
* _ID - dsm_grad_: see [Table 1](#Table1) 
* _cad_sum_: sum of cadastral reference pixels being within buffer around line
* _cad_count_: sum of pixels being within buffer around line
* <a name="bound_ref"></a>_bound_ref_: value between **0** and **1** showing overlap between line's buffer and cadastral reference buffer (_cad_sum_ divided by _bound_ref_):
    * _bound_ref_ = **0** : no overlap between line and cadastral reference buffer
    * _bound_ref_ = **1** : 100% overlap between line and cadastral reference buffer
***
<a name="Continuation">**Semi-automatic line labelling (part 2/2):**</a>

* Set the _boundary_ value for all lines having _bound_ref_ > **0.5** to **1**
<br>`Open Attribute Table` | `Toggle editing mode` | `Select features using an expression`| `"bound_ref">0.5` | `Select Features`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60087880-19e95780-973e-11e9-96aa-d4225e525519.png" title="Set boundary attribute" width="500">

* Set _boundary_ = 1 for all selected features with `Update Selected`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60088140-83696600-973e-11e9-8aa8-cc4c613110f2.png" title="Set boundary attribute" width="500">     

* `Invert selection` and Set _boundary_ = 0 for all selected features with `Update Selected`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60102888-db17c980-975e-11e9-98fe-4d2493fd69ac.png" title="Invert selection" width="500"> 
        
* `Save edits` | `Toggle editing mode`     

***
***

## <a name="Train-classifier"></a>3. Train classifier
### Goal:
To create a classifier model based on training data to be applied later on testing data.

### Input:
* image segmentation **lines** with attributes and _boundary_ label (`.shp`) 
### Output:
* trained classifier model (`.pkl`)
### Steps:
* Set `"TrainingLayer"` in `config\config.json` to the name of your training lines
        <p> <img src="https://user-images.githubusercontent.com/28596024/60102417-f0d8bf00-975d-11e9-9482-90c38b21040b.png" title="config.json" width="500">    

* Create classifier
    * `-c`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60103404-d7387700-975f-11e9-9c49-d1f4a98db7db.png" title="-c" width="500"> 
The classifier model `classifierModel.pkl` is now saved in `\share\output`
***
***

## <a name="Predict-boundary-likelihood"></a>4. Predict boundary likelihoods
### Goal:
To apply trained classifier on testing data in order to predict boundary likelihoods.

### Input:
* image segmentation **lines** with attributes and without _boundary_ label (`.shp`) 
### Output:
* image segmentation **lines** with attributes and with predicted _boundary_ label (`.shp`) 
### Steps:
* Copy `classifierModel.pkl` from `\share\output` to `\share\input`

* Set `"ValidationLayer"` in `config\config.json` to the name of your testing lines
        <p> <img src="https://user-images.githubusercontent.com/28596024/60103890-b1f83880-9760-11e9-94a7-1d6f8a450da6.png" title="config.json" width="500">  

* Predict boundary likelihoods
    * `-p`
        <p> <img src="https://user-images.githubusercontent.com/28596024/60104011-e66bf480-9760-11e9-9655-d7f39d67be29.png" title="-p" width="500">      
 
The _boundary_ attribute in your training data is now updated with a _boundary_ value between **0** and **1**. 
                <p> <img src="https://user-images.githubusercontent.com/28596024/60104142-2337eb80-9761-11e9-8aea-df82918c36fe.png" title="Updated boundary attribute" width="500"> 
    
***
***
### General notes:
* A log file containing information about the data processing is saved as `processing.txt` in `\share\temp`
* If not further specified, the term _lines_ refers to the _input segmentation lines_
* The created classifier can be reused and applied to more testing data. In that case, steps 1 and 3 are not needed.

***
***
### References:
* The GIS used for this wiki is the open source [QGIS](https://qgis.org).