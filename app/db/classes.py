"""
Database operations for fitness classes.
"""
from bson import ObjectId
from bson.errors import InvalidId
import uuid

from app.db import DB
from app.db.constants import CLASS_COLLECTION

# Required fields for creating a class
REQUIRED_FIELDS = ['name', 'instructor', 'schedule', 'capacity', 'location']


def _class_to_dict(cls) -> dict:
    """Convert a MongoDB document to a JSON-serializable dict."""
    if cls is None:
        return None
    cls['id'] = str(cls.pop('_id'))
    if 'booked_members' not in cls:
        cls['booked_members'] = []
    return cls


def add_class(name: str, instructor: str, schedule: str,
              capacity: int, location: str,
              description: str = '') -> dict:
    """
    Insert a new fitness class into the database.

    Args:
        name:        Name of the fitness class.
        instructor:  Name of the instructor.
        schedule:    Date/time string (e.g. "2026-03-10T10:00").
        capacity:    Maximum number of participants (must be > 0).
        location:    Where the class is held.
        description: Optional description of the class.

    Returns:
        The newly created class document as a dict (with 'id' field).

    Raises:
        ValueError: If capacity is not a positive integer.
    """
    if not isinstance(capacity, int) or capacity <= 0:
        raise ValueError('Capacity must be a positive integer.')

    col = DB.get_collection(CLASS_COLLECTION)
    new_class = {
        '_id': uuid.uuid4().hex[:8],
        'name': name.strip(),
        'instructor': instructor.strip(),
        'schedule': schedule.strip(),
        'capacity': capacity,
        'location': location.strip(),
        'description': description.strip(),
        'enrolled': 0,   
        'booked_members': [],
    }
    col.insert_one(new_class)
    return _class_to_dict(new_class)


def get_class_by_id(class_id: str) -> dict:
    """
    Retrieve a single fitness class by its ID.

    Returns:
        The class document as a dict, or None if not found.
    """
    col = DB.get_collection(CLASS_COLLECTION)
    
    try:
        query_id = ObjectId(class_id)
    except InvalidId:
        query_id = class_id

    cls = col.find_one({'_id': query_id})
    return _class_to_dict(cls)

def get_all_classes() -> list[dict]:
    """
    Retrieve all fitness classes from the database.

    Returns:
        A list of class dicts.
    """
    col = DB.get_collection(CLASS_COLLECTION)
    classes = col.find()
    return [_class_to_dict(cls) for cls in classes]


def book_class(class_id: str, member_email: str) -> dict:
    """
    Book a spot in a fitness class for a member.

    Args:
        class_id:     The ID of the class to book.
        member_email: The email of the member booking the class.

    Returns:
        The updated class document as a dict.

    Raises:
        ValueError: If class not found, already booked, or class is full.
    """
    col = DB.get_collection(CLASS_COLLECTION)

    try:
        query_id = ObjectId(class_id)
    except InvalidId:
        query_id = class_id

    cls = col.find_one({'_id': query_id})

    if cls is None:
        raise ValueError('Class not found.')

    if member_email in cls.get('booked_members', []):
        raise ValueError('You have already booked this class.')

    if cls.get('enrolled', 0) >= cls.get('capacity', 0):
        raise ValueError('Class is full.')

    col.update_one(
        {'_id': query_id},
        {
            '$push': {'booked_members': member_email},
            '$inc':  {'enrolled': 1},
        }
    )

    updated = col.find_one({'_id': query_id})
    return _class_to_dict(updated)
