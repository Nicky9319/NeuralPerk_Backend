import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os
from matplotlib import pyplot as plt
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import ResNet50V2
from tensorflow.keras import Model
from tensorflow.keras import Input
from tensorflow.keras.layers import GlobalAveragePooling2D, BatchNormalization, Dropout, Dense
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn import metrics

import keras

import requests

import json
import time

import NeuralPerk as npe


print(tf.config.list_physical_devices('GPU'))


tf_man = npe.Tensorflow_Manager()


import tensorflow as tf
from keras.preprocessing.image import ImageDataGenerator
from keras.applications import ResNet50V2
from keras import Model
from keras import Input
from keras.layers import GlobalAveragePooling2D, BatchNormalization, Dropout, Dense
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn import metrics


NUM_CLASSES = 38
IMAGE_SIZE = 256


base_model = ResNet50V2(input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3), include_top=False)
base_model.trainable = False


inputs = Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3))
base = base_model(inputs)
base = GlobalAveragePooling2D()(base)
base = Dropout(0.2)(base)
base = BatchNormalization()(base)
base = Dropout(0.5)(base)
output = Dense(NUM_CLASSES, activation="softmax")(base)

model = Model(inputs, output)

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense



# img_size = (150 , 150)

# model = Sequential([
#     Conv2D(32, (3, 3), activation='relu', input_shape=(img_size[0], img_size[1], 3)),
#     MaxPooling2D(pool_size=(2, 2)),
#     Conv2D(64, (3, 3), activation='relu'),
#     MaxPooling2D(pool_size=(2, 2)),
#     Conv2D(128, (3, 3), activation='relu'),
#     MaxPooling2D(pool_size=(2, 2)),
#     Flatten(),
#     Dense(128, activation='relu'),
#     Dense(1, activation='sigmoid')
# ])


# model.compile(optimizer='adam',
#               loss='binary_crossentropy',
#               metrics=['accuracy'])


def getDataset():
    dataPath = "C:/Users/paart/OneDrive/Documents/Paarth Workshop/Start-Up/Deep Logic/Distributed AI Testing/AIMS Plant Disease/ValiditySet"
    NUM_CLASSES = 38
    IMAGE_SIZE = 256

    train_augmentation = ImageDataGenerator(
        rescale=1/255.,
        rotation_range=15,
        shear_range=0.3,
        zoom_range=0.2,
        vertical_flip=True,
        horizontal_flip=True,
        validation_split=0.15,
    )

    test_augmentation = ImageDataGenerator(
        rescale=1/255.,
        rotation_range=15,
        shear_range=0.3,
        zoom_range=0.2,
        vertical_flip=True,
        horizontal_flip=True,
    )

    training_dataset = train_augmentation.flow_from_directory(dataPath, target_size=(IMAGE_SIZE, IMAGE_SIZE), batch_size=32, class_mode="categorical", shuffle=True)
    return training_dataset



# model = tf_man.loadModel()
# model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])


# model.evaluate(getDataset())



tf_man.InformationTransfer(model = model , epochs = 10)
tf_man.initiateSessionRequest()


localHost = 'http://127.0.0.1:5500'
ubuntuHost = 'http://192.168.0.125:5500'

serverHost = 'http://64.227.139.68:5500'

response = requests.post(f"{serverHost}/initializeSession" , json = {"EMAIL" : "paarthsaxena2005@gmail.com"})
print(response.text)

