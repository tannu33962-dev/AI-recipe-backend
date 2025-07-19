from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# MongoDB config from .env
mongo_uri = os.getenv("MONGO_URI")
dbname = os.getenv("DB_NAME")

# App setup
app = Flask(__name__)
CORS(app)
client = MongoClient(mongo_uri)
db = client[dbname]
users_collection = db["users"]

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if users_collection.find_one({'email': email}):
        return jsonify({'message': 'User already exists'}), 409

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({'email': email, 'password': hashed_password})
    return jsonify({'message': 'Signup successful'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = users_collection.find_one({'email': email})
    if user and check_password_hash(user['password'], password):
        return jsonify({"success": True, "message": "Login successful!"})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/')
def home():
    return 'Backend is working!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
