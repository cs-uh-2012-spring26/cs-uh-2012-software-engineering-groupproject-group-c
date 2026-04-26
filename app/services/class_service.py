"""
Business logic for fitness classes, including recurrence support.
"""

from datetime import datetime
import app.db.users as users_db
from app.db import DB
from app.db.classes import ClassRepository
from app.services.email_service import get_class_reminder_template
from app.services.notification_service import NotificationService
from app.services.email_channel import EmailChannel
from app.services.telegram_channel import TelegramChannel
from app.services import recurrence_service

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
    Fetches all classes and expands recurring classes into individual
    occurrence entries for public display. Non-recurring classes are
    returned as-is.
    """
    raw_classes = class_repo.get_all_classes()
    result = []

    for c in raw_classes:
        base = {
            "id": c.get("id"),
            "name": c.get("name"),
            "instructor": c.get("instructor"),
            "capacity": c.get("capacity"),
            "enrolled": c.get("enrolled"),
            "location": c.get("location"),
            "description": c.get("description"),
        }

        recurrence = c.get("recurrence")
        if recurrence:
            # Include the recurrence rule metadata once
            base["recurrence"] = recurrence
            occurrences = recurrence_service.get_occurrences(c)
            for occ in occurrences:
                entry = dict(base)
                entry["schedule"] = c.get("schedule")
                entry["occurrence_date"] = occ.isoformat()
                result.append(entry)
        else:
            base["schedule"] = c.get("schedule")
            result.append(base)

    return result


def create_class(name: str, instructor: str, schedule: str, capacity: int,
                 location: str, description: str = '',
                 recurrence: dict = None):
    """
    Validates and creates a new fitness class via the repository.
    Optionally attaches a recurrence rule.
    """
    if not isinstance(capacity, int) or capacity <= 0:
        raise ValueError('Capacity must be a positive integer.')

    if not date_validation(schedule):
        raise ValueError('Schedule must be a future date and time')

    # Validate and build recurrence if provided
    recurrence_dict = None
    if recurrence:
        schedule_dt = datetime.fromisoformat(schedule)
        recurrence_dict = recurrence_service.validate_and_build_recurrence(
            recurrence, schedule_dt
        )

    return class_repo.add_class(
        name=name.strip(),
        instructor=instructor.strip(),
        schedule=schedule.strip(),
        capacity=capacity,
        location=location.strip(),
        description=description.strip(),
        recurrence=recurrence_dict,
    )


def book_class_for_member(class_id: str, member_email: str,
                          occurrence_date: str = None):
    """
    Handles business logic for booking a class or a specific occurrence
    of a recurring class.

    Args:
        class_id:        The ID of the class to book.
        member_email:    The member's email address.
        occurrence_date: Optional ISO datetime string for a specific
                         occurrence of a recurring class.
    """
    cls = class_repo.get_class_by_id(class_id)
    if cls is None:
        raise ValueError("Class not found.")

    # For recurring classes, validate the requested occurrence
    if cls.get("recurrence"):
        if not occurrence_date:
            raise ValueError(
                "occurrence_date is required when booking a recurring class."
            )
        if not recurrence_service.is_valid_occurrence(cls, occurrence_date):
            raise ValueError(
                "The specified occurrence_date is not a valid occurrence "
                "of this recurring class."
            )
        # Ensure the occurrence is in the future
        if not date_validation(occurrence_date):
            raise ValueError("Cannot book an occurrence that has already passed.")
    else:
        if not date_validation(cls.get('schedule', '')):
            raise ValueError("Cannot book a class that has already ended.")

    return class_repo.book_class(class_id, member_email)


def get_class_members(class_id: str):
    """
    Retrieves the list of members for a specific class.
    """
    members = class_repo.get_booked_members(class_id)

    return members


def update_class_recurrence(class_id: str, recurrence_data: dict):
    """
    Update the recurrence rule on a class, applying to future occurrences only.

    Args:
        class_id:        The class document ID.
        recurrence_data: New recurrence rule dict from the API.

    Returns:
        Updated class dict.

    Raises:
        ValueError: If validation fails or the class is not found.
    """
    cls = class_repo.get_class_by_id(class_id)
    if cls is None:
        raise ValueError("Class not found.")

    schedule_dt = datetime.fromisoformat(cls["schedule"])

    # Use 'now' as the effective start for future-only application
    now = datetime.now()
    effective_start = max(schedule_dt, now)

    recurrence_dict = recurrence_service.validate_and_build_recurrence(
        recurrence_data, effective_start
    )

    return class_repo.update_class_recurrence(class_id, recurrence_dict)


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