### Description:
Boundary classification refers to training a machine learning algorithm to predict boundary probabilities for lines obtained through image segmentation. Training data is required to train the classifier, which line represents a desired outline before it can predict boundary probabilities for unseen lines.

### Input:
* image segmentation **lines** without attributes `.shp`
* RGB orthoimage **raster** `.tif`
* DSM orthoimage **raster** `.tif` (optional)

### Output:
* image segmentation **lines** with boundary likelihood as attribute per line `.shp` 

### Steps:
The prediction can be realized through <a href="https://github.com/SCrommelinck/Delineation-Tool/wiki/2a)-Random-Forest-Classification">Random Forest</a> and  <a href="https://github.com/SCrommelinck/Delineation-Tool/wiki/2b)-Convolutional-Neural-Network-Classification">Convolutional Neural Network</a> classification.
