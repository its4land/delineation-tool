from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Simplifysegmentation(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('inputsegmentation', 'Input Segmentation', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Simplifiedsegmentation', 'SimplifiedSegmentation', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(11, model_feedback)
        results = {}
        outputs = {}

        # Extract layer extent
        alg_params = {
            'INPUT': parameters['inputsegmentation'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractLayerExtent'] = processing.run('qgis:polygonfromlayerextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Polygons to lines
        alg_params = {
            'INPUT': outputs['ExtractLayerExtent']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PolygonsToLines'] = processing.run('qgis:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Union
        alg_params = {
            'INPUT': outputs['PolygonsToLines']['OUTPUT'],
            'OVERLAY': parameters['inputsegmentation'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Union'] = processing.run('native:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Polygonize
        alg_params = {
            'INPUT': outputs['Union']['OUTPUT'],
            'KEEP_FIELDS': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Polygonize'] = processing.run('qgis:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': True,
            'DISTANCE': 1e-05,
            'END_CAP_STYLE': 2,
            'INPUT': outputs['PolygonsToLines']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Field calculator
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': '$area',
            'INPUT': outputs['Polygonize']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldCalculator'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Select by expression
        alg_params = {
            'EXPRESSION': '\"area\" <30',
            'INPUT': outputs['FieldCalculator']['OUTPUT'],
            'METHOD': 0
        }
        outputs['SelectByExpression'] = processing.run('qgis:selectbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Eliminate selected polygons
        alg_params = {
            'INPUT': outputs['SelectByExpression']['OUTPUT'],
            'MODE': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EliminateSelectedPolygons'] = processing.run('qgis:eliminateselectedpolygons', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # v.to.lines
        alg_params = {
            'GRASS_MIN_AREA_PARAMETER': 0.0001,
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_SNAP_TOLERANCE_PARAMETER': -1,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_LCO': '',
            'input': outputs['EliminateSelectedPolygons']['OUTPUT'],
            'method': 0,
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Vtolines'] = processing.run('grass7:v.to.lines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Define layer projection
        alg_params = {
            'CRS': 'ProjectCrs',
            'INPUT': outputs['Vtolines']['output']
        }
        outputs['DefineLayerProjection'] = processing.run('qgis:definecurrentprojection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Symmetrical difference
        alg_params = {
            'INPUT': outputs['DefineLayerProjection']['INPUT'],
            'OVERLAY': outputs['Buffer']['OUTPUT'],
            'OUTPUT': parameters['Simplifiedsegmentation']
        }
        outputs['SymmetricalDifference'] = processing.run('native:symmetricaldifference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Simplifiedsegmentation'] = outputs['SymmetricalDifference']['OUTPUT']
        return results

    def name(self):
        return 'SimplifySegmentation'

    def displayName(self):
        return 'SimplifySegmentation'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Simplifysegmentation()
