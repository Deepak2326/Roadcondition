from flask import Flask, request, jsonify, send_from_directory
import os
import numpy as np
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import tensorflow as tf
import cv2
import uuid
import sqlite3
import jwt
import bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow frontend requests

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MODEL_PATH = 'model/road_damage_resnet50.h5'  # ResNet50 model path
DATABASE_PATH = 'database/road_damage.db'
SECRET_KEY = "your_secret_key_here"  # Change this for production

# Create necessary directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['SECRET_KEY'] = SECRET_KEY

# Load the trained ResNet50 model
model = None
if os.path.exists(MODEL_PATH):
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        print("✅ ResNet50 Model loaded successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not load model. {str(e)}")
        print("API will start but classification functionality will be disabled")
else:
    print("⚠️ Warning: Model file not found! Please train or place the model in 'model/' directory.")

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        category TEXT NOT NULL,
        confidence REAL
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_token(username):
    payload = {"username": username, "exp": datetime.utcnow() + timedelta(days=1)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["username"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Image Classification Function for ResNet50
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224)) / 255.0
    return np.expand_dims(img, axis=0)

def classify_damage(image_path):
    if model is None:
        return "unknown", 0.0
    processed_img = preprocess_image(image_path)
    prediction = model.predict(processed_img)[0]
    category_index = np.argmax(prediction)
    categories = ["minor", "moderate", "major"]
    return categories[category_index], float(prediction[category_index])

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    username, password = data.get("username"), data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    username, password = data.get("username"), data.get("password")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password(user[0], password):
        return jsonify({"token": generate_token(username)}), 200
    return jsonify({"error": "Invalid username or password"}), 401

# Image Upload & Classification Route
@app.route('/api/upload', methods=['POST'])
def upload_file():
    token = request.headers.get('Authorization')
    if not token or not verify_token(token.split(" ")[-1]):
        return jsonify({"error": "Unauthorized"}), 401
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename.strip() == "" or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    image_id, filename = str(uuid.uuid4()), secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    category, confidence = classify_damage(file_path)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO images (id, filename, upload_date, category, confidence) VALUES (?, ?, ?, ?, ?)", (image_id, filename, datetime.now().isoformat(), category, confidence))
    conn.commit()
    conn.close()
    return jsonify({'id': image_id, 'filename': filename, 'category': category, 'confidence': confidence}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
