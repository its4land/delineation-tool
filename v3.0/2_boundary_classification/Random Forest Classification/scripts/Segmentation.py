"""
!/bin/python
-*- coding: utf-8 -*-
/*****************************************************************************
        begin                : 2018-05-23
        copyright            : (C) 2019 by Sophie Crommelinck, 
                                University of Twente
        email                : s.crommelinck@utwente.nl
        description          : module for executing an external segmentation 
                                tool, which creates superpixel areas from 
                                raster files.
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

# Import required modules
import os
import math
import json
import logging
from subprocess import call
from osgeo import ogr, gdal
from rasterstats import zonal_stats
from geojson import Feature, FeatureCollection

from BasicProcessing import BasicProcessing

class Segmentation(BasicProcessing):

    def __init__(self):
        super(Segmentation, self).__init__()
        self._inputDataSource = None
        self._inputLayer = None

    def createSegmentation (self, rasterFileName):
        if rasterFileName:
            self._print("Starting segmentation for raster '{0}'...".format(rasterFileName), logging.INFO)
            inputFileName = self.getInputFilePath(rasterFileName)
            outputFileName = self.getOutputFilePath(rasterFileName)
            if outputFileName:
                outputFileName += ".shp"
                command = self._configValue("SegmantationCommand").format(inputFileName, outputFileName)
                self._print("- command: {0}".format(command), logging.INFO)
                call(command)
                self._print("Segmentation finished.", logging.INFO)
                return outputFileName
        self._print("No files specified!", logging.ERROR)
        return None

    def createBoundaries(self, inputFileName, inMemory = False, asShape = True, asFileName = True):
        if not inputFileName:
            inputFileName = self._configValue("RawSegmentsShapeFile")
        if self._inputLayer is None and self._prepareLayer(inputFileName) is None:
            return None
        fileName = self._inputLayer.GetName() + '_boundaries'
        if inMemory:
            driverName = BasicProcessing.DRIVER_MEM
            asFileName = False
        elif asShape:
            driverName = BasicProcessing.DRIVER_SHP
            fileName = self.getOutputFilePath('{0}.shp'.format(fileName))
        else:
            driverName = BasicProcessing.DRIVER_JSON
            fileName = self.getOutputFilePath('{0}.json'.format(fileName))
        
        if not inMemory and os.path.isfile(fileName):
            os.remove(fileName)
        datasource, layer = self._openVectorLayer(fileName, driverName, createNew=True)
        if datasource is not None:
            layer = datasource.CreateLayer("boundaries", geom_type=ogr.wkbLineString)
            self._populateBoundariesLayer(datasource, layer)
        if asFileName:
            self._closeDataSource(datasource)
            return fileName
        return self._features2Json(layer)

    def _prepareLayer(self, fileName, driverName = None):
        self._inputDataSource, self._inputLayer = self._prepareInputLayer(fileName, driverName)
        return self._inputLayer

    def _populateBoundariesLayer(self, datasource, targetLayer):
        self._print("Creating Boundaries for '{0}'...".format(self._inputLayer.GetName()), logging.INFO)
        try:
            total = self._inputLayer.GetFeatureCount()
            processed = 0
            failed = 0

            idField = self._configValue("RawSegmentsIDField")
            tolAverageR = self._configValue("Tolerance_Average_R")
            tolAverageG = self._configValue("Tolerance_Average_G")
            tolAverageB = self._configValue("Tolerance_Average_B")
            tolStdDevR = self._configValue("Tolerance_StdDev_R")
            tolStdDevG = self._configValue("Tolerance_StdDev_G")
            tolStdDevB = self._configValue("Tolerance_StdDev_B")
            where = "and (abs(a.AVERAGE_1 - b.AVERAGE_1) > {0} or abs(a.AVERAGE_2 - b.AVERAGE_2) > {1} or abs(a.AVERAGE_3 - b.AVERAGE_3) > {2}".format(
                tolAverageR, tolAverageG, tolAverageB) \
                + " or abs(a.STDDEV_1 - b.STDDEV_1) > {0} or abs(a.STDDEV_2 - b.STDDEV_2) > {1} or abs(a.STDDEV_3 - b.STDDEV_3) > {2})".format(
                tolStdDevR, tolStdDevG, tolStdDevB)

            sql = "select " \
                + "a.{1} as ID_LEFT, a.AREA as AREA_LEFT, " \
                + "a.AVERAGE_1 as AVERAGE1_L, a.AVERAGE_2 as AVERAGE2_L, a.AVERAGE_3 as AVERAGE3_L, " \
                + "a.STDDEV_1 as STDDEV1_L, a.STDDEV_2 as STDDEV2_L, a.STDDEV_3 as STDDEV3_L, " \
                + "b.{1} as ID_RIGHT, b.AREA as AREA_RIGHT, " \
                + "b.AVERAGE_1 as AVERAGE1_R, b.AVERAGE_2 as AVERAGE2_R, b.AVERAGE_3 as AVERAGE3_R, " \
                + "b.STDDEV_1 as STDDEV1_R, b.STDDEV_2 as STDDEV2_R, b.STDDEV_3 as STDDEV3_R, " \
                + "ST_intersection(a.geometry, b.geometry) " \
                + "from {0} as a, {0} as b " \
                + "where a.{1} < b.{1} and st_relate(a.geometry,b.geometry,'FF2F11212') {2};"
            sql = sql.format(self._inputLayer.GetName(), idField, where)
            results = self._inputDataSource.ExecuteSQL(sql, dialect='SQLite')
            if results is not None:
                tolerance = self._configValue("RawSegmentsResolution")
                fields = []
                for fld in results.schema:
                    fields.append(self._createField(None, fld.GetName(), fld.GetType(), fld.GetWidth(), fld.GetPrecision()))
                targetLayer.CreateFields(fields)
                for feature in results:
                    geometry = feature.GetGeometryRef()
                    if geometry is not None:
                        try:
                            line = ogr.Geometry(ogr.wkbLineString)
                            count = 0
                            lastPt = None
                            for part in geometry:
                                pt1 = part.GetPoint(0)
                                lastPt = part.GetPoint(1)
                                line.AddPoint(pt1[0], pt1[1])
                                count += 1
                            if lastPt is not None:
                                line.AddPoint(lastPt[0], lastPt[1])
                            newFeature = feature.Clone()
                            newFeature.SetGeometry(line.Simplify(tolerance))
                            targetLayer.CreateFeature(newFeature)
                            processed += 1
                            self._print("Boundary #{0} on polygons {1}/{2} created.".
                                        format(processed, feature.GetField("ID_LEFT"), feature.GetField("ID_RIGHT")), logging.INFO)
                        except:
                            self._print("Error: {0}".format(str(e)), logging.ERROR)
                            self._print("...#{0} on boundary {1}/{2}!".
                                        format(processed, feature.GetField("ID_LEFT"), feature.GetField("ID_RIGHT")), logging.ERROR)
                            failed += 1
                targetLayer.SyncToDisk()
                return True
        except Exception as e:
            self._print("Error: {0}".format(str(e)), logging.ERROR)
            return False
        finally:
            if results:
                self._inputDataSource.ReleaseResultSet(results)
            self._inputLayer.ResetReading()
            self._print("Boundaries with {0} features created, {1} failed.".format(processed, failed), logging.INFO)

    ### Run all processing functions

    def runAll(self):
        try:
            self._print("*** Starting Segmentation...", logging.INFO)

            # Create buffer layers
            targetLayer = self.createBoundaries(self._configValue("RawSegmentsShapeFile"), inMemory = False, asShape = False, asFileName = True)
            if targetLayer:
                self._print("- Edges layer file {0} created.".format(targetLayer), logging.INFO)

            self._print("*** Segmentation finished.", logging.INFO)

            return True
        finally:
            self._closeAllDataSources()

