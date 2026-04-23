import re
import app.db.users as users_db
from flask_jwt_extended import create_access_token
from app.models.roles import UserRole

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password)
    )

def register_user(username, email, password, phone, role):
    """
    Handles the business logic for creating a new user.
    """
    role_val = role.strip().lower()
    
    # 1. Domain Validation
    if not username.strip():
        raise ValueError("username must not be blank.")
        
    if not is_strong_password(password):
        raise ValueError("password must be at least 8 characters long and include an uppercase letter, lowercase letter, and number.")

    if not re.match(r'^\d{10}$', phone):
        raise ValueError("Invalid phone number format. Must be 10 digits.")

    if role_val not in UserRole.values():
        raise ValueError(f"Invalid role. Must be one of: {', '.join(UserRole.values())}")

    # 2. Check existence
    if users_db.get_user_by_email(email):
        raise ValueError("Email already registered")

    # 3. Database Interaction
    new_user = users_db.add_user(
        username=username.strip(),
        email=email.strip(),
        password=password.strip(),
        role=role.strip(),
        phone=phone.strip()
    )
    return new_user

def authenticate_user(email, password):
    """
    Handles logic for verifying credentials and generating tokens.
    """
    user = users_db.get_user_for_login(email)
    
    if user is None or not users_db.verify_password(user['password'], password):
        return None

    token = create_access_token(
        identity=user['email'],
        additional_claims={'role': user['role']}
    )
    
    return {'token': token, 'role': user['role']}