import socket
import threading
import time
import pickle
import random

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.image import ImageDataGenerator

import numpy as np 
import pandas as pd 
from matplotlib import pyplot as plt
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import ResNet50V2
from tensorflow.keras import Model
from tensorflow.keras import Input
from tensorflow.keras.layers import GlobalAveragePooling2D, BatchNormalization, Dropout, Dense
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras import backend as K
from sklearn import metrics

from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import BatchNormalization
from keras.callbacks import ModelCheckpoint
from keras.layers import ReLU
from keras.models import Sequential
from keras.layers import Dropout
from keras.layers import Flatten
from keras.layers import Dense , Input
from keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from keras.optimizers import RMSprop
from keras.callbacks import ReduceLROnPlateau, EarlyStopping
from keras.models import load_model

import socketio



sio = socketio.Client()

@sio.event
def connect():
    print("I'm connected!")

@sio.event
def disconnect():
    print("I'm disconnected!")

@sio.on("response")
def response(data):
    print(data)





def parserMessage(message):
    msgType = message["TYPE"]
    pass

@sio.event
def message(data):
    print('Message received from server: ', data)
    parserMessage(data)






def getDataset(customerIdentifier):
    pass
    


def copyModel(oriModel , newModel):
    length = len(oriModel.layers)
    for ind in range(length):
        newModel.layers[ind].set_weights(oriModel.layers[ind].get_weights())

def calculateGrads(newModel , oldModel):
    newLayer = newModel.layers
    oldLayer = oldModel.layers
    
    gradModel = keras.models.model_from_json(newModel.to_json())

    length = len(gradModel.layers)
    for layerInd in range(length):
        updated_params = []
        oldParams = oldLayer[layerInd].get_weights()
        newParams = newLayer[layerInd].get_weights()
        for par in range(len(newLayer[layerInd].get_weights())):
            delta = oldParams[par] - newParams[par]
            updated_params.append(delta)
        gradModel.layers[layerInd].set_weights(updated_params)
    
    #printModel(gradModel)
    return gradModel



def handleTraining(modelInfo):
    global model
    global epochs
    global sio 
    global customerIdentifier
    model.compile(optimizer="adam" , loss="categorical_crossentropy", metrics=["accuracy", "top_k_categorical_accuracy"])

    es_callback = EarlyStopping(patience=3, verbose=1)
    reduce_lr_callback = ReduceLROnPlateau(factor=0.2, patience=2, verbose=1, min_lr=0.00035)
    prevModel = keras.models.model_from_json(model.to_json())
    
    copyModel(model , prevModel)
    for epoch_number in range(epochs):
        print("Working on Epoch Number : " , epoch_number)
        model.fit(getDataset(customerIdentifier), epochs = 1, callbacks=[es_callback , reduce_lr_callback] , verbose = 1)
        grads = calculateGrads(model , prevModel)
        print("Sending Model back to Server !!")
        msg = {"TYPE" : "MODEL_GRADS" , "DATA" : model.get_weights() , "TIME" : time.time()}
        sio.emit("USER_MESSAGE" , msg)
        modelUpdate.wait()
        if modelUpdate.is_set():
            copyModel(model , prevModel)
        modelUpdate.clear()



# def write():
#     while True:
#         msg = {"message" : input() , "TIME" : time.time()}
#         msg = str(msg)
#         sio.emit('USER_MESSAGE' , msg)


if __name__ == "__main__":
    print(tf.config.list_physical_devices('GPU'))

    modelUpdate = threading.Event()
    model = None
    epochs = None

    # write_thread = threading.Thread(target=write)
    # write_thread.start()

    sio.connect('http://127.0.0.1:7777')
    sio.wait()

