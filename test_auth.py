
from core.auth import register_user, login_user

print("STUDYPOD AUTHENTICATION TEST")

# Register a test user
success, message, user = register_user(
    username="TestStudent",
    email="teststudent@example.com",
    password="StudyPod123"
)

print("\nRegistration:", message)

# Try logging in
success, message, user = login_user(
    email="teststudent@example.com",
    password="StudyPod123"
)

print("Login:", message)

if success:
    print("Logged-in user:", user["username"])
    print("Test user ID:", user["id"])

# Try logging in with an incorrect password
success, message, user = login_user(
    email="teststudent@example.com",
    password="WrongPassword123"
)

print("Incorrect password test:", message)
