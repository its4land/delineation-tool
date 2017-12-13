"""
!/bin/python
-*- coding: utf-8 -*
QGIS Version: QGIS 2.16

### Author ###
 S. Crommelinck, 2017

### Description ###
 This script applies Random Forest classification on SLIC lines with certain attributes
"""

### Predefine variables ###
input_csv_training = r"D:\path to file"
input_csv_validation = r"D:\path to file"
output_csv = r"D:\path to file"

### Import required modules ###
import numpy as np
import pandas as pd
import csv

### Get Training samples ###
def get_training_validation_samples():
    ### Training Data ###
    # Open input ascii file for reading
    input_csv = input_csv_training
    file(input_csv_training, 'r')

    # Read values from attribute values
    ID = np.genfromtxt(input_csv, usecols=0, delimiter=',', dtype=None, skip_header=1)
    boundary = np.genfromtxt(input_csv, usecols=1, delimiter=',', dtype=None, skip_header=1)
    length = np.genfromtxt(input_csv, usecols=2, delimiter=',', dtype=None, skip_header=1)
    ucm_rgb = np.genfromtxt(input_csv, usecols=3, delimiter=',', dtype=None, skip_header=1)
    lap_dsm = np.genfromtxt(input_csv, usecols=4, delimiter=',', dtype=None, skip_header=1)
    dist_to_gPb = np.genfromtxt(input_csv, usecols=5, delimiter=',', dtype=None, skip_header=1)
    azimuth = np.genfromtxt(input_csv, usecols=6, delimiter=',', dtype=None, skip_header=1)
    sinuosity = np.genfromtxt(input_csv, usecols=7, delimiter=',', dtype=None, skip_header=1)
    azi_gPb = np.genfromtxt(input_csv, usecols=8, delimiter=',', dtype=None, skip_header=1)
    r_dsm_medi = np.genfromtxt(input_csv, usecols=9, delimiter=',', dtype=None, skip_header=1)
    l_dsm_medi = np.genfromtxt(input_csv, usecols=10, delimiter=',', dtype=None, skip_header=1)
    r_red_medi = np.genfromtxt(input_csv, usecols=11, delimiter=',', dtype=None, skip_header=1)
    l_red_medi = np.genfromtxt(input_csv, usecols=12, delimiter=',', dtype=None, skip_header=1)
    r_gre_medi = np.genfromtxt(input_csv, usecols=13, delimiter=',', dtype=None, skip_header=1)
    l_gre_medi = np.genfromtxt(input_csv, usecols=14, delimiter=',', dtype=None, skip_header=1)
    r_blu_medi = np.genfromtxt(input_csv, usecols=15, delimiter=',', dtype=None, skip_header=1)
    l_blu_medi = np.genfromtxt(input_csv, usecols=16, delimiter=',', dtype=None, skip_header=1)
    red_grad = np.genfromtxt(input_csv, usecols=17, delimiter=',', dtype=None, skip_header=1)
    green_grad = np.genfromtxt(input_csv, usecols=18, delimiter=',', dtype=None, skip_header=1)
    blue_grad = np.genfromtxt(input_csv, usecols=19, delimiter=',', dtype=None, skip_header=1)
    dsm_grad = np.genfromtxt(input_csv, usecols=20, delimiter=',', dtype=None, skip_header=1)

    # Merge all input data in one array with the following structure:
    # [ID length ucm_rgb] -> first row
    # [ID length ucm_rgb] -> second row
    # sample_data[0] = attributes of one feature -> array with 17 values
    # sample_data[:, 0] = all ID values
    # sample_data[row, column] = sample_data[row][column] = sample_data[y][x]
    training_data = np.column_stack((ID, boundary, length, ucm_rgb, lap_dsm, dist_to_gPb, azimuth, sinuosity, azi_gPb,
                                     r_dsm_medi, l_dsm_medi, r_red_medi, l_red_medi, r_gre_medi, l_gre_medi,
                                     r_blu_medi, l_blu_medi, red_grad, green_grad, blue_grad, dsm_grad))

    ### Validation Data ###
    # Open input ascii file for reading
    input_csv = input_csv_validation
    file(input_csv, 'r')

    # Read values from attribute values
    ID = np.genfromtxt(input_csv, usecols=0, delimiter=',', dtype=None, skip_header=1)
    boundary = np.genfromtxt(input_csv, usecols=1, delimiter=',', dtype=None, skip_header=1)
    length = np.genfromtxt(input_csv, usecols=2, delimiter=',', dtype=None, skip_header=1)
    ucm_rgb = np.genfromtxt(input_csv, usecols=3, delimiter=',', dtype=None, skip_header=1)
    lap_dsm = np.genfromtxt(input_csv, usecols=4, delimiter=',', dtype=None, skip_header=1)
    dist_to_gPb = np.genfromtxt(input_csv, usecols=5, delimiter=',', dtype=None, skip_header=1)
    azimuth = np.genfromtxt(input_csv, usecols=6, delimiter=',', dtype=None, skip_header=1)
    sinuosity = np.genfromtxt(input_csv, usecols=7, delimiter=',', dtype=None, skip_header=1)
    azi_gPb = np.genfromtxt(input_csv, usecols=8, delimiter=',', dtype=None, skip_header=1)
    r_dsm_medi = np.genfromtxt(input_csv, usecols=9, delimiter=',', dtype=None, skip_header=1)
    l_dsm_medi = np.genfromtxt(input_csv, usecols=10, delimiter=',', dtype=None, skip_header=1)
    r_red_medi = np.genfromtxt(input_csv, usecols=11, delimiter=',', dtype=None, skip_header=1)
    l_red_medi = np.genfromtxt(input_csv, usecols=12, delimiter=',', dtype=None, skip_header=1)
    r_gre_medi = np.genfromtxt(input_csv, usecols=13, delimiter=',', dtype=None, skip_header=1)
    l_gre_medi = np.genfromtxt(input_csv, usecols=14, delimiter=',', dtype=None, skip_header=1)
    r_blu_medi = np.genfromtxt(input_csv, usecols=15, delimiter=',', dtype=None, skip_header=1)
    l_blu_medi = np.genfromtxt(input_csv, usecols=16, delimiter=',', dtype=None, skip_header=1)
    red_grad = np.genfromtxt(input_csv, usecols=17, delimiter=',', dtype=None, skip_header=1)
    green_grad = np.genfromtxt(input_csv, usecols=18, delimiter=',', dtype=None, skip_header=1)
    blue_grad = np.genfromtxt(input_csv, usecols=19, delimiter=',', dtype=None, skip_header=1)
    dsm_grad = np.genfromtxt(input_csv, usecols=20, delimiter=',', dtype=None, skip_header=1)

    validation_data = np.column_stack((ID, boundary, length, ucm_rgb, lap_dsm, dist_to_gPb, azimuth, sinuosity, azi_gPb,
                                       r_dsm_medi, l_dsm_medi, r_red_medi, l_red_medi, r_gre_medi, l_gre_medi,
                                       r_blu_medi, l_blu_medi, red_grad, green_grad, blue_grad, dsm_grad))

    print "--> all values from attribute table read.\n"

    # Number of attributes (without ID and boundary value)
    N_attr = len(training_data[0]) - 2

    # Create arrays to store data
    training_samples = len(training_data)
    validation_samples = len(validation_data)

    # Divide training and validation data again into two portions x/a (features) and y/b (manual labels)
    training_data_x = np.zeros([training_samples, N_attr])
    training_data_y = np.zeros([training_samples, 1])

    validation_data_a = np.zeros([validation_samples, N_attr])
    validation_data_b = np.zeros([validation_samples, 1])

    # Create array for output data which contains same data as validation_data_a + IDs
    validation_data_output = np.zeros([validation_samples, N_attr + 1])

    # Fill arrays with data from csv
    for i in range(0, training_samples):
        training_data_x[i] = np.array(training_data[i][2:N_attr + 2])
        training_data_y[i] = np.array(training_data[i][1:2])

    for i in range(0, validation_samples):
        validation_data_a[i] = np.array(validation_data[i][2:N_attr + 2])
        validation_data_b[i] = np.array(validation_data[i][1:2])

    for i in range(0, validation_samples):
        validation_data_output[i] = np.array(validation_data[i][0:N_attr + 1])

    # Replace no data values with -1
    where_are_NaNs = np.isnan(training_data_x)
    training_data_x[where_are_NaNs] = -1

    where_are_NaNs = np.isnan(validation_data_a)
    validation_data_a[where_are_NaNs] = -1

    print'--> stored all data in array.\n'
    return training_data_x, training_data_y, validation_data_a, validation_data_b, validation_data_output


# Call function to get training and validation data
training_data_x, training_data_y, validation_data_a, validation_data_b, validation_data_output \
    = get_training_validation_samples()

print'Features in training data: %i\n' % (len(training_data_x))
print'Features in validation data: %i\n' % (len(validation_data_a))

# List of features
features = ["length", "ucm_rgb", "lap_dsm", "dist_to_gP", "azimuth", "sinuosity", "azi_gPb", "r_dsm_medi", "l_dsm_medi",
            "r_red_medi", "l_red_medi", "r_gre_medi", "l_gre_medi", "r_blu_medi", "l_blu_medi", "red_grad",
            "green_grad", "blue_grad", "dsm_grad"]

### Train random forest classifier ###
# Load scikit's random forest classifier library
from sklearn.ensemble import RandomForestClassifier

# Create RF classifier model
clf = RandomForestClassifier(n_jobs=2, n_estimators=100)
print'--> RF classifier model created.\n'

# Train the classifier to take the training features and learn how they relate to the training y (the species/labels)
clf.fit(training_data_x, training_data_y[:, 0])
print'--> RF classifier trained.\n'

# Predict class for validation_data_a
prediction = clf.predict(validation_data_a)

# Predict class probabilities for validation_data_a
prediction_proba = clf.predict_proba(validation_data_a)
print'--> RF model applied to data.\n'

### Create confusion matrix and print results ###
cm = pd.crosstab(validation_data_b[:, 0], prediction, rownames=['Actual Class'], colnames=['Predicted Class'])
print'--> Confusion matrix created.\n'

print('Confusion matrix:\n')
print(cm)
print('##########################')

# View a list of the features and their importance scores
print('feature importance')
for i in range(0, len(features)):
    print(features[i], clf.feature_importances_[i])
print('##########################')

# Print quality measures
accuracy = float((cm[0][0] + cm[1][1])) / float(cm[0][0] + cm[1][1] + cm[0][1] + cm[1][0])
print('overall accuracy: ', accuracy)
print('##########################')
precision = float(cm[1][1]) / (cm[1][0] + cm[1][1])
recall = float(cm[1][1]) / (cm[0][1] + cm[1][1])
fscore = 2 * ((precision * recall) / (precision + recall))
print('Recall/Completeness', recall)  # TP/(TP+FN) of all lines labelled as boundary, how many are correct?
print('Precision/Correctness', precision)  # TP/(TP+FP) of all true boundaries, how many are labelled correctly as
# boundaries?
print('fscore', fscore)  # harmonic mean of precision and recall [0;1]

### Create new csv file containing the probability of being a boundary per line ###
# Create array for probability values
proba_vals = np.zeros([len(validation_data_output), 1])

for i in range(0, len(validation_data_output)):
    proba_vals[i] = 1 - prediction_proba[i, 1]
print'\n--> Collecting boundary probabilities per line.\n'

# Write output to csv file
with open(output_csv, 'w') as csvoutput:
    writer = csv.writer(csvoutput, lineterminator='\n',
                        quoting=csv.QUOTE_NONNUMERIC)  # converts all non-quoted fields to type float
    header = ["ID", "length", "ucm_rgb", "lap_dsm", "dist_to_gP", "azimuth", "sinuosity", "azi_gPb", "r_dsm_medi",
              "l_dsm_medi", "r_red_medi", "l_red_medi", "r_gre_medi", "l_gre_medi", "r_blu_medi", "l_blu_medi",
              "red_grad", "green_grad", "blue_grad", "dsm_grad", "proba_bo"]
    writer.writerow(header)

    all = np.zeros([len(validation_data_output), 21])
    for i in range(0, len(validation_data_output)):
        row = np.append(validation_data_output[i], proba_vals[i])  # write output as shorter number
        all[i] = row
    writer.writerows(all)

csvoutput.close()

print'--> Written boundary probabilities to updated csv file.\n'

print'--> All processing finished.\n'

"""
### Notes ###
# Websites:
http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier.fit
"""