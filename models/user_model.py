from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db.users

def create_user(user_data):
    existing = users.find_one({"email": user_data["email"]})
    if existing:
        return None
    users.insert_one(user_data)
    return user_data

def find_user(email, password):
    return users.find_one({"email": email, "password": password})



