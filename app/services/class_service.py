from datetime import datetime
import app.db.users as users_db
from app.db import DB
from app.db.classes import ClassRepository
from app.services.email_service import get_class_reminder_template
from app.services.notification_service import NotificationService
from app.services.email_channel import EmailChannel
from app.services.telegram_channel import TelegramChannel

# Initialize the repository instance once
class_repo = ClassRepository(DB)

def date_validation(schedule_str: str):
    try:
        schedule_dt = datetime.fromisoformat(schedule_str)
    except ValueError:
        raise ValueError('Invalid schedule format. Must be ISO 8601 string (e.g., 2026-03-10T08:00).')

    if schedule_dt < datetime.now():
        return False
    else:
        return True


notification_service = NotificationService([
    EmailChannel(),
    TelegramChannel(),
])


def get_public_classes():
    """
    Fetches all classes using class_repo and filters internal state.
    """
    raw_classes = class_repo.get_all_classes()

    return [{
        "id": c.get("id"),
        "name": c.get("name"),
        "instructor": c.get("instructor"),
        "schedule": c.get("schedule"),
        "capacity": c.get("capacity"),
        "enrolled": c.get("enrolled"),
        "location": c.get("location"),
        "description": c.get("description")
    } for c in raw_classes]


def create_class(name: str, instructor: str, schedule: str, capacity: int, location: str, description: str = ''):
    """
    Validates and creates a new fitness class via the repository.
    """

    if not isinstance(capacity, int) or capacity <= 0:
        raise ValueError('Capacity must be a positive integer.')


    if not date_validation(schedule):
        raise ValueError('Schedule must be a future date and time')

    return class_repo.add_class(
        name=name.strip(),
        instructor=instructor.strip(),
        schedule=schedule.strip(),
        capacity=capacity,
        location=location.strip(),
        description=description.strip()
    )


def book_class_for_member(class_id: str, member_email: str):
    """
    Handles business logic for booking.
    """
    cls = class_repo.get_class_by_id(class_id)
    if cls is None:
        raise ValueError("Class not found.")
    
    if not date_validation(cls.get('schedule', '')):
        raise ValueError("Cannot book a class that has already ended.")

    return class_repo.book_class(class_id, member_email)


def get_class_members(class_id: str):
    """
    Retrieves the list of members for a specific class.
    """
    members = class_repo.get_booked_members(class_id)

    return members


def send_class_reminders(class_id: str):
    """
    Orchestrates the reminder process using the Strategy Pattern.
    Dispatches notifications to each member based on their preferences.
    """
    cls = class_repo.get_class_by_id(class_id)
    if cls is None:
        raise ValueError("Class not found.")

    members = cls.get('booked_members', [])
    if not members:
        raise ValueError("No booked members for this class.")

    if not date_validation(cls.get('schedule', '')):
        raise ValueError("Cannot send reminders for a class that has already ended.")

    # Build subject and body once for all members
    subject, body = get_class_reminder_template(cls)

    all_sent = []
    all_failed = []

    for member_email in members:
        # Look up this member's notification preferences
        prefs = users_db.get_user_preferences(member_email)
        preferences = prefs.get('notification_preferences', ['email'])
        telegram_chat_id = prefs.get('telegram_chat_id')

        results = notification_service.notify(
            to=member_email,
            subject=subject,
            body=body,
            preferences=preferences,
            telegram_chat_id=telegram_chat_id
        )

        all_sent.extend(results['sent'])
        all_failed.extend(results['failed'])

    return {
        'total_sent': len(all_sent),
        'total_failed': len(all_failed),
        'sent_list': all_sent,
        'failed_list': all_failed
    }