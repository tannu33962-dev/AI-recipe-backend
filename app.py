from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import requests
from datetime import datetime


# Load environment variables from .env
load_dotenv()

# MongoDB config from .env
mongo_uri = os.getenv("MONGO_URI")
dbname = os.getenv("DB_NAME")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# App setup
app = Flask(__name__)
CORS(app)
client = MongoClient(mongo_uri)
db = client[dbname]
users_collection = db["users"]
history_collection = db["history"]



def generate_recipe(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "You are a professional chef and cooking assistant AI. "
                            "You help users come up with delicious and practical recipes based on their ingredients. "
                            "Format your responses clearly with recipe names and short instructions.\n\n"
                            f"Suggest some recipes I can make using these ingredients: {prompt}."
                        )
                    }
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, params=params, json=data)

    if response.status_code == 200:
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    else:
        print("Gemini API Status:", response.status_code)
        print("Gemini Response:", response.text)
        return "Sorry, I couldn't generate a recipe at the moment."

@app.route("/generate-recipe", methods=["POST"])
def recipe():
    data = request.json
    ingredients = data.get("ingredients", "")
    prompt = f"Suggest some recipes I can make using these ingredients: {ingredients}."
    result = generate_recipe(prompt)
    return jsonify({"recipe": result})




@app.route('/api/get_history', methods=['POST'])
def get_history():
    data = request.json
    email = data.get('email')

    # Look for the user document in the history collection
    user_history = history_collection.find_one({'email': email}, {'_id': 0, 'history': 1})

    if not user_history or 'history' not in user_history:
        return jsonify([])  # Return empty list if no history found

    return jsonify(user_history['history'][::-1])





@app.route('/api/save_history', methods=['POST'])
def save_history():
    data = request.json
    email = data.get('email')
    prompt = data.get('prompt')
    response = data.get('response')
    
    if not email or not prompt or not response:
        return jsonify({"error": "Missing fields"}), 400
    
    timestamp = datetime.utcnow().isoformat()

    new_entry = {
        "prompt": prompt,
        "response": response,
        "timestamp": timestamp
    }

    # ✅ Corrected: Use collection, not db
    existing = history_collection.find_one({"email": email})
    
    if existing:
        # ✅ Append new entry to existing history
        history_collection.update_one(
            {"email": email},
            {"$push": {"history": new_entry}}
        )
    else:
        # ✅ Create new document with history array
        history_collection.insert_one({
            "email": email,
            "history": [new_entry]
        })
    
    return jsonify({"message": "History saved successfully."}), 200



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
        return jsonify({"success": True, "message": "Login successful!", "email": email})

    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/')
def home():
    return 'Backend is working!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
