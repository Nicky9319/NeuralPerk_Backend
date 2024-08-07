from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense

import copy

model = Sequential()

# Add the first convolutional layer
model.add(Conv2D(512, (3, 3), activation='relu', input_shape=(64, 64, 3)))

# Add a pooling layer
model.add(MaxPooling2D(pool_size=(2, 2)))

# Add another convolutional layer
model.add(Conv2D(512, (3, 3), activation='relu'))

# Add another pooling layer
model.add(MaxPooling2D(pool_size=(2, 2)))

# Flatten the tensor output from the previous layer
model.add(Flatten())

# Add a fully connected layer
model.add(Dense(units=250, activation='relu'))

# Add the output layer
model.add(Dense(units=10, activation='softmax'))

# Compile the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Print the model summary
model.summary()


st = model.to_json()

import time

t1 = time.time()
new_st = copy.deepcopy(st)
t2 = time.time()
print(t2 - t1)
