
import re
import bcrypt

from pymongo.errors import DuplicateKeyError
from core.database import get_database


def get_users_collection():
    db = get_database()
    users = db["users"]

    # Ensure email addresses are unique
    users.create_index("email", unique=True)

    return users


def register_user(username, email, password):

    username = username.strip()
    email = email.strip().lower()

    # Basic validation
    if not username or not email or not password:
        return False, "All fields are required.", None

    if len(username) < 3:
        return False, "Username must contain at least 3 characters.", None

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Please enter a valid email address.", None

    if len(password.encode("utf-8")) > 72:
        return False, "Password must not exceed 72 bytes.", None

    if len(password) < 8:
        return False, "Password must contain at least 8 characters.", None

    # Hash password before storing it
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    user = {
        "username": username,
        "email": email,
        "password_hash": password_hash
    }

    try:
        users = get_users_collection()
        result = users.insert_one(user)

        return True, "Registration successful!", {
            "id": str(result.inserted_id),
            "username": username,
            "email": email
        }

    except DuplicateKeyError:
        return False, "An account with this email already exists.", None

    except Exception:
        return False, "Registration failed. Please try again.", None


def login_user(email, password):

    email = email.strip().lower()

    if not email or not password:
        return False, "Please enter your email and password.", None

    try:
        users = get_users_collection()

        user = users.find_one({"email": email})

        if not user:
            return False, "Invalid email or password.", None

        password_matches = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        )

        if not password_matches:
            return False, "Invalid email or password.", None

        return True, "Login successful!", {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }

    except Exception:
        return False, "Login failed. Please try again.", None
