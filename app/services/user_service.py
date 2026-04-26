import re
import app.db.users as users_db
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

def register_user(username, email, password, phone, role,
                  notification_preferences=None, telegram_chat_id=None):
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

    # 2. Validate notification preferences if provided
    if notification_preferences is not None:
        invalid = [p for p in notification_preferences if p not in ALLOWED_CHANNELS]
        if invalid:
            raise ValueError(f"Invalid notification channels: {invalid}. Allowed: {ALLOWED_CHANNELS}")

    # 3. Telegram chat_id required if telegram is in preferences
    if notification_preferences and 'telegram' in notification_preferences:
        if not telegram_chat_id:
            raise ValueError("telegram_chat_id is required when telegram is selected as a notification channel.")

    # 4. Check existence
    if users_db.get_user_by_email(email):
        raise ValueError("Email already registered")

    # 5. Database Interaction
    new_user = users_db.add_user(
        username=username.strip(),
        email=email.strip(),
        password=password.strip(),
        role=role.strip(),
        phone=phone.strip(),
        notification_preferences=notification_preferences,
        telegram_chat_id=telegram_chat_id
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