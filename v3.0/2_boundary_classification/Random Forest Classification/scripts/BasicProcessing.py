# -*- coding: utf-8 -*-
"""
/***************************************************************************
 its4land WP5: Automate It
                              -------------------
        begin                : 2018-05-23
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Sophie Crommelinck, University of Twente
        email                : s.crommelinck@utwente.nl
        development          : Reiner Borchert, Hansa Luftbild AG Münster
        email                : borchert@hansaluftbild.de
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

"""
!/bin/python
-*- coding: utf-8 -*

### Author ###
 S. Crommelinck, Reiner Borchert, 2018

### Description ###
 abstract base class for processing
"""

from osgeo import ogr, gdal
from sqlalchemy import MetaData, Table, Column, create_engine, select, update, insert
from geoalchemy2.functions import ST_AsGeoJSON
import os
from datetime import *
import logging
import uuid
import json
from geojson import Feature, FeatureCollection, GeometryCollection
from RequestController import RequestController
from RestAPI import RestAPI

STD_SRID = 4326
STD_GEOMENCODING = 'GeoJSON'

# Enable GDAL error handling
gdal.UseExceptions()

class BasicProcessing():
    
    CONFIG_FILENAME = '../share/config/config.json'
    
    DRIVER_SHP = 'ESRI Shapefile'
    DRIVER_JSON = 'GeoJSON'
    DRIVER_MEM = 'MEMORY'

    def __init__(self):
        self._basePath = os.path.split(__file__)[0]
        configFile = os.path.join(self._basePath, BasicProcessing.CONFIG_FILENAME)
        self._configuration = json.load(open(configFile))
        RestAPI.setServerURL(self._configValue("ServerURL"))
        self._inputDataPath = self._configValue("InputDataPath")
        self._tempDataPath = self._configValue("TempDataPath")
        self._outputDataPath = self._configValue("OutputDataPath")
        self._dataSources = []
        self._isLogging = False
        self._showConsoleLogging = self._configValue("ShowConsoleLogging") > 0
        self.startLogging(self.getTempFilePath(self._configValue("LogfileName")))
        RequestController.connectNotification(self._errorMessage)
        #Request._logResponseError ("url", "code", "msg")
        #RestAPI.loadClassifier("jolla")
        
    def __del__(self):
        self.stopLogging()

    def _configValue(self, key):
       try:
           return self._configuration[key]
       except:
           self._print("Config Key {0} could not be found!".format(key), logging.ERROR)
           return None

    def applicationName(self):
        return self.__class__.__name__

    def getInputFilePath(self, fileName):
        if not fileName:
            return None
        if os.path.isabs(fileName):
            return fileName
        return os.path.join(self._basePath, self._inputDataPath, fileName)

    def getTempFilePath(self, fileName):
        if not fileName:
            return None
        if os.path.isabs(fileName):
            return fileName
        path = os.path.join(self._basePath, self._tempDataPath)
        if not os.path.exists(path):
            os.mkdir(path)
        return os.path.join(path, fileName)

    def getOutputFilePath(self, fileName):
        if not fileName:
            return None
        if os.path.isabs(fileName):
            return fileName
        path = os.path.join(self._basePath, self._outputDataPath)
        if not os.path.exists(path):
            os.mkdir(path)
        return os.path.join(path, fileName)

    def startLogging(self, fileName, level=logging.DEBUG):
        self.stopLogging()
        if fileName:
            handler = logging.FileHandler(fileName)
            if handler is not None:
                handler.setLevel(level)
                handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
                log = logging.root
                log.addHandler(handler)
                log.setLevel(level)
                self._isLogging = True
                self._print('*** Start Logging for "{0}" ***'.format(self.applicationName()), logging.INFO)
    
    def stopLogging(self):
        if self._isLogging:
            RequestController.connectNotification(None)
            self._print('*** Stop Logging for "{0}" ***'.format(self.applicationName()), logging.INFO)
            self._isLogging = False
            log = logging.root
            for hdlr in log.handlers[:]:
                log.removeHandler(hdlr)

    def _print (self, message, level=logging.DEBUG):
        if self._showConsoleLogging:
            print("{0} - {1}".format(datetime.now(), message))
        if self._isLogging:
            try:
                logging.log(level, message)
            except:
                pass

    def _errorMessage(self, title, message, exception = None):
        self._print(message, level=logging.ERROR)

    def runAll(self):
        pass

    @staticmethod
    def _getDriver(name):
        if name:
            return ogr.GetDriverByName(name)
        return None

    @staticmethod
    def _getShapeDriver():
        return BasicProcessing._getDriver(BasicProcessing.DRIVER_SHP)

    @staticmethod
    def _getMemoryDriver():  
        return BasicProcessing._getDriver(BasicProcessing.DRIVER_MEM)

    @staticmethod
    def _getJsonDriver():
        return BasicProcessing._getDriver(BasicProcessing.DRIVER_JSON)

    def _registerDataSource(self, datasource):
        if datasource is not None:
            self._dataSources.append(datasource)
        return datasource

    def _createDataSource(self, name, driver):
        if not isinstance(driver, ogr.Driver):
            driver = BasicProcessing._getDriver(driver)
        if driver is not None:
            return self._registerDataSource(driver.CreateDataSource(name))
        return None

    def _openDataSource(self, fileName, driverName, createNew=False):
        if not driverName and fileName:
            base, ext = os.path.splitext(fileName)
            if ext.lower() == ".shp":
                driverName = BasicProcessing.DRIVER_SHP
            else:
                driverName = BasicProcessing.DRIVER_JSON
        if os.path.isfile(fileName):
            dsource = BasicProcessing._getDriver(driverName).Open(fileName, 1)
            if dsource is None:
                self._print('Unable to open {0}!'.format(fileName), logging.ERROR)
            return self._registerDataSource(dsource)
        if createNew:
            return self._createDataSource(fileName, driverName)
        elif fileName:
            self._print('File {0} does not exit!'.format(fileName), logging.ERROR)
        return None

    def _closeDataSource(self, datasource):
        if datasource is not None:
            self._dataSources.remove(datasource)
            # datasource.Release() ---deprecated---
        return datasource

    def _closeAllDataSources(self):
        if self._dataSources is not None:
            try:
                pass
                #for ds in self._dataSources:
                    # ds.Release() ---deprecated---
            finally:
                self._dataSources = []

    def _openRasterLayer(self, fileName):
        if os.path.isfile(fileName):
            layer = gdal.Open(fileName)
            if layer is None:
                self._print('Unable to open {0}!'.format(fileName), logging.ERROR)
            return layer
        if fileName:
            self._print('File {0} does not exit!'.format(fileName), logging.ERROR)
        return None

    def _openVectorLayer(self, fileName, driverName, createNew=False):
        dataSource = self._openDataSource(fileName, driverName, createNew)
        if dataSource is not None:
            return dataSource, dataSource.GetLayer()
        return None, None

    def _prepareInputLayer(self, fileName, driverName):
        if fileName:
            fileName = self.getInputFilePath(fileName)
        datasource, layer = self._openVectorLayer(fileName, driverName, createNew=False)
        if layer is None:
            self._print("No layer in {0} assigned!".format(fileName), logging.ERROR)
            datasource = None
        return datasource, layer
    
    def _deleteAllFields(self, layer):
        layerDefn = layer.GetLayerDefn()
        for i, field in enumerate(range(layerDefn.GetFieldCount() - 1, -1, -1), start=1):
            layer.DeleteField(field)

    def _createField(self, layer, fieldName, fieldType, fieldWidth, fieldPrecision):
        if layer is None:
            index = -1
        else:
            index = layer.FindFieldIndex(fieldName, False)
        if index < 0:
            field = ogr.FieldDefn(fieldName, fieldType)
            if fieldWidth:
                field.SetWidth(fieldWidth)
            if fieldPrecision:
                field.SetPrecision(fieldPrecision)
            if layer is None:
                return field
            return layer.CreateField(field)
        layerDef = layer.GetLayerDefn()
        return layerDef.GetFieldDefn(index)

    def _calculateLayer(self, layer, calcFuncs):
        if layer is not None:
            try:
                i = 0
                for feature in layer:
                    geometry = feature.GetGeometryRef()
                    for func in calcFuncs:
                        func(i, feature, geometry)
                    layer.SetFeature(feature)
                    i += 1 
            except Exception as e:
                self._print("Error: {0}".format(str(e)), logging.ERROR)
            finally:
                layer.ResetReading()

    def _features2Json (self, layer):
        if layer is not None:
            if isinstance(layer, FeatureCollection):
                return layer
            try:
                self._print("Converting {0} features of layer '{1}' to GeoJson format...".format(layer.GetFeatureCount(), layer.GetName()), logging.INFO)
                jsonFeats = []
                for feature in layer:
                    jfeat = json.loads(feature.ExportToJson())
                    if jfeat.get('geometry') is not None:
                        jsonFeats.append(jfeat)
                return FeatureCollection(jsonFeats)
            except Exception as e:
                self._print("Error: {0}".format(str(e)), logging.ERROR)
            finally:
                layer.ResetReading()
                self._print("{0} features converted.".format(len(jsonFeats)), logging.INFO)
        return None
    
    


    
