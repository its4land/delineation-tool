"""
!/bin/python
-*- coding: utf-8 -*-
/*****************************************************************************
        begin                : 2018-05-23
        copyright            : (C) 2019 by Sophie Crommelinck, 
                                University of Twente
        email                : s.crommelinck@utwente.nl
        description          : This script calculates attributes per line 
                               segment by taking into account information from 
                               each line’s geometry as well as information 
                               from underlying raster data (RGB and DSM).
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
 This script calculates attributes per line segment by taking into account information from each line’s
 geometry as well as information from underlying raster data (RGB and DSM).

 The following attributes are calculated:
    ID, int:                unique number per line
    boundary, int:          value containing the line label
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
import os
import math
import json
import logging
from osgeo import ogr, gdal
from rasterstats import zonal_stats
from geojson import Feature, FeatureCollection

from BasicProcessing import BasicProcessing

class AttributeCalculation(BasicProcessing):

    LEFTSIDE = 1
    RIGHTSIDE = 0
    SIDES = {LEFTSIDE : 'Left', RIGHTSIDE : 'Right'}

    RED = 1
    GREEN = 2
    BLUE = 3
    RGB = {RED : 'red', GREEN : 'green', BLUE : 'blue'}

    ID_ATTRIB = 'ID'

    def __init__(self):
        super(AttributeCalculation, self).__init__()
        self._inputFileName = None
        self._inputDataSource = None
        self._inputLayer = None

    def _prepareLayer(self, fileName, driverName = None):
        if not fileName:
            fileName = self._configValue("SegmentShapeFile")
        self._inputFileName = self.getInputFilePath(fileName)
        self._inputDataSource, self._inputLayer = self._prepareInputLayer(self._inputFileName, driverName)
        return self._inputLayer

    ### Calculate Attributes 

    def calculateAttributes(self, fileName, driverName = None):
        if self._inputLayer is None and self._prepareLayer(fileName, driverName) is None:
            return False
        
        self._print("Starting Attribute Calculation of '{0}'...".format(self._inputLayer.GetName()), logging.INFO)

        layer = self._inputLayer
        self._prepareLayerFields(layer)
        
        calcFuncs = [AttributeCalculation._calcID, 
                     AttributeCalculation._calcVertices,
                     AttributeCalculation._calcLength,
                     AttributeCalculation._calcAzimuth, 
                     AttributeCalculation._calcSinuosity]

        self._print("Calculating Attributes ({0} features)...".format(layer.GetFeatureCount()), logging.INFO)
        self._calculateLayer(layer, calcFuncs)
        layer.SyncToDisk()
        self._print("Attributes calculated.", logging.INFO)
        return True

    def _prepareLayerFields(self, layer):
        # Delete all fields in attribute table
        #self._deleteAllFields(layer)

        # Add fields to attribute table
        self._createField(layer, AttributeCalculation.ID_ATTRIB, ogr.OFTInteger, 10, None)
        self._createField(layer, 'boundary', ogr.OFTReal, 10, 3)
        self._createField(layer, 'vertices', ogr.OFTInteger, 10, None)
        self._createField(layer, 'length', ogr.OFTReal, 10, 3)
        self._createField(layer, 'azimuth', ogr.OFTReal, 10, 3)
        self._createField(layer, 'sinuosity', ogr.OFTReal, 10, 3)
        self._createField(layer, 'red_grad', ogr.OFTReal, 10, 3)
        self._createField(layer, 'green_grad', ogr.OFTReal, 10, 3)
        self._createField(layer, 'blue_grad', ogr.OFTReal, 10, 3)
        self._createField(layer, 'dsm_grad', ogr.OFTReal, 10, 3)

    @staticmethod
    def _calcID(index, feature, geometry):
        feature.SetField(AttributeCalculation.ID_ATTRIB, index + 1)

    @staticmethod
    def _calcVertices(index, feature, geometry):
        feature.SetField('vertices', geometry.GetPointCount())

    @staticmethod
    def _calcLength(index, feature, geometry):
        feature.SetField('length', geometry.Length())

    @staticmethod
    def _getAzimuth(pointA, pointB):
        """
        Calculates the bearing in degrees between two points.
        The formulae used is the following:
            θ = atan2(sin(Δlong).cos(lat2)cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
        :Source:
          https://gist.github.com/jeromer/2005586
        :Alternatives:
            https://pypi.org/project/fionautil/
            http://www.gaia-gis.it/gaia-sins/spatialite-sql-latest.html#p14b
        """
        if (type(pointA) != tuple) or (type(pointB) != tuple):
            raise TypeError('Only tuples are supported as arguments for azimuth calculation')
        lat1 = math.radians(pointA[0])
        lat2 = math.radians(pointB[0])
        diffLong = math.radians(pointB[1] - pointA[1])
        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))
        initial_bearing = math.atan2(x, y)
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
        return compass_bearing

    @staticmethod
    def _calcAzimuth(index, feature, geometry):
        startPoint = geometry.GetPoint(0)
        endPoint = geometry.GetPoint(geometry.GetPointCount() - 1)
        feature.SetField('azimuth', AttributeCalculation._getAzimuth(startPoint, endPoint))

    @staticmethod
    def _calcSinuosity(index, feature, geometry):
        """
        Calculates the sinuosity of a line. Sinuosity is the total line length divided by the shortest distance
        between the start of the line and the end of the line.
        The formulae used is the following:
            Length / Sqrt((firstPoint.X - Shape.lastPoint.X) ^ 2 + (firstPoint.Y - lastPoint.Y) ^ 2)
        :Source:
          https://community.esri.com/thread/39734
        """
        startPoint = geometry.GetPoint(0)
        endPoint = geometry.GetPoint(geometry.GetPointCount() - 1)
        startPoint_geom = ogr.Geometry(ogr.wkbPoint)
        endPoint_geom = ogr.Geometry(ogr.wkbPoint)
        startPoint_geom.AddPoint(startPoint[0], startPoint[1])
        endPoint_geom.AddPoint(endPoint[0], endPoint[1])
        dist = startPoint_geom.Distance(endPoint_geom)
        if dist != 0:
            dist = geometry.Length() / dist
        feature.SetField('sinuosity', dist)

    ### Single Sided Buffer

    def createBuffers(self, fileName, driverName = None, inMemory = False, asShape = False, asFileName = True):
        if self._inputLayer is None and self._prepareLayer(fileName, driverName) is None:
            return None, None
        distance = self._configValue("BufferDistance")
        return self.createBuffer(distance, AttributeCalculation.LEFTSIDE, fileName, driverName, inMemory=inMemory, asShape=asShape, asFileName=asFileName), \
            self.createBuffer(distance, AttributeCalculation.RIGHTSIDE, fileName, driverName, inMemory=inMemory, asShape=asShape, asFileName=asFileName)

    def createBuffer(self, bufferDistance, side, fileName, driverName = None, inMemory = False, asShape = False, asFileName = True):
        if self._inputLayer is None or self._prepareLayer(fileName, driverName) is None:
            return None
        fileName = '{0}_buffer{1}'.format(self._inputLayer.GetName(), AttributeCalculation.SIDES[side])
        if inMemory:
            driverName = BasicProcessing.DRIVER_MEM
            asFileName = False
        elif asShape:
            driverName = BasicProcessing.DRIVER_SHP
            fileName = self.getTempFilePath('{0}.shp'.format(fileName))
        else:
            driverName = BasicProcessing.DRIVER_JSON
            fileName = self.getTempFilePath('{0}.json'.format(fileName))
        
        bufferExists = False
        bufferLayer = None
        bufferDatasource = None
        if not inMemory and os.path.isfile(fileName):
            bufferExists = True
        if bufferExists:
            self._print("SingleSided Buffer at Distance {0} on {1} Side already exists.". format(
                bufferDistance, AttributeCalculation.SIDES[side]), logging.INFO)
            if not asFileName:
                bufferDatasource, bufferLayer = self._openVectorLayer(fileName, driverName)
        else:
            bufferDatasource = self._createDataSource(fileName, driverName)
            if bufferDatasource is not None:
                bufferLayer = self._createSingleSidedBufferLayer(bufferDatasource, bufferDistance, side, not asShape) #inMemory)
        if asFileName:
            self._closeDataSource(bufferDatasource)
            return fileName
        return self._features2Json(bufferLayer)

    def _createSingleSidedBufferLayer(self, bufferDataSource, distance, side, asJson):
        self._print("Creating SingleSided Buffer at Distance {0} on {1} Side...". format(distance, AttributeCalculation.SIDES[side]), logging.INFO)
        try:
            total = self._inputLayer.GetFeatureCount()
            sql = "select ID, ST_SingleSidedBuffer(geometry, %.2f , %i) from %s" % (distance, side, self._inputLayer.GetName())
            resultLayer = self._inputDataSource.ExecuteSQL(sql, dialect='SQLite')
            bufferLayer = bufferDataSource.CreateLayer('bufferLayer{0}'.format(AttributeCalculation.SIDES[side]), self._inputLayer.GetSpatialRef())
            self._createField(bufferLayer, AttributeCalculation.ID_ATTRIB, ogr.OFTInteger, 10, None)
        
            processed = 0
            for feature in resultLayer:
                if feature.GetGeometryRef() is not None:
                    bufferLayer.CreateFeature(feature.Clone())
                    processed += 1
            bufferLayer.SyncToDisk()
            return bufferLayer
        except Exception as e:
            self._print("Error: {0}".format(str(e)), logging.ERROR)
            processed = 0
            return None
        finally:
            self._inputLayer.ResetReading()
            self._print("SingleSided Buffer created. {0} features processed, {1} failed.".format(total, total - processed), logging.INFO)
    
    ### Zonal Stats
    
    def calculateZonalStats (self, rasterFileRGB, rasterFileDSM, leftBufferlayer = None, rightBufferlayer = None):
        if self._inputLayer is None and self._prepareLayer(fileName, driverName) is None:
            return False
        layer = self._inputLayer

        # Create buffer layers
        distance = self._configValue("BufferDistance")
        if leftBufferlayer is None:
            leftBufferlayer = self.createBuffer(distance, AttributeCalculation.LEFTSIDE)
        if rightBufferlayer is None:
            rightBufferlayer = self.createBuffer(distance, AttributeCalculation.RIGHTSIDE)

        statsMesaure = self._configValue("StatsMeasure")
        # RGB
        if not rasterFileRGB:
            rasterFileRGB = self._configValue("RGB_RasterFile")
        fileName = self.getInputFilePath(rasterFileRGB)
        if os.path.isfile(fileName):
            self._calculateZonalStats (layer, leftBufferlayer, rightBufferlayer, fileName, 
                                       'red_grad', AttributeCalculation.RED, statsMesaure)
            self._calculateZonalStats (layer, leftBufferlayer, rightBufferlayer, fileName, 
                                        'green_grad', AttributeCalculation.GREEN, statsMesaure)
            self._calculateZonalStats (layer, leftBufferlayer, rightBufferlayer, fileName, 
                                        'blue_grad', AttributeCalculation.BLUE, statsMesaure)
        else:
            self._print("Raster file {0} does not exist!".format(fileName), logging.ERROR)

        # DSM
        if not rasterFileDSM:
            rasterFileDSM = self._configValue("DSM_RasterFile")
        fileName = self.getInputFilePath(rasterFileDSM)
        if os.path.isfile(fileName):
            self._calculateZonalStats (layer, leftBufferlayer, rightBufferlayer, fileName, 
                                        'dsm_grad', 1, statsMesaure)
        else:
            self._print("Raster file '{0}' does not exist!".format(fileName), logging.ERROR)

        layer.SyncToDisk()
        return True

    def _calculateZonalStats (self, layer, leftBufferlayer, rightBufferlayer, 
                              rasterFileName, attributeName, colorBand, statsMeasure):
        self._print("Calculating ZonalStats on raster '{0}' for attribute '{1}'...".format(os.path.basename(rasterFileName), attributeName), logging.INFO)
        try:
            leftStats = zonal_stats(leftBufferlayer, rasterFileName, band=colorBand, stats=statsMeasure, geojson_out=True, nodata=-999)
        except Exception as e:
            leftStats = []
            self._print("Error: {0}".format(str(e)), logging.ERROR)
        try:
            rightStats = zonal_stats(rightBufferlayer, rasterFileName, band=colorBand, stats=statsMeasure, geojson_out=True, nodata=-999)
        except Exception as e:
            rightStats = []
            self._print("Error: {0}".format(str(e)), logging.ERROR)

        if not leftStats or not rightStats:
            self._print("ZonalStats: No data received!", logging.ERROR)
            return False
        self._setZonalStatsField(layer, leftStats, rightStats, statsMeasure, attributeName)
        self._print("ZonalStats calculated.", logging.INFO)
        return True

    def _setZonalStatsField(self, layer, leftStats, rightStats, statsMeasure, attributeName):
        try:
            self._print("Populating field '{0}' with {1} values...".format(attributeName, len(leftStats)), logging.INFO)
            calculated = 0
            failed = 0 
            for i, feature in enumerate(layer):
                featID = feature.GetField(AttributeCalculation.ID_ATTRIB)
                for x in range(0, len(leftStats)):
                    leftProps = leftStats[x]['properties']
                    if leftProps.get(AttributeCalculation.ID_ATTRIB) == featID:
                        leftMeasure = leftProps.get(statsMeasure)
                        rightMeasure = rightStats[x]['properties'].get(statsMeasure)
                        value = None
                        if leftMeasure is not None and rightMeasure is not None:
                            value = abs(leftMeasure - rightMeasure)
                            calculated += 1
                        else:
                            failed += 1
                        feature.SetField(attributeName, value)
                        layer.SetFeature(feature)
                        del leftStats[x]
                        del rightStats[x]
                        break
            total = layer.GetFeatureCount()
            self._print("Field '%s' populated, %i of %i features have been attributed." % (attributeName, calculated, total), logging.INFO)
        except Exception as e:
            self._print("Error: {0}".format(str(e)), logging.ERROR)
        finally:
            layer.ResetReading()

    ### Run all processing functions

    def runAll(self, rasterFileRGB, rasterFileDSM, vectorFileName, driverName = None):
        try:
            self._print("*** Starting Attribute Calculation...", logging.INFO)

            if self._prepareLayer(vectorFileName) is None:
                return None
            self.calculateAttributes(None, None)

            # Create buffer layers
            leftBufferlayer, rightBufferlayer = self.createBuffers(None, None, inMemory = False, asShape = True, asFileName = True)

            # Zonal stats of RGB and DSM
            self.calculateZonalStats (rasterFileRGB, rasterFileDSM, leftBufferlayer, rightBufferlayer)

            self._print("*** Attribute Calculation finished.", logging.INFO)

            return self._inputFileName
        finally:
            self._closeAllDataSources()

