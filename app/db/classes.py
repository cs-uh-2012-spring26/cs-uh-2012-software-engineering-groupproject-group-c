"""
Database operations for fitness classes.
"""
from bson import ObjectId
from bson.errors import InvalidId

from app.db import DB
from app.db.constants import CLASS_COLLECTION

# Required fields for creating a class
REQUIRED_FIELDS = ['name', 'instructor', 'schedule', 'capacity', 'location']


def _class_to_dict(cls) -> dict:
    """Convert a MongoDB document to a JSON-serializable dict."""
    if cls is None:
        return None
    cls['id'] = str(cls.pop('_id'))
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
        'name': name.strip(),
        'instructor': instructor.strip(),
        'schedule': schedule.strip(),
        'capacity': capacity,
        'location': location.strip(),
        'description': description.strip(),
        'enrolled': 0,   # number of current bookings
    }
    result = col.insert_one(new_class)
    new_class['_id'] = result.inserted_id
    return _class_to_dict(new_class)


def get_class_by_id(class_id: str) -> dict:
    """
    Retrieve a single fitness class by its ID.

    Args:
        class_id: The string representation of the MongoDB ObjectId.

    Returns:
        The class document as a dict, or None if not found.

    Raises:
        ValueError: If class_id is not a valid ObjectId string.
    """
    try:
        oid = ObjectId(class_id)
    except InvalidId:
        raise ValueError(f'Invalid class ID: {class_id}')

    cls = DB.get_collection(CLASS_COLLECTION).find_one({'_id': oid})
    return _class_to_dict(cls)