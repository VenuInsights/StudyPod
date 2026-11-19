
from core.database import get_database

try:
    db = get_database()

    print("MongoDB connection successful!")
    print("Connected database:", db.name)

except Exception as e:
    print("MongoDB connection failed.")
    print("Error:", e)
