"""
!/bin/python
-*- coding: utf-8 -*-
/*****************************************************************************
        begin                : 2018-05-23
        copyright            : (C) 2019 by Sophie Crommelinck, 
                                University of Twente
        email                : s.crommelinck@utwente.nl
        description          : this script applies Random Forest 
                               classification on a line vector shapefile with
                               certain attributes to predict a boundary 
                               probability per line.
        funding              : H2020 EU project its4land 
                                (#687826, its4land.com)
                                Work package 5: Automate It
		      development          : Reiner Borchert, Hansa Luftbild AG Münster
        email                : borchert@hansaluftbild.de
 *****************************************************************************/
 
 /*****************************************************************************
 *    This program is free software: you can redistribute it and/or modify    *
 *    it under the terms of the GNU General Public License as published by    *
 *    the Free Software Foundation, either version 3 of the License, or       *
 *    (at your option) any later version.                                     *
 *                                                                            *
 *    This program is distributed in the hope that it will be useful,         *
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           *
 *    GNU General Public License for more details.                            *
 *                                                                            *
 *    You should have received a copy of the GNU General Public License       *
 *    along with this program.  If not, see <https://www.gnu.org/licenses/>.  *
  *****************************************************************************/
"""

"""
### Description ###
 This script applies Random Forest classification on a line vector shapefile with certain attributes to predict a
 boundary probability per line.
 A line vector shapefile for training (for which the boundary attribute is defined)
 and validation (for which the boundary attribute will be predicted) should be provided.

  The following attributes should be part of the attribute tables of the training and validation shapefiles:
    ID, int:                unique number per line
    boundary, int:          value containing the line label (empty for validation data)
    vertices, int           number of vertices per line
    length [m], float:      length per line
    azimuth [°], float:     bearing in degrees between start and end of each line
    sinuosity, float:       total line length divided by the shortest distance between start and end of each line
    red_grad, float:        absolute difference between median of all red values of RGB lying within a 0.4m buffer right
                            and left of each line
    green_grad, float:      same as red_grad for green of RGB
    blue_grad, float:       same as red_grad for blue of RGB
    dsm_grad, float:        same as red_grad for DSM
"""

# Import required modules
import numpy as np
import os
import logging
from osgeo import ogr, gdal
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib

from BasicProcessing import BasicProcessing
from RestAPI import RestAPI

class Classification(BasicProcessing):

    IDLABEL = 'ID'
    LENGTHLABEL = 'length'
    BOUNDARYLABEL = 'boundary'
    ATTRIBUTES = ['vertices', 'length', 'azimuth', 'sinuosity', 'red_grad', 'green_grad', 'blue_grad', 'dsm_grad']

    def __init__(self):
        super(Classification, self).__init__()

    ### Training

    def createClassifier(self, fileName, driverName = None, saveFile=True):
        if not fileName:
            fileName = self._configValue("TrainingLayer");
        datasource, layer = self._prepareInputLayer(fileName, driverName)
        if layer is not None:
            self._print("Create classifier from training data '{0}'...".format(fileName), logging.INFO)
        
            trainingAttributes, trainingLabels = self._loadFields(datasource, layer, Classification.BOUNDARYLABEL, Classification.ATTRIBUTES)
            classifier = self._createClassifier(trainingAttributes, trainingLabels)
            if saveFile:
                return self._saveClassifier(classifier, None)
            else:
                return classifier
        return None

    def _loadFields(self, datasource, layer, labelName, attributeList):
        self._print("Load field data from '{0}'...".format(layer.GetName()), logging.INFO)
        try:

            # Copy datasource to memory, otherwise some fields in layer are set to None
            driver = self._getMemoryDriver()
            sqlDatasource = driver.CopyDataSource(datasource, 'sqlDatasource')

            # Create arrays to store attribute table values
            numberAttributes = len(attributeList)
            numberSamples = layer.GetFeatureCount()
            attributes = np.zeros([numberSamples, numberAttributes])
            labels = np.zeros([numberSamples, 1])

            # Get labels
            sql = 'SELECT %s FROM %s' % (labelName, layer.GetName())
            sqlLayer = sqlDatasource.ExecuteSQL(sql)
            for i, feature in enumerate(sqlLayer):
                labels[i] = feature.GetField(labelName)
        
            # Get attributes
            sql = 'SELECT %s FROM %s' % (', '.join(attributeList), layer.GetName())
            sqlLayer = sqlDatasource.ExecuteSQL(sql)
            for i, feature in enumerate(sqlLayer):
                for j in range(0, len(attributeList)):
                    attributes[i][j] = feature.GetField(attributeList[j])

            # Replace no data values
            NaNs = np.isnan(attributes)
            attributes[NaNs] = -1

            self._print("{0} field data samples loaded.".format(numberSamples), logging.INFO)
            return attributes, labels
        finally:
            sqlDatasource.Release()
            layer.ResetReading()

    def _createClassifier(self, trainingAttributes, trainingLabels):
        self._print("Creating Classifier Model...", logging.INFO)
        classifierModel = RandomForestClassifier(n_estimators=100, n_jobs=-1)
        classifierModel.fit(trainingAttributes, trainingLabels[:, 0])
        self._print("Classifier Model created.", logging.INFO)
        return classifierModel

    def _saveClassifier(self, classifier, name):
        if classifier is not None:
            if RestAPI.serverConnected():
                name = RestAPI.saveContentItem(classifier)
                if RestAPI.saveClassifier(name):
                    return name
                return None
            if not name:
                name = self._configValue("ClassifierFileName")
            self._print("Saving Classifier Model in file '{0}'...".format(name), logging.INFO)
            name = self.getOutputFilePath(name)
            joblib.dump(classifier, name)
            return name
        self._print("No classifier to save!", logging.ERROR)
        return None

    ### Validate

    def applyClassifier(self, classifierName, fileName, driverName = None, classifier = None):
        if not fileName:
            fileName = self._configValue("ValidationLayer");
        fileName = self.getInputFilePath(fileName)
        datasource, layer = self._prepareInputLayer(fileName, driverName)
        if layer is not None:
            self._print("Classification for '{0}'...".format(layer.GetName()), logging.INFO)
        
            validationAttributes, validationLabels = self._loadFields(datasource, layer, Classification.IDLABEL, Classification.ATTRIBUTES)
            if classifier is None:
                if not classifierName:
                    classifierName = self._configValue("ClassifierFileName")
                classifier = self._loadClassifier(classifierName)
            if classifier is not None:
                predictedLabels = self._predictLabels(classifier, validationAttributes)
                self._updateFeatureAttributes(predictedLabels, validationLabels, layer, Classification.IDLABEL, Classification.BOUNDARYLABEL, Classification.LENGTHLABEL)
                self._print("Layer classified.", logging.INFO)
                return fileName
            self._print("No classifier loaded!", logging.ERROR)
        return None

    def _loadClassifier(self, name):
        if RestAPI.serverConnected():
            return RestAPI.loadClassifier(name)
        name = self.getInputFilePath(name)
        if os.path.isfile(name):
            self._print("Load classifier from '{0}'...".format(name), logging.INFO)
            return joblib.load(name)
        self._print("Could not load classifier from '{0}'!".format(name), logging.ERROR)
        return None

    def _predictLabels(self, classifier, validationAttributes):
        self._print("Calculate prediction data...", logging.INFO)
        return classifier.predict_proba(validationAttributes)[:, 0]

    def _updateFeatureAttributes(self, predictedLabels, validationLabels, layer, IDLabel, boundaryLabel, lengthLabel):
        self._print("Updating attributes of {0} features...".format(layer.GetFeatureCount()), logging.INFO)
        for feature in layer:
            featureID = feature.GetField(IDLabel)
            featureLength = float(feature.GetField(lengthLabel))
            bndFieldIndex = feature.GetFieldIndex(boundaryLabel)
            for i in range(0, len(predictedLabels)):
                # Match feature and according boundary probability via ID
                if int(validationLabels[i]) == featureID:
                    # Scale boundary probability by line length (probability * length)
                    feature.SetField(bndFieldIndex, float(predictedLabels[i]) * featureLength)
                    break
            layer.SetFeature(feature)
        layer.ResetReading()
        layer.SyncToDisk()
        self._print("Feature attributes updated.", logging.INFO)
        
    ### Run all processing functions

    def runAll(self):
        try:
            self._print("*** Starting Classification...", logging.INFO)

            classifier = self.createClassifier(None, None, saveFile=False) 
            self.applyClassifier(None, None, None, classifier)

            self._print("*** Classification finished.", logging.INFO)

            return True
        finally:
            self._closeAllDataSources()

