# import os
# import requests
# import json
# import pickle
# import keras



# jsMsg = json.dumps({"TYPE" : "GET_TRAINED_MODELS" , "EMAIL" : "paarthsaxena2005@gmail.com"})
# response = requests.get(f'http://127.0.0.1:5555/getCustomerData?message={jsMsg}')
# if response.status_code == 200:
#     print(response.json()["DATA"])

# jsMsg = json.dumps({"TYPE" : "GET_MODEL" , "EMAIL" : "paarthsaxena2005@gmail.com" , "MODEL_NAME" : "PlantDisease"})
# response = requests.get(f'http://127.0.0.1:5555/getCustomerData?message={jsMsg}')
# data = pickle.loads(response.content)
# statuscode = response.status_code

# model = keras.models.Model.from_config(data['MODEL_CONFIG'])

# trainedModelList = os.listdir("CustomerData/paarthsaxena2005@gmail.com")
# trainedModelNameList = [model.split(".")[0] for model in trainedModelList]

# print(trainedModelNameList)



import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense

import keras


# Define the CNN model
model = Sequential()
model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(64, 64, 3)))
model.add(MaxPooling2D((2, 2)))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D((2, 2)))
model.add(Conv2D(128, (3, 3), activation='relu'))
model.add(MaxPooling2D((2, 2)))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dense(10, activation='softmax'))

# Compile the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Train the model
newModel = keras.models.load_model("CustomerData/test.h5")

# newModel = keras.models.load_model("test.h5")

