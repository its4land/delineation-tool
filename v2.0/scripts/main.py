# -*- coding: utf-8 -*-
"""
/***************************************************************************
 its4land WP5: Automate It
                              -------------------
        begin                : 2018-05-23
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Sophie Crommelinck
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
 main module for running inside a docker container et al.
"""

from AttributeCalculation import AttributeCalculation
from Classification import Classification
from Segmentation import Segmentation

from os import *
from sys import argv, stdout


QUIT = 0
SEGM = 1
EDGE = 2
ATTR = 3
CRCL = 4
PRD = 5
HELP = 9

SEED = 12
SEA = 123
EDAT = 23
SEAC = 1234
SEAP = 1235
PREP = 123

TRAIN = 21
CLASS = 22
PRED = 23


argumentsCount = {QUIT:0, HELP:0, SEGM:1, EDGE:1, ATTR:3, CRCL:1, PRD:2, 
                  SEED:1, SEA:3, EDAT:3, SEAC:3, SEAP:4, 
                  TRAIN:3, CLASS:1, PRED:4}
parameterMessage = {QUIT:"-q:  Quit", 
                    HELP:"-h:  Shows this parameter list", 
                    SEGM:"-s <fileName>:  Segmentation - input: raster file; output: segments file", 
                    EDGE:"-e <fileName>:  segments to Edges - input: segments file; output: edges file", 
                    ATTR:"-a <fileName> <fileName> <fileName>:  calculate Attributes - input: RGB Raster, DSM Raster, edges file; output: calculated edges file", 
                    CRCL:"-c <fileName>:  Create Classifier - input: calculated edges file; output: classifier", 
                    PRD:"-p <fileName> <fileName>:  Predict boundaries - input: edges file, classifier; output: classified validation set", 

                    SEED:"-se <fileName>:  input: raster file; output: edges file", 
                    SEA:"-sea <fileName> <fileName> <fileName>:  input: raster file, RGB Raster, DSM Raster; output: calculated edges file", 
                    EDAT:"-ea <fileName> <fileName> <fileName>:  input: RGB Raster, DSM Raster, edges file; output: calculated edges file", 
                    SEAC:"-seac <fileName> <fileName> <fileName>:  input: raster file, RGB Raster, DSM Raster; output: classifier", 
                    SEAP:"-seap <fileName> <fileName> <fileName> <classifier>:  input: raster file, RGB Raster, DSM Raster, classifier; output: classified edges file",

                    TRAIN:"-train:  Create Training Set - input: raster file, RGB Raster, DSM Raster; output: calculated training set", 
                    CLASS:"-class:  Create Classifier - input: training set; output: classifier", 
                    PRED: "-pred:   Prediction - input: raster file, RGB Raster, DSM Raster, classifier; output: classified validation set"}

outputData = None
testMode = False

def parseArguments (args):
    arguments = {"-q":QUIT, "-h":HELP, "-s":SEGM, "-e":EDGE, "-a":ATTR, "-c":CRCL, "-p": PRD, 
                 "-se":SEED, "-sea":SEA, "-ea":EDAT, "-seac":SEAC, "-seap":SEAP,
                 "-train":TRAIN, "-class":CLASS, "-pred":PRED}
    modID = None
    inputParams = []
    i = 0
    for arg in args:
        if i > 0:
            if arg.lower() == "--test":
                global testMode
                testMode = True
            elif modID is None:
                modID = arguments.get(arg.lower())
                if modID is None:
                    inputParams.append(arg)
            else:
                inputParams.append(arg)
        i += 1
    if testMode and not inputParams:
        inputParams = [None, None, None, None]
    return modID, inputParams

def executeParams (modID, inputParams):
    if modID == HELP:
        print("*** ITS4LAND WP5: Automate It *** - Parameters:")
        if testMode:
            print(parameterMessage[SEGM])
            print(parameterMessage[EDGE])
            print(parameterMessage[ATTR])
            print(parameterMessage[CRCL])
            print(parameterMessage[PRD])
            
            print(parameterMessage[SEED])
            print(parameterMessage[SEA])
            print(parameterMessage[EDAT])
            print(parameterMessage[SEAC])
            print(parameterMessage[SEAP])
        print(parameterMessage[TRAIN])
        print(parameterMessage[CLASS])
        print(parameterMessage[PRED])
        print(parameterMessage[HELP])
        print(parameterMessage[QUIT])
    elif modID == QUIT:
        print("Leaving 'Automate It' - bye!")
    else:
        global outputData
        argNum = argumentsCount[modID]
        if argNum > 0 and (inputParams is None or len(inputParams) < argNum):
            print("This function needs {0} input parameter(s):".format(argNum))
            print(parameterMessage[modID])
        else:
            process = None
            if modID == SEGM:
                process = Segmentation()
                outputData = process.createSegmentation(inputParams[0])
            elif modID == EDGE:
                process = Segmentation()
                outputData = process.createBoundaries(inputParams[0])
            elif modID == ATTR:
                process = AttributeCalculation()
                outputData = process.runAll(inputParams[0], inputParams[1], inputParams[2])
            elif modID in [CRCL, CLASS]:
                process = Classification()
                outputData = process.createClassifier(inputParams[0], None) 
            elif modID == PRD:
                process = Classification()
                outputData = process.applyClassifier(inputParams[1], inputParams[0])
            elif modID == SEED:
                process = Segmentation()
                fileName = process.createSegmentation(inputParams[0])
                outputData = process.createBoundaries(fileName)
            elif modID in [SEA, TRAIN]:
                process = Segmentation()
                fileName = process.createSegmentation(inputParams[0])
                fileName = process.createBoundaries(fileName)
                process = AttributeCalculation()
                outputData = process.runAll(inputParams[1], inputParams[2], fileName)
            elif modID == EDAT:
                process = Segmentation()
                fileName = process.createBoundaries(inputParams[2])
                process = AttributeCalculation()
                outputData = process.runAll(inputParams[0], inputParams[1], fileName)
            elif modID == SEAC:
                process = Segmentation()
                fileName = process.createSegmentation(inputParams[0])
                fileName = process.createBoundaries(fileName)
                process = AttributeCalculation()
                fileName = process.runAll(inputParams[1], inputParams[2], fileName)
                process = Classification()
                outputData = process.createClassifier(fileName, None) 
            elif modID in [SEAP, PRED]:
                process = Segmentation()
                fileName = process.createSegmentation(inputParams[0])
                fileName = process.createBoundaries(fileName)
                process = AttributeCalculation()
                fileName = process.runAll(inputParams[1], inputParams[2], fileName)
                process = Classification()
                outputData = process.applyClassifier(inputParams[3], fileName)
        modID = HELP
    return modID

#for key, value in environ.items():
#    print(key + "=" + value)

args = argv
modID, inputParams = parseArguments(args)
if modID is not None:
    executeParams(modID, inputParams)
else:
    while modID != QUIT:
        modID, inputParams = parseArguments(args)
        if modID is None:
            modID = HELP
        modID = executeParams(modID, inputParams)
        if modID == HELP:
            try:
                cmd = argv[0] + " " + input('--> ')
                args = cmd.split(" ")
            except:
                modID = QUIT
if outputData:
    #print("Output File: {0}".format(outputData))
    #stdout.write(outputData)
    environ["OUTPUT_DATA"] = outputData
    #for key, value in environ.items():
    #    print(key + "=" + value)



