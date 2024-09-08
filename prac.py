# import tensorflow as tf
# from keras.layers import Conv2D, BatchNormalization, ReLU, Add, GlobalAveragePooling2D, Dense, Input , MaxPooling2D, Flatten
# from keras.models import Model
# import json

# from keras.preprocessing.image import ImageDataGenerator



# from keras.preprocessing.image import ImageDataGenerator
# from keras.applications import ResNet50V2
# from keras import Model
# from keras import Input
# from keras.layers import GlobalAveragePooling2D, BatchNormalization, Dropout, Dense
# from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
# from sklearn import metrics


# NUM_CLASSES = 38
# IMAGE_SIZE = 256




# model = tf.keras.Sequential([
#     Conv2D(32, (3, 3), activation='relu', input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3)),
#     MaxPooling2D((2, 2)),
#     Conv2D(64, (3, 3), activation='relu'),
#     MaxPooling2D((2, 2)),
#     Conv2D(128, (3, 3), activation='relu'),
#     MaxPooling2D((2, 2)),
#     Flatten(),
#     Dense(128, activation='relu'),
#     Dense(NUM_CLASSES, activation='softmax')
# ])


# # base_model = ResNet50V2(input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3), include_top=False)
# # base_model.trainable = False


# # inputs = Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3))
# # base = base_model(inputs)
# # base = GlobalAveragePooling2D()(base)
# # base = Dropout(0.2)(base)
# # base = BatchNormalization()(base)
# # base = Dropout(0.5)(base)
# # output = Dense(NUM_CLASSES, activation="softmax")(base)

# # model = Model(inputs, output)

# model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])


dict = {1 : 'a', 2 : 'b', 3 : 'c'}
print(dict)
del dict[1]
print(dict)