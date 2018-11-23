from __future__ import print_function
import gzip
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import glob
import shutil
import sys
import urllib
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from PIL import Image
from mask_to_submission import *
from helpers import *

import code
import tensorflow.python.platform

import numpy as np

import tensorflow as tf
from scipy import misc, ndimage

import keras
#from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.utils import np_utils
from keras import backend as K
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img


from pathlib import Path
from sklearn.utils import class_weight



NUM_CHANNELS = 3 # RGB images
PIXEL_DEPTH = 255
NUM_LABELS = 2
TRAINING_SIZE = 50
TESTING_SIZE = 50
VALIDATION_SIZE = 5  # Size of the validation set.
SEED = 66478  # Set to None for random seed.
BATCH_SIZE = 16 # 64
NUM_EPOCHS = 5
RESTORE_MODEL = False # If True, restore existing model instead of training a new one
RECORDING_STEP = 1000
MAX_AUG = 4

# The size of the patches each image is split into. Should be a multiple of 4, and the image
# size would be a multiple of this. For this assignment to get the delivery correct it has to be 16
IMG_PATCH_SIZE = 16


# Extract data into numpy arrays, divided into patches of 16x16
data_dir = 'data/'
train_data_filename = data_dir + 'training/images/'
train_labels_filename = data_dir + 'training/groundtruth/' 
test_data_filename = data_dir + 'test_set_images'


#############################################
seed = 0
datagenImg = ImageDataGenerator(
        rotation_range=90, #in radians
        zoom_range=0.1,
        vertical_flip=True,
        fill_mode= 'reflect')
        #horizontal_flip=True,
        #shear_range=0.25,
        #width_shift_range=0.2,
        #height_shift_range=0.2,
        #channel_shift_range=10,
datagenGT = ImageDataGenerator(
        rotation_range=90, #in radians
        zoom_range=0.1,
        vertical_flip=True,
        fill_mode= 'reflect')
        #horizontal_flip=True,
        #shear_range=0.25,
        #width_shift_range=0.2,
        #height_shift_range=0.2,
        #channel_shift_range=10,

data_gen_args = dict(featurewise_center=True,
                     featurewise_std_normalization=True,
                     rotation_range=90,
                     width_shift_range=0.1,
                     height_shift_range=0.1,
                     shear_range=0.15,
                     zoom_range=0.1,
                     channel_shift_range=10,
                     horizontal_flip=True,
                     vertical_flip=True)
imgDir = data_dir + 'training/augmented/images'
groundThruthDir = data_dir + 'training/augmented/groundtruth'

# Create target directory & all intermediate directories if don't exists
try:
  os.makedirs(imgDir)
  os.makedirs(groundThruthDir)
  print("Directory " , imgDir ,  " Created ")
except FileExistsError:
    print("Directory " , imgDir ,  " already exists")  





image_datagen = ImageDataGenerator(**data_gen_args)
ground_thruth_datagen = ImageDataGenerator(**data_gen_args)

#moving original pictures to augmentet position
for i in range(1, TRAINING_SIZE+1):
  imageid = "satImage_%.3d" % i
  image_filename = train_data_filename + imageid + ".png"
  gt_filename = train_labels_filename + imageid + ".png"
  image_dest = imgDir + "/" + imageid + ".png"
  gt_dest = groundThruthDir + "/" + imageid + ".png"
  #print(image_dest,gt_dest)
  shutil.copyfile(image_filename, image_dest)
  shutil.copyfile(gt_filename, gt_dest)

for i in range(1,TRAINING_SIZE+1):
  imageid = "satImage_%.3d" % i
  image_filename = train_data_filename + imageid + ".png"
  groundthruth_filename = train_labels_filename + imageid + ".png"
  trainImg = load_img(image_filename)
  trainLabel = load_img(groundthruth_filename,color_mode='grayscale')
  img_arr = img_to_array(trainImg)
  img_arr = img_arr.reshape((1,) + img_arr.shape)
  gT_arr = img_to_array(trainLabel)
  gT_arr = gT_arr.reshape((1,) + gT_arr.shape)
  #for j in range(5):
    #image_datagen.flow_from_directory(img_arr,batch_size=1, save_to_dir=imgDir, save_prefix=imageid,save_format='png', seed=j)
    #ground_thruth_datagen.flow_from_directory(gT_arr,batch_size=1, save_to_dir=groundThruthDir, save_prefix=imageid,save_format='png', seed=j)
  j = 0
  for batch in datagenImg.flow(
    img_arr,
    batch_size=1, 
    save_to_dir=imgDir, 
    save_prefix=imageid,
    save_format='png', 
    seed=j):
    j +=1
    if j>=MAX_AUG:
      break
  j = 0
  for batch in datagenGT.flow(
    gT_arr,
    batch_size=1, 
    save_to_dir=groundThruthDir, 
    save_prefix=imageid,
    save_format='png', 
    seed=j):
    j +=1
    if j>=MAX_AUG:
      break



# Loading the data, and set wheter it is to be augmented or not
x_train, y_train, x_test = load_data(train_data_filename, train_labels_filename, test_data_filename, TRAINING_SIZE, IMG_PATCH_SIZE, TESTING_SIZE, 
          augment=True, MAX_AUG=MAX_AUG, augImgDir=imgDir) # The last 3 parameters can be blank when we dont want augmentation



# Class weigths
classes = np.array([0,1])
class_weights = class_weight.compute_class_weight('balanced',classes,y_train[:,1])


# input image dimensions
img_rows, img_cols = BATCH_SIZE, BATCH_SIZE
input_shape = (img_rows, img_cols, NUM_CHANNELS) 

model = Sequential()
model.add(Conv2D(32, kernel_size=(2, 2),
                 activation='relu',
                 input_shape=input_shape, padding="same")) #32 is number of outputs from that layer, kernel_size is filter size, 
#model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2), padding="same"))
model.add(Conv2D(64, (3, 3), activation='relu', padding="same"))
model.add(MaxPooling2D(pool_size=(2, 2), padding="same"))
model.add(Conv2D(64*2, (5, 5), activation='relu', padding="same"))
model.add(MaxPooling2D(pool_size=(2, 2), padding="same"))
model.add(Flatten())
model.add(Dense(128*2, activation='relu'))
#model.add(Dropout(0.5))
model.add(Dense(NUM_LABELS, activation='softmax'))

# Compile
model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adadelta(),
              metrics=['accuracy'])

# Train the model
print("X", x_train.shape, "y", y_train.shape)
model.fit(x_train, y_train,
          batch_size=BATCH_SIZE,
          epochs=NUM_EPOCHS,
          shuffle = True,
          verbose=1,
          validation_split = 0.1,
          class_weight = class_weights)
          #validation_data=(x_test, y_test))
#score = model.evaluate(x_test, y_test, verbose=0)
#print('Test loss:', score[0])
#print('Test accuracy:', score[1])
'''model.fit_generator(train_datagen.flow(x_train, y_train, batch_size=BATCH_SIZE),
                    steps_per_epoch=25000, epochs=NUM_EPOCHS, verbose=1)'''


y_submit = model.predict_classes(x_test)
print(y_submit.shape)
print(sum(y_submit))

#image_filenames=[]
prediction_test_dir = "predictions_test/"
for i in range(1,TESTING_SIZE+1):
    test_data_filename = data_dir + 'test_set_images'

    oimg = get_prediction_with_overlay(test_data_filename, i, 'test', model, IMG_PATCH_SIZE, PIXEL_DEPTH)
    oimg.save(prediction_test_dir + "overlay_" + str(i) + ".png")

    filename = prediction_test_dir + "predictimg_" + str(i) + ".png"
    imgpred = get_predictionimage(test_data_filename, i, 'test', model, IMG_PATCH_SIZE, PIXEL_DEPTH)
    imgpred.save(filename)
    #print(filename)
    #image_filenames.append(filename)


#submission_filename = 'keras_submission'
#pred_to_submission(submission_filename,*image_filenames)    

# Make submission file
prediction_to_submission('submission_keras.csv', y_submit)







