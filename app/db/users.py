""" Database operations for users. """

from typing import Optional
from bson import ObjectId
import bcrypt
from app.db import DB
from app.db.constants import USER_COLLECTION


def _user_to_dict(user) -> Optional[dict]:
    """Convert a MongoDB document to a JSON-serializable dict (no password)."""
    if user is None:
        return None
    user['id'] = str(user['_id'])
    del user['_id']
    del user['password']
    return user


def get_user_by_email(email: str) -> Optional[dict]:
    """Retrieve a user by email. Does NOT include password hash."""
    col = DB.get_collection(USER_COLLECTION)
    user = col.find_one({'email': email.strip().lower()})
    return _user_to_dict(user)


def get_user_for_login(email: str) -> Optional[dict]:
    """
    Retrieve a user by email INCLUDING the password hash.
    """
    col = DB.get_collection(USER_COLLECTION)
    user = col.find_one({'email': email.strip().lower()})
    if user is None:
        return None
    user['id'] = str(user['_id'])
    del user['_id']
    return user  


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify a provided password against a stored bcrypt hash."""
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash.encode('utf-8'))


def add_user(username: str, email: str, password: str, role: str, phone: str) -> dict:
    """
    Insert a new user into the database. Password will be hashed using bcrypt.

    Args:
        username: Name or handle of the user.
        email:    User email address (must be unique).
        password: Plaintext password (will be hashed).
        role:     User role (e.g., 'admin', 'member', 'trainer').
        phone:    User phone number.

    Returns:
        The newly created user document (without the password hash).
    """
    col = DB.get_collection(USER_COLLECTION)

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    new_user = {
        'username': username.strip(),
        'email': email.strip().lower(),
        'password': hashed_password.decode('utf-8'),
        'role': role.strip().lower(),
        'phone': phone.strip()
    }

    result = col.insert_one(new_user)
    new_user['_id'] = result.inserted_id
    
    return _user_to_dict(new_user)
