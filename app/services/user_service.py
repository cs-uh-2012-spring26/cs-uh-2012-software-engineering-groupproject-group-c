import re
import app.db.users as users_db
import bcrypt
from flask_jwt_extended import create_access_token
from app.models.roles import UserRole

ALLOWED_CHANNELS = ['email', 'telegram']

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password)
    )

def validate_user_data(password, phone, role, email, notification_preferences=None, telegram_chat_id=None):
    if not is_strong_password(password):
        raise ValueError("password must be at least 8 characters long and include an uppercase letter, lowercase letter, and number.")

    if not re.match(r'^\d{10}$', phone):
        raise ValueError("Invalid phone number format. Must be 10 digits.")

    if role not in UserRole.values():
        raise ValueError(f"Invalid role. Must be one of: {', '.join(UserRole.values())}")
    
    if users_db.get_user_by_email(email):
        raise ValueError("Email already registered")
    
    if notification_preferences is not None:
        invalid = [p for p in notification_preferences if p not in ALLOWED_CHANNELS]
        if invalid:
            raise ValueError(f"Invalid notification channels: {invalid}. Allowed: {ALLOWED_CHANNELS}")

    if notification_preferences and 'telegram' in notification_preferences:
        if not telegram_chat_id:
            raise ValueError("telegram_chat_id is required when telegram is selected as a notification channel.")
    

def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify a provided password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        provided_password.encode('utf-8'), 
        stored_hash.encode('utf-8')
    )


def register_user(username, email, password, phone, role,
                  notification_preferences=None, telegram_chat_id=None):
    """
    Handles the business logic for creating a new user.
    """
    
    new_user = {
        'username': username.strip(),
        'email': email.strip(),
        'password': password.strip(),
        'phone': phone.strip(),
        'role': role.strip().lower(),
        'notification_preferences': notification_preferences or ['email'],
        'telegram_chat_id': telegram_chat_id.strip() if telegram_chat_id else None
    }
    
    validate_user_data(new_user['password'], new_user['phone'], new_user['role'], new_user['email'], new_user['notification_preferences'], new_user['telegram_chat_id'])    

    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(new_user['password'].encode('utf-8'), salt)
    new_user['password'] = hashed_password_bytes.decode('utf-8')         
    updated_new_user = users_db.add_user(new_user)

    return updated_new_user


def authenticate_user(email, password):
    """
    Handles logic for verifying credentials and generating tokens.
    """
    user = users_db.get_user_for_login(email)

    if user is None or not verify_password(user['password'], password):
        return None

    token = create_access_token(
        identity=user['email'],
        additional_claims={'role': user['role']}
    )

    return {'token': token, 'role': user['role']}


def update_user_preferences(email: str, preferences: list,
                            telegram_chat_id: str = None) -> dict:
    """
    Updates notification preferences for a user.

    Args:
        email:            User's email address.
        preferences:      List of channel names e.g. ['email', 'telegram'].
        telegram_chat_id: Optional Telegram chat_id.

    Returns:
        Updated user document.

    Raises:
        ValueError: If preferences contain invalid channels or
                    telegram_chat_id is missing for telegram.
    """
    # Validate channels
    invalid = [p for p in preferences if p not in ALLOWED_CHANNELS]
    if invalid:
        raise ValueError(f"Invalid notification channels: {invalid}. Allowed: {ALLOWED_CHANNELS}")

    # Telegram requires chat_id
    if 'telegram' in preferences and not telegram_chat_id:
        raise ValueError("telegram_chat_id is required when telegram is selected.")

    return users_db.update_notification_preferences(
        email=email,
        preferences=preferences,
        telegram_chat_id=telegram_chat_id
    )