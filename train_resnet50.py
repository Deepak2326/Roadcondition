import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras import layers, models
import numpy as np
import os
import cv2
from sklearn.model_selection import train_test_split

# Load dataset
def load_data(dataset_path):
    images, labels = [], []
    categories = ["minor", "moderate", "major"]
    
    for label, category in enumerate(categories):
        category_path = os.path.join(dataset_path, category)
        for img_name in os.listdir(category_path):
            img_path = os.path.join(category_path, img_name)
            img = cv2.imread(img_path)
            img = cv2.resize(img, (224, 224)) / 255.0  # Resize & Normalize
            images.append(img)
            labels.append(label)
    
    return np.array(images), np.array(labels)

# Load dataset
dataset_path = "dataset/"  # Change this to your dataset path
X, y = load_data(dataset_path)

# Split dataset (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Load Pretrained ResNet50
base_model = ResNet50(input_shape=(224, 224, 3), include_top=False, weights="imagenet")
base_model.trainable = False  # Freeze pretrained layers

# Build Model
model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation="relu"),
    layers.Dense(3, activation="softmax")  # 3 categories: minor, moderate, major
])

# Compile Model
model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

# Train Model (Only 5-10 mins on GPU)
model.fit(X_train, y_train, epochs=5, validation_data=(X_test, y_test))

# Save Model
os.makedirs("model", exist_ok=True)
model.save("model/road_damage_resnet50.h5")
print("✅ ResNet50 Model saved successfully!")
