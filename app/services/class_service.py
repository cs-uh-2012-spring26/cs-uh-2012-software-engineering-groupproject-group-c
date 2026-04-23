from datetime import datetime
import app.services.email_service as email_service

# DIP: Import the Repository class and the concrete DB connection
from app.db import DB  
from app.db.classes import ClassRepository

# Initialize the repository instance once
class_repo = ClassRepository(DB)

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

def create_class(data: dict):
    """
    Validates and creates a new fitness class via the repository.
    """
    capacity = data.get('capacity')
    if not isinstance(capacity, int) or capacity <= 0:
        raise ValueError('Capacity must be a positive integer.')

    name = data.get('name', '').strip()
    if not name:
        raise ValueError('Class name must not be blank.')
    
    

    return class_repo.add_class(
        name=name,
        instructor=data.get('instructor'),
        schedule=data.get('schedule'),
        capacity=capacity,
        location=data.get('location'),
        description=data.get('description', ''),
    )

def book_class_for_member(class_id: str, member_email: str):
    """
    Handles business logic for booking.
    """
    cls = class_repo.get_class_by_id(class_id)
    if cls is None:
        raise ValueError("Class not found.")

    return class_repo.book_class(class_id, member_email)

def get_class_members(class_id: str):
    """
    Retrieves the list of members for a specific class.
    """
    # Use repo to get members
    members = class_repo.get_booked_members(class_id)
    
    if members is None:
        raise ValueError("Class not found.")
    
    if len(members) == 0:
        raise ValueError("No members booked for this class.")
    
    return members

def send_class_reminders(class_id: str):
    """
    Orchestrates the reminder process.
    """
    # Use repo to fetch class
    cls = class_repo.get_class_by_id(class_id)
    if cls is None:
        raise ValueError("Class not found.")

    members = cls.get('booked_members', [])
    if not members:
        raise ValueError("No booked members for this class.")
    
    # Date Validation
    schedule_str = cls.get('schedule')
    if schedule_str:
        try:
            schedule_dt = datetime.fromisoformat(schedule_str)
            if schedule_dt < datetime.now():
                raise ValueError("Cannot send reminders for a class that has already ended.")
        except ValueError:
            # If format is invalid, we skip the date check as requested
            pass

    # Send via email service
    sent, failed = email_service.send_batch_reminders(cls)
    
    return {
        'total_sent': len(sent),
        'total_failed': len(failed),
        'sent_list': sent,
        'failed_list': failed
    }