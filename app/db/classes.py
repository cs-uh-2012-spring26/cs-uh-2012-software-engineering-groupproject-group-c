"""
Database operations for fitness classes following the Repository Pattern (DIP).
"""
from bson import ObjectId
from bson.errors import InvalidId
from app.db.constants import CLASS_COLLECTION

class ClassRepository:
    def __init__(self, db_provider):
        """
        DIP: We depend on a db_provider abstraction rather than a global object.
        """
        self.db = db_provider
        self.collection_name = CLASS_COLLECTION

    def _get_col(self):
        """Helper to get the MongoDB collection."""
        return self.db.get_collection(self.collection_name)

    def _class_to_dict(self, cls) -> dict:
        """Convert a MongoDB document to a JSON-serializable dict."""
        if cls is None:
            return None
        cls['id'] = str(cls.pop('_id'))
        return cls

    def _format_id(self, class_id):
        """Helper to handle both ObjectId and custom string IDs."""
        try:
            return ObjectId(class_id)
        except (InvalidId, TypeError):
            return ValueError("Invalid Class ID format.")

    def add_class(self, name: str, instructor: str, schedule: str,
                  capacity: int, location: str,
                  description: str = '') -> dict:
        """Insert a new fitness class into the database."""

        col = self._get_col()
        new_class = {
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
        return self._class_to_dict(new_class)

    def get_class_by_id(self, class_id: str) -> dict:
        """Retrieve a single fitness class by its ID."""
        col = self._get_col()
        query_id = self._format_id(class_id)
        cls = col.find_one({'_id': query_id})
        return self._class_to_dict(cls)

    def get_all_classes(self) -> list[dict]:
        """Retrieve all fitness classes from the database."""
        col = self._get_col()
        classes = col.find()
        return [self._class_to_dict(cls) for cls in classes]

    def book_class(self, class_id: str, member_email: str) -> dict:
        """Book a spot in a fitness class for a member."""
        col = self._get_col()
        query_id = self._format_id(class_id)

        cls = col.find_one({'_id': query_id})

        if cls is None:
            raise ValueError('Class not found.')
        
        update_result = col.update_one(
            {
                '_id': query_id,
                'booked_members': {'$ne': member_email}, 
                'enrolled': {'$lt': cls['capacity']} 
            },
            {
                '$push': {'booked_members': member_email},
                '$inc':  {'enrolled': 1},
            }
        )

        if update_result.modified_count == 0:
            if member_email in cls.get('booked_members', []):
                raise ValueError('You have already booked this class.')
            else:
                raise ValueError('Class is full.')

        updated = col.find_one({'_id': query_id})
        return self._class_to_dict(updated)

    def get_booked_members(self, class_id: str) -> list[str]:
        """Retrieve the list of member emails who have booked a class."""
        col = self._get_col()
        query_id = self._format_id(class_id)

        cls = col.find_one({'_id': query_id})

        if cls is None:
            raise ValueError('Class not found.')

        return cls.get('booked_members', [])