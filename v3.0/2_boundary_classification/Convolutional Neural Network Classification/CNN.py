"""
!/bin/python
-*- coding: utf-8 -*-
/*****************************************************************************
        begin                : 2019-03-22
        copyright            : (C) 2019 by Sophie Crommelinck, 
                                University of Twente
        email                : s.crommelinck@utwente.nl
        description          : this script applies transfer-learning on a
                                pre-trained CNN to predict class
                                probabilities for image tiles.
        funding              : H2020 EU project its4land 
                                (#687826, its4land.com)
                                Work package 5: Automate It
	development          : Sophie Crommelinck
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

# Import modules
from keras import backend as K
from keras import utils
from keras import optimizers
from keras.models import Model
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.layers import Dense, Dropout, GlobalAveragePooling2D
from keras.applications.vgg19 import VGG19
from keras.applications.vgg19 import preprocess_input
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import pandas
import numpy as np
import cv2
import os
from shutil import copy
from datetime import datetime
import tensorflow as tf
import random as rn

# Define input parameters
scriptVersion = "_v21"

imagePathTraining = r"/xxx/CNN/CNN_balanced/training"
imagePathValidation = r"/xxx/CNN/CNN_balanced/validation"
imagePathTesting = r"/xxx/CNN/CNN_balanced/testing"
imagePathPrediction = r"/xxx/CNN/CNN_balanced/prediction"
resultPath = r"/xxx/CNN/CNN_results"
labelLocation = 1                                               # index location of class label in input file ('b0_image.tif) -> label 0 = index 1
ext = '.tif'                                                    # image format of input and output images

# Hyper parameters
nBatches = 32                                                   # batch size used for training, evaluation and predictions
nEpochs = 100                                                   # number of epochs
nClasses = 2
imagesize = 224
nBands = 3
classWeights = None

# Ensure reproducible results
np.random.seed(42)
rn.seed(12345)
session_conf = tf.ConfigProto(intra_op_parallelism_threads=1,
                              inter_op_parallelism_threads=1)
tf.set_random_seed(1234)
sess = tf.Session(graph=tf.get_default_graph(), config=session_conf)
K.set_session(sess)

# INFO and WARNING messages are not printed
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def load_data(path, labelLocation):
    print("%s: Loading images..." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    imagedata = []
    imagefiles = os.listdir(path)
    labels = []

    # Read input images and labels
    for imagefile in imagefiles:
        if os.path.splitext(imagefile)[-1] == ext:
            image = cv2.imread(os.path.join(path, imagefile))
            imagedata.append(image)
            label = imagefile[labelLocation:labelLocation+1]
            labels.append(label)
        else:
            print("%s: Input folder contains a file or directory that cannot be read as input data." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

    # Scale RGB pixel values to the range [0, 1]
    data = np.array(imagedata, dtype="float") / 255.0

    # Converts labels to binary class matrix
    labels = utils.to_categorical(np.array(labels))

    print("%s: Images loaded:"
          "\n\t\t\t\t\t\t Number of images: %i"
          "\n\t\t\t\t\t\t Number of pixels: %i x %i"
          "\n\t\t\t\t\t\t Number of bands: %i"
          "\n\t\t\t\t\t\t Number of classes: %i" %
          (datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
           data.shape[0],
           len(data[0][0]), len(data[0][0]),
           len(data[0][0][0]),
           len(labels[0])))
    return data, labels, imagefiles

def generate_data(path, imagesize, nBatches):
    datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
    generator = datagen.flow_from_directory(directory=path,     # path to the target directory
         target_size=(imagesize,imagesize),                     # dimensions to which all images found will be resize
         color_mode='rgb',                                      # whether the images will be converted to have 1, 3, or 4 channels
         classes=None,                                          # optional list of class subdirectories
         class_mode='categorical',                              # type of label arrays that are returned
         batch_size=nBatches,                                   # size of the batches of data
         shuffle=True,                                          # whether to shuffle the data
         seed=42)                                               # random seed for shuffling and transformations
    return generator

def create_model(imagesize, nBands, nClasses):
    print("%s: Creating the model..." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    # Create pre-trained base model
    basemodel = VGG19(include_top=False,                        # exclude final pooling and fully connected layer in the original model
                         weights='imagenet',                    # pre-training on ImageNet
                         input_tensor=None,                     # optional tensor to use as image input for the model
                         input_shape=(imagesize,                # shape tuple
                                      imagesize,
                                      nBands),
                         pooling=None,                          # output of the model will be the 4D tensor output of the last convolutional layer
                         classes=nClasses)                      # number of classes to classify images into

    # Freeze weights on pre-trained layers
    for layer in basemodel.layers:
        layer.trainable = False

    print("%s: Base model created with %i layers and %i parameters." %
          (datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
           len(basemodel.layers),
           basemodel.count_params()))

    # Create new untrained layers
    x = basemodel.output
    x = GlobalAveragePooling2D()(x)                             # global spatial average pooling layer
    x = Dense(1024, activation='relu')(x)                       # fully-connected layer
    x = Dropout(rate=0.8)(x)                                    # dropout layer
    y = Dense(nClasses, activation='softmax')(x)                # logistic layer making sure that probabilities sum up to 1

    # Create model combining pre-trained base model and new untrained layers
    model = Model(inputs=basemodel.input,
                  outputs=y)
    print("%s: New model created with %i layers and %i parameters." %
          (datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
           len(model.layers),
           model.count_params()))

    # Define learning optimizer
    learningRate = 0.001
    optimizerSGD = optimizers.SGD(lr=learningRate,              # learning rate.
                                  momentum=0.9,                 # parameter that accelerates SGD in the relevant direction and dampens oscillations
                                  decay=learningRate/nEpochs,   # learning rate decay over each update
                                  nesterov=True)                # whether to apply Nesterov momentum
    # Compile model
    model.compile(optimizer=optimizerSGD,                       # stochastic gradient descent optimizer
                  loss='categorical_crossentropy',              # objective function
                  metrics=['accuracy'],                         # metrics to be evaluated by the model during training and testing
                  loss_weights=None,                            # scalar coefficients to weight the loss contributions of different model outputs
                  sample_weight_mode=None,                      # sample-wise weights
                  weighted_metrics=None,                        # metrics to be evaluated and weighted by sample_weight or class_weight during training and testing
                  target_tensors=None)                          # tensor model's target, which will be fed with the target data during training
    print("%s: Model compiled." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    return model

def train_model(model, nBatches, nEpochs, trainGenerator, valGenerator, classWeights, resultPath):
    callback = [EarlyStopping(monitor='val_acc',                # quantity to be monitored
                             min_delta=0,                       # minimum change in the monitored quantity to qualify as an improvement
                             patience=50,                       # number of epochs with no improvement after which training will be stopped
                             verbose=1,                         # verbosity mode
                             mode='max',                        # one of {auto, min, max}
                             baseline=None,                     # training will stop if the model doesn't show improvement over the baseline
                             restore_best_weights=False),       # whether to restore model weights from the epoch with the best value of the monitored quantity
                ModelCheckpoint(filepath= os.path.join(resultPath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + scriptVersion + '_modelCheckpoint.h5'),
                                monitor='val_acc',              # quantity to monitor.
                                verbose=0,                      # verbosity mode, 0 or 1
                                save_best_only=True,            # if True, the latest best model according to the quantity monitored will not be overwritten
                                save_weights_only=False,        # if True, then only the model's weights will be saved
                                mode='auto',                    # one of {auto, min, max}
                                period=1)]                      # interval (number of epochs) between checkpoints

    history = model.fit_generator(generator=trainGenerator,
                                  steps_per_epoch=trainGenerator.samples//nBatches,     # total number of steps (batches of samples)
                                  epochs=nEpochs,                   # number of epochs to train the model
                                  verbose=2,                        # verbosity mode. 0 = silent, 1 = progress bar, 2 = one line per epoch
                                  callbacks=callback,               # keras.callbacks.Callback instances to apply during training
                                  validation_data=valGenerator,     # generator or tuple on which to evaluate the loss and any model metrics at the end of each epoch
                                  validation_steps=
                                  valGenerator.samples//nBatches,   # number of steps (batches of samples) to yield from validation_data generator before stopping at the end of every epoch
                                  class_weight=classWeights,                # optional dictionary mapping class indices (integers) to a weight (float) value, used for weighting the loss function
                                  max_queue_size=10,                # maximum size for the generator queue
                                  workers=1,                        # maximum number of processes to spin up when using process-based threading
                                  use_multiprocessing=False,        # whether to use process-based threading
                                  shuffle=True,                     # whether to shuffle the order of the batches at the beginning of each epoch
                                  initial_epoch=0)                  # epoch at which to start training
    print("%s: Model trained." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

    # Save model
    modelPath = os.path.join(resultPath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + scriptVersion + '_modelArchitecture.h5')
    weightsPath = os.path.join(resultPath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + scriptVersion + '_modelWeights.h5')
    model.save(modelPath)
    model.save_weights(weightsPath)
    print("%s: Model saved." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    return history, model

def evaluate_model(model, generator, nBatches):
    # Loss and accuracy
    score = model.evaluate_generator(generator=generator,           # Generator yielding tuples
                                     steps=generator.samples//nBatches, # number of steps (batches of samples) to yield from generator before stopping
                                     max_queue_size=10,           # maximum size for the generator queue
                                     workers=1,                   # maximum number of processes to spin up when using process based threading
                                     use_multiprocessing=False,   # whether to use process-based threading
                                     verbose=0)
    print("\t eval_loss: %.3f - eval_acc: %.3f" %
          (score[0], score[1]))

def plot_acc_loss(history, path):
    acc = history.history['acc']
    val_acc = history.history['val_acc']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    epochs = range(len(acc))

    plt.figure()
    plt.plot(epochs, acc, color='#ff0000', label='training accuracy')
    plt.plot(epochs, val_acc, color='#00ff00', label='validation accuracy')
    plt.plot(epochs, loss, linestyle='-.', color='#ff0000', label='training loss')
    plt.plot(epochs, val_loss, linestyle='-.', color='#00ff00', label='validation loss')
    plt.ylim(0, 2)
    plt.xlim(0, 100)
    plt.xlabel("epoch")
    plt.ylabel("accuracy and loss")
    plt.legend()
    plt.savefig(os.path.join(path, datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + scriptVersion + '_evaluationPlot.jpg'))
    print("%s: Model evaluation plotted." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

def evaluate_predcitions(model, generator, resultPath):
    # Get predictions
    predictions = model.predict_generator(generator=generator,
                                    steps=generator.samples/nBatches,
                                    max_queue_size=10,
                                    workers=1,
                                    use_multiprocessing=False,
                                    verbose=0)

    # Evaluate predictions
    predictedClass = np.argmax(predictions, axis=1)
    trueClass = generator.classes
    classLabels = list(generator.class_indices.keys())

    # Create classification report
    classificationReport = (classification_report
          (y_true=trueClass,                                    # ground truth (correct) target values
           y_pred=predictedClass,                               # estimated targets as returned by a classifier
           target_names=classLabels,                            # display names matching the labels
            output_dict = True))

    print(classification_report
          (y_true=trueClass,                                    # ground truth (correct) target values
           y_pred=predictedClass,                               # estimated targets as returned by a classifier
           target_names=classLabels,                            # display names matching the labels
           output_dict=False))

    # Save classification report
    df = pandas.DataFrame(classificationReport).transpose()
    outputfileCSV = os.path.join(resultPath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + scriptVersion + '_classificationReport.csv')
    df.to_csv(path_or_buf=outputfileCSV, sep='\t')

    # Create confusion matrix
    confusionMatrix = (confusion_matrix(
        y_true=trueClass,                                       # ground truth (correct) target values
        y_pred=predictedClass))                                 # estimated targets as returned by a classifier

    # Save confusion matrix
    df = pandas.DataFrame(confusionMatrix)
    df.to_csv(path_or_buf=outputfileCSV, sep='\t', mode='a')    # append confusion matrix to CSV
    print(df)

    # Save confusion matrix figure
    fig = plt.figure()
    ax = fig.add_subplot(111)
    cax = ax.matshow(confusionMatrix, cmap='binary', interpolation='None')
    fig.colorbar(cax)
    ax.set_xticklabels([''] + classLabels)
    ax.set_yticklabels([''] + classLabels)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.savefig(os.path.join(resultPath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + scriptVersion + '_confusionMatrix.jpg'))
    print("%s: Metrics saved." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

def predict_labels(model, testX, nBatches, resultPath, testImageFiles, ext):
    # Get predictions
    predictions = model.predict(x=testX,                        # numpy array of testing data
                                batch_size=nBatches,            # number of samples per gradient update
                                verbose=0,                      # verbosity mode. 0 = silent, 1 = progress bar, 2 = one line per epoch
                                steps=None)                     # total number of steps (batches of samples) before declaring the prediction round finished

    # Change to current directory
    os.chdir(resultPath)

    # Create directory to store updated training tiles
    time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    outputDir = "trainY_" + time + scriptVersion
    os.mkdir(outputDir)

    # Save prediction to image files
    print("%s: Write predictions to image files..." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    for i in range(0, len(predictions)):
        # Get path for input files
        inputfile = os.path.splitext(testImageFiles[i])[0]
        inputfilePath = os.path.join(imagePathPrediction, testImageFiles[i])

        # Get path for output files
        # probability for tile belonging
        #   to first class -> predictions[i][0]
        #   to second class -> predictions[i][1]
        outputfile = os.path.join(inputfile + "_p_" + str(round(predictions[i][0], 3)) + ext)
        outputfilePath = os.path.join(resultPath, outputDir, outputfile)

        # Copy updated input file to output directory
        copy(inputfilePath, outputfilePath)
    print("%s: Predictions written to image files." % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

def main():
    # Create model
    modelUntrained = create_model(imagesize, nBands, nClasses)

    # Prepare training and validation data
    trainGenerator = generate_data(imagePathTraining, imagesize, nBatches)
    valGenerator = generate_data(imagePathValidation, imagesize, nBatches)

    # Train and save model
    history, modelTrained = train_model(modelUntrained, nBatches, nEpochs, trainGenerator, valGenerator, classWeights, resultPath)

    # Evaluate on validation data
    print("%s: Model evaluation on validation data:" % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    evaluate_model(modelTrained, valGenerator, nBatches)
    evaluate_predcitions(modelTrained, valGenerator, resultPath)

    # Evaluate on training data
    print("%s: Model evaluation on training data:" % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    evaluate_model(modelTrained, trainGenerator, nBatches)

    # Plot evaluation of trained model
    plot_acc_loss(history, resultPath)

    # Evaluate on testing data
    testGenerator = generate_data(imagePathTesting, imagesize, nBatches)
    print("%s: Model evaluation on testing data:" % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    evaluate_model(modelTrained, testGenerator, nBatches)
    evaluate_predcitions(modelTrained, testGenerator, resultPath)

    # Write predictions to testing data
    testX, testY, testImageFiles = load_data(imagePathPrediction, labelLocation)
    predict_labels(modelTrained, testX, nBatches, resultPath, testImageFiles, ext)

if __name__ == "__main__":
    main()
