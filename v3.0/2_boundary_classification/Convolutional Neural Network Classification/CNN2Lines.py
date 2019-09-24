# -*- coding: utf-8 -*-
"""
/***************************************************************************

                              -------------------
        begin                : 2019-03-25
        copyright            : (C) 2019 by Sophie Crommelinck, University of Twente
        email                : s.crommelinck@utwente.nl
        description          : this script takes probabilities of image tiles
                                averages them based on its ID value and writes
                                this value to the corresponding line feature.
        funding               H2020 EU project its4land (#687826, its4land.com)
                                Work package 5: Automate It
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import modules
import numpy as np
import os
from datetime import datetime
from osgeo import ogr
import sys

# Define input parameters
resultPath = r"/path_to_folder"
lineFile = r"/path_to_file"
ext = '.tif'                        # file type of input image tiles
predictionField = 'boundary'        # attribute field in shapefile to store predictions to
# Assumption: image files are saved as 'b1_19409_1_p_0.012.tif'

def load_predictions(path):
    print("%s: Reading input data..." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    # Array to store ID and probability of image tile
    ID = []
    Y = []
    imagefiles = os.listdir(path)

    # Iterate over all tiles in input directory
    for imagefile in imagefiles:
        if os.path.splitext(imagefile)[-1] == ext:
            # Get Y from values behind '_p_' to end of array without extension '.tif'
            indexP = imagefile.index('_p_')
            Y.append(imagefile[indexP+3:-4])

            # Get ID from values behind 'b0_' (3rd item) until second occurrence of '_'
            indexID = [i for i, x in enumerate(imagefile) if x == '_']
            ID.append(imagefile[3:indexID[1]])
        else:
            print("%s: Input folder contains a file or directory that cannot be read as input data." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

    # Calculate average of all probability values having the same feature ID
    IDpredict = []
    for indexList, id in enumerate(set(ID)):
        # Get index of Y values for ID value
        indexY = np.asarray([i for i, x in enumerate(ID) if x == id])
        # Get rounded mean of Y values
        # y = np.round(np.mean(np.asarray(Y)[indexY].astype(np.float)),3)
        f
        # Get 97th percentile of Y values (in accordance with ratio of b0 and b1 in reference)
        y = np.round(np.percentile(np.asarray(Y)[indexY].astype(np.float), 97), 3)
        # Write ID and y value to list
        IDpredict.append([int(id), y])
    print("%s: Input data read." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    return IDpredict

def predictions_to_lines(lineFile, IDpredict, predictionField):
    # Open shapefile in write mode
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(lineFile, 1)
    if datasource is None:
        print("%s: Input shapefile could not be opened." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        sys.exit(1)

    # Get layer
    layer = datasource.GetLayer()
    print("%s: Writing predictions to %i features for attribute '%s'..." %
          (datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
           layer.GetFeatureCount(),
           predictionField))

    # Iterate over features
    for feature in layer:
        # Get feature ID
        featID = feature.GetField("ID")
        # Get index of prediction corresponding to feature ID
        index = [(i, x.index(featID)) for i, x in enumerate(IDpredict) if featID in x]
        if index == []:
            pass
        else:
            # Get prediction value corresponding to feature ID
            y = IDpredict[index[0][0]][1]
            # Write prediction to feature
            feature.SetField(predictionField, y)
            layer.SetFeature(feature)
    print("%s: Predictions written as attribute to input shapefile." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

    # Clean-up
    layer.ResetReading()
    datasource.Destroy()


def main():
    # Get IDs and probabilities from input tiles
    IDpredict = load_predictions(resultPath)

    # Write probability to shapefile features
    predictions_to_lines(lineFile, IDpredict, predictionField)


if __name__ == "__main__":
    main()
