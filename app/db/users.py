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


def add_user(username: str, email: str, password: str, role: str,
             phone: str, notification_preferences: list = None,
             telegram_chat_id: str = None) -> dict:
    """
    Insert a new user into the database. Password will be hashed using bcrypt.

    Args:
        username:                 Name or handle of the user.
        email:                    User email address (must be unique).
        password:                 Plaintext password (will be hashed).
        role:                     User role (e.g., 'admin', 'member', 'trainer').
        phone:                    User phone number.
        notification_preferences: List of preferred channels, defaults to ['email'].
        telegram_chat_id:         Optional Telegram chat_id for Telegram notifications.

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
        'phone': phone.strip(),
        'notification_preferences': notification_preferences or ['email'],
        'telegram_chat_id': telegram_chat_id or None,
    }

    result = col.insert_one(new_user)
    new_user['_id'] = result.inserted_id

    return _user_to_dict(new_user)


def get_user_preferences(email: str) -> dict:
    """
    Retrieve notification preferences for a user by email.

    Returns:
        Dict with notification_preferences and telegram_chat_id.
    """
    col = DB.get_collection(USER_COLLECTION)
    user = col.find_one(
        {'email': email.strip().lower()},
        {'notification_preferences': 1, 'telegram_chat_id': 1}
    )
    if user is None:
        return {'notification_preferences': ['email'], 'telegram_chat_id': None}

    return {
        'notification_preferences': user.get('notification_preferences', ['email']),
        'telegram_chat_id': user.get('telegram_chat_id', None)
    }


def update_notification_preferences(email: str, preferences: list,
                                    telegram_chat_id: str = None) -> dict:
    """
    Update a user's notification preferences.

    Args:
        email:            User's email address.
        preferences:      List of channel names e.g. ['email', 'telegram'].
        telegram_chat_id: Optional Telegram chat_id.

    Returns:
        Updated user document.
    """
    col = DB.get_collection(USER_COLLECTION)

    update_fields = {'notification_preferences': preferences}
    if telegram_chat_id is not None:
        update_fields['telegram_chat_id'] = telegram_chat_id

    col.update_one(
        {'email': email.strip().lower()},
        {'$set': update_fields}
    )

    return get_user_by_email(email)