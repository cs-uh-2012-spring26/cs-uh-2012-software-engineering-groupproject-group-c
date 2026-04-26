""" Database operations for users. """

from typing import Optional
from bson import ObjectId
import bcrypt
from app.db import DB
from app.db.constants import USER_COLLECTION


def _get_col():
        """Helper to get the MongoDB collection."""
        return DB.get_collection(USER_COLLECTION)

def _fetch_and_format_user(email: str) -> Optional[dict]:
    """ Internal helper: Retrieves user by email and normalizes the MongoDB _id. """
    col = _get_col()
    user = col.find_one({'email': email.strip().lower()})
    
    if user is None:
        return None
        
    user['id'] = str(user.pop('_id'))
    return user

def get_user_for_login(email: str) -> Optional[dict]:
    """Retrieve a user by email INCLUDING the password hash."""
    return _fetch_and_format_user(email)


def get_user_by_email(email: str) -> Optional[dict]:
    """Retrieve a user by email. Does NOT include password hash."""
    user = _fetch_and_format_user(email)
    
    if user and 'password' in user:
        del user['password']
        
    return user


def add_user(new_user: dict) -> dict:
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
    col = _get_col()

    result = col.insert_one(new_user)
    new_user['id'] = str(new_user.pop('_id', result.inserted_id))
    
    if 'password' in new_user:
        del new_user['password']
        
    return new_user



def get_user_preferences(email: str) -> dict:
    """
    Retrieve notification preferences for a user by email.

    Returns:
        Dict with notification_preferences and telegram_chat_id.
    """
    col = _get_col()
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
    col = _get_col()

    update_fields = {'notification_preferences': preferences}
    if telegram_chat_id is not None:
        update_fields['telegram_chat_id'] = telegram_chat_id

    col.update_one(
        {'email': email.strip().lower()},
        {'$set': update_fields}
    )

    return get_user_by_email(email)