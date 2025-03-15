import tensorflow as tf
import numpy as np
import cv2
import os

# Load trained model
MODEL_PATH = "model/road_damage_resnet50.h5"
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("❌ Model file not found! Train the model first.")

model = tf.keras.models.load_model(MODEL_PATH)
print("✅ Model loaded successfully!")

# Define categories
CATEGORIES = ["minor", "moderate", "major"]

def preprocess_image(image_path):
    """Preprocess image for ResNet50 prediction."""
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224)) / 255.0  # Resize & Normalize
    return np.expand_dims(img, axis=0)

# Test on a new image
test_image_path = "test_images/potholes28_png.rf.439bc5a8a927f466fdb66a6e91064353.jpg"  # Change this to your test image
if not os.path.exists(test_image_path):
    raise FileNotFoundError("❌ Test image not found! Add an image in 'test_images/' folder.")

processed_img = preprocess_image(test_image_path)
prediction = model.predict(processed_img)[0]
category_index = np.argmax(prediction)
confidence = float(prediction[category_index])

print(f"🔹 Predicted Category: {CATEGORIES[category_index]} ({confidence * 100:.2f}%)")
