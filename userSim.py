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



import asyncio
import websockets
import threading
import pickle
import numpy as np








sio = socketio.Client()




def sendInBuffer(data):
    chunk_size = 1024*1024
    for i in range(0, len(data), chunk_size):
        try:
            sio.emit('message_in_batches', data[i:i+chunk_size])
        except:
            print("Error in Sending Data")
            break
    
@sio.event
def connect():
    print("I'm connected!")

@sio.event
def disconnect():
    print("I'm disconnected!")


@sio.on('response')
def on_response(data):
    print("Response")
    msg = pickle.loads(data)
    print(msg)
    parserMessage(msg)


@sio.on('message')
def on_message(data):
    print(f"Length of Message Received : {len(data)}")
    message = pickle.loads(data)
    #print(message)
    parserMessage(message)




# sio = socketio.Client()

# @sio.event
# def connect():
#     print("I'm connected!")

# @sio.event
# def disconnect():
#     print("I'm disconnected!")

# @sio.on("response")
# def response(data):
#     print("data")







def informationTransferTime(startTime , note):
    t1 = startTime
    t2 = time.time()
    print("\n-------------------------------\n")
    print("Note : " , note)
    print("Total Time Taken : " , t2 - t1)
    print("\n-------------------------------\n")

def setupModel(setupInfo):
    global model
    global compilationInfo
    global customerIdentifier
    global userClusterSize
    global epochs

    data = setupInfo["DATA"]
    customerIdentifier = setupInfo["CUSTOMER"]
    userClusterSize = setupInfo["TOTAL_USERS"]
    epochs = setupInfo["EPOCHS"]

    model = keras.models.model_from_json(data["MODEL_JSON"])
    compilationInfo = {"OPTIMIZER_CONFIG" : data["OPTIMIZER_CONFIG"] ,"LOSS" : data["LOSS"] , "METRICS" : data["METRICS"] , "LOSS_WEIGHTS" : data["LOSS_WEIGHTS"] , "WEIGHTED_METRICS" : data["WEIGHTED_METRICS"]}
    informationTransferTime(setupInfo["TIME"] , "Time Taken to Transfer the Setup Model Information")
    print("Model Setup Completed !!!")


def preSetupAndTraining(data):
    global model
    model.set_weights(data["DATA"])
    informationTransferTime(data["TIME"] , "Time Taken to transfer the initial Values of the Weights of the Model")
    training_thread = threading.Thread(target = handleTraining)
    training_thread.start()

    

def updateModel(data):
    global model
    global modelUpdate
    model.set_weights(data["DATA"])
    modelUpdate.set()
    informationTransferTime(data["TIME"] , "Time Taken to Transfer the Updated Model Params")

def parserMessage(message):
    msgType = message["TYPE"]
    if msgType == "MODEL_SETUP":
        setupModel(message)
    elif msgType == "TRAIN":
        preSetupAndTraining(message)
    elif msgType == "UPDATED_MODEL":
        updateModel(message)

# @sio.event
# def message(data):
#     print('Message received from server !!!')
#     parserMessage(data)






def getDataset(customerIdentifier):
    if customerIdentifier == "paarthsaxena2005@gmail.com":
        dataPath = "C:/Users/paart/OneDrive/Documents/Paarth Workshop/Start-Up/Deep Logic/Distributed AI Testing/AIMS Plant Disease/TrainingSet"
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
    else:
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



def handleTraining():
    global model
    global epochs
    global sio 
    global customerIdentifier
    global compilationInfo

    model.compile(optimizer="Adam" , loss=compilationInfo["LOSS"], metrics=compilationInfo["METRICS"] , loss_weights = compilationInfo["LOSS_WEIGHTS"] , weighted_metrics = compilationInfo["WEIGHTED_METRICS"])
    model.optimizer = tf.keras.optimizers.deserialize(compilationInfo["OPTIMIZER_CONFIG"])

    prevModel = keras.models.model_from_json(model.to_json())
    
    copyModel(model , prevModel)
    for epoch_number in range(epochs):
        print("Working on Epoch Number : " , epoch_number)
        model.fit(getDataset(customerIdentifier), epochs = 1, verbose = 1)
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


# if __name__ == "__main__":
#     print(tf.config.list_physical_devices('GPU'))

#     modelUpdate = threading.Event()
#     model = None
#     epochs = None
#     userClusterSize = None
#     customerIdentifier = None
#     compilationInfo = None

#     # write_thread = threading.Thread(target=write)
#     # write_thread.start()

#     sio.connect('http://127.0.0.1:6000')
#     sio.wait()


if __name__ == "__main__":
    print(tf.config.list_physical_devices('GPU'))

    modelUpdate = threading.Event()
    model = None
    epochs = None
    userClusterSize = None
    customerIdentifier = None
    compilationInfo = None

    sio.connect('http://localhost:6000')
    sio.wait()

    print("Client is Closing")