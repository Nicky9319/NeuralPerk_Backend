import tensorflow as tf

# Define the CNN model
model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')
])

# Compile the model

optimizer_config = {'class_name': 'Adam', 'config': {'name': 'Adam', 'learning_rate': 0.001, 'decay': 0.0, 'beta_1': 0.3, 'beta_2': 0.999, 'epsilon': 1e-07, 'amsgrad': False}}

# optimizer = tf.keras.optimizers.get(optimizer_config['name'])(**optimizer_config)
model.compile(optimizer="ADAM", loss='sparse_categorical_crossentropy', metrics=['accuracy'])

print()
print(model.optimizer.get_config())

# val = tf.keras.optimizers.serialize(model.optimizer)
model.optimizer = tf.keras.optimizers.deserialize(optimizer_config)

print(model.optimizer.get_config())


# {'class_name': 'Adam', 'config': {'name': 'Adam', 'learning_rate': 0.001, 'decay': 0.0, 'beta_1': 0.3, 'beta_2': 0.999, 'epsilon': 1e-07, 'amsgrad': False}}
