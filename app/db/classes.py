"""
Database operations for fitness classes following the Repository Pattern (DIP).
"""
from datetime import datetime
from app.db.constants import CLASS_COLLECTION
import uuid

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
        if cls is None:
            return None
        cls = dict(cls)
        cls['id'] = str(cls['_id'])
        del cls['_id']
        return cls
    
    def _format_id(self, class_id):
        """Validate and normalize custom string class IDs."""
        if not class_id or not isinstance(class_id, str):
            raise ValueError("Invalid Class ID format.")
        return class_id.strip()

    def add_class(self, name: str, instructor: str, schedule: str,
                  capacity: int, location: str,
                  description: str = '',
                  recurrence: dict = None) -> dict:
        """Insert a new fitness class into the database.

        All classes use bookings_by_occurrence for per-occurrence tracking.
        """

        col = self._get_col()
        new_class = {
            '_id': str(uuid.uuid4())[:8],
            'name': name.strip(),
            'instructor': instructor.strip(),
            'schedule': schedule.strip(),
            'capacity': capacity,
            'location': location.strip(),
            'description': description.strip(),
            'bookings_by_occurrence': {},
        }
        if recurrence is not None:
            new_class['recurrence'] = recurrence
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

    def book_class(self, class_id: str, member_email: str,
                   occurrence_date: str = None) -> dict:
        """Book a spot in a specific occurrence of a fitness class.

        Args:
            class_id:        The class document ID.
            member_email:    The member's email address.
            occurrence_date: ISO datetime string for the occurrence to book.

        Returns:
            Dict with booking result including per-occurrence enrolled
            count and class capacity.

        Raises:
            ValueError: If class not found, already booked, or full.
        """
        col = self._get_col()
        query_id = self._format_id(class_id)

        cls = col.find_one({'_id': query_id})

        if cls is None:
            raise ValueError('Class not found.')

        if not occurrence_date:
            raise ValueError('occurrence_date is required to book a class.')

        occ_key = f'bookings_by_occurrence.{occurrence_date}'
        bookings = cls.get('bookings_by_occurrence', {})
        occ_data = bookings.get(occurrence_date, {
            'enrolled': 0, 'booked_members': []
        })

        # Check if already booked for this occurrence
        if member_email in occ_data.get('booked_members', []):
            raise ValueError('You have already booked this occurrence.')

        # Check capacity for this occurrence
        if occ_data.get('enrolled', 0) >= cls['capacity']:
            raise ValueError('This occurrence is full.')

        # Atomic update using dot notation for the specific occurrence
        update_result = col.update_one(
            {
                '_id': query_id,
                f'{occ_key}.booked_members': {'$ne': member_email},
            },
            {
                '$push': {f'{occ_key}.booked_members': member_email},
                '$inc':  {f'{occ_key}.enrolled': 1},
            }
        )

        # If no sub-document existed yet (first booking for this occurrence),
        # the $ne check on a missing field won't match.  Initialise and retry.
        if update_result.modified_count == 0:
            init_result = col.update_one(
                {
                    '_id': query_id,
                    occ_key: {'$exists': False},
                },
                {
                    '$set': {
                        occ_key: {
                            'enrolled': 1,
                            'booked_members': [member_email],
                        }
                    }
                }
            )
            if init_result.modified_count == 0:
                # Sub-doc exists but the first update didn't match
                if member_email in occ_data.get('booked_members', []):
                    raise ValueError('You have already booked this occurrence.')
                else:
                    raise ValueError('This occurrence is full.')

        updated = col.find_one({'_id': query_id})
        result = self._class_to_dict(updated)

        # Return per-occurrence enrolled count
        updated_bookings = result.get('bookings_by_occurrence', {})
        occ = updated_bookings.get(occurrence_date, {})
        result['enrolled'] = occ.get('enrolled', 0)

        return result

    def get_booked_members(self, class_id: str,
                           occurrence_date: str = None) -> list[str]:
        """Retrieve the list of member emails who have booked a class.

        Args:
            class_id:        The class document ID.
            occurrence_date: The specific occurrence date to query.
                             If omitted, returns all members across all
                             occurrences (deduplicated).

        Returns:
            List of member email strings.

        Raises:
            ValueError: If the class is not found.
        """
        col = self._get_col()
        query_id = self._format_id(class_id)

        cls = col.find_one({'_id': query_id})

        if cls is None:
            raise ValueError('Class not found.')

        bookings = cls.get('bookings_by_occurrence', {})

        if occurrence_date:
            occ = bookings.get(occurrence_date, {})
            return occ.get('booked_members', [])
        else:
            # Return all members across all occurrences (deduplicated)
            all_members = []
            seen = set()
            for occ_data in bookings.values():
                for email in occ_data.get('booked_members', []):
                    if email not in seen:
                        all_members.append(email)
                        seen.add(email)
            return all_members

    def get_occurrence_enrolled(self, class_id: str,
                                occurrence_date: str) -> int:
        """Get the enrolled count for a specific occurrence.

        Reads directly from the database to ensure accuracy.

        Args:
            class_id:        The class document ID.
            occurrence_date: ISO datetime of the occurrence.

        Returns:
            Integer enrolled count.
        """
        col = self._get_col()
        query_id = self._format_id(class_id)
        cls = col.find_one({'_id': query_id})
        if cls is None:
            return 0
        bookings = cls.get('bookings_by_occurrence', {})
        # Try exact key match first, then try matching by parsed datetime
        if occurrence_date in bookings:
            return bookings[occurrence_date].get('enrolled', 0)
        # Fallback: parse both sides and compare as datetime objects
        try:
            target_dt = datetime.fromisoformat(occurrence_date)
        except (ValueError, TypeError):
            return 0
        for key, occ_data in bookings.items():
            try:
                if datetime.fromisoformat(key) == target_dt:
                    return occ_data.get('enrolled', 0)
            except (ValueError, TypeError):
                continue
        return 0

    def update_class_recurrence(self, class_id: str,
                                recurrence: dict = None,
                                new_schedule: str = None) -> dict:
        """Update or remove the recurrence rule on an existing class.

        Args:
            class_id:     The class document ID.
            recurrence:   New recurrence dict, or None to remove recurrence.
            new_schedule: If provided, also update the schedule field so
                          rrule uses the correct dtstart.

        Returns:
            Updated class dict.

        Raises:
            ValueError: If the class is not found.
        """
        col = self._get_col()
        query_id = self._format_id(class_id)

        if recurrence is not None:
            set_fields = {'recurrence': recurrence}
            if new_schedule:
                set_fields['schedule'] = new_schedule
            update_op = {'$set': set_fields}
        else:
            update_op = {'$unset': {'recurrence': ''}}

        result = col.update_one({'_id': query_id}, update_op)

        if result.matched_count == 0:
            raise ValueError('Class not found.')

        updated = col.find_one({'_id': query_id})
        return self._class_to_dict(updated)