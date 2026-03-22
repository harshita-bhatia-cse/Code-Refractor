# from motor.motor_asyncio import AsyncIOMotorClient

# MONGO_URL = "mongodb://localhost:27017"

# client = AsyncIOMotorClient(MONGO_URL)

# db = client["code_refactorer"]

# users_collection = db["users"]

import sqlite3

conn = sqlite3.connect("app.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id TEXT UNIQUE,
    email TEXT,
    name TEXT,
    avatar TEXT
)
""")

conn.commit()