"""
Recurrence service — stateless orchestrator for recurrence operations.

Delegates to the recurrence model for validation and generation.
Keeps recurrence concerns separated from class_service / notification logic.
"""

from datetime import datetime
from typing import List, Optional

from app.models.recurrence import (
    generate_occurrences,
    validate_recurrence_input,
    build_recurrence_dict,
)


def get_occurrences(class_doc: dict) -> List[datetime]:
    """
    Generate all occurrences for a stored class document.

    Args:
        class_doc: A class dict as returned by the repository (must contain
                   'schedule' and optionally 'recurrence').

    Returns:
        List of datetime objects. Returns a single-element list containing
        the schedule datetime if the class is non-recurring.
    """
    schedule_dt = datetime.fromisoformat(class_doc["schedule"])
    recurrence = class_doc.get("recurrence")

    if not recurrence:
        return [schedule_dt]

    return generate_occurrences(recurrence, schedule_dt)


def get_future_occurrences(class_doc: dict) -> List[datetime]:
    """
    Generate only future occurrences (after now) for a class document.

    Args:
        class_doc: Class dict from the repository.

    Returns:
        List of future datetime objects.
    """
    schedule_dt = datetime.fromisoformat(class_doc["schedule"])
    recurrence = class_doc.get("recurrence")

    if not recurrence:
        if schedule_dt > datetime.now():
            return [schedule_dt]
        return []

    return generate_occurrences(recurrence, schedule_dt, after=datetime.now())


def get_occurrences_in_range(
    class_doc: dict,
    range_start: datetime,
    range_end: datetime,
) -> List[datetime]:
    """
    Generate occurrences within a specific date range.

    Args:
        class_doc:   Class dict from the repository.
        range_start: Start of the date window (inclusive).
        range_end:   End of the date window (inclusive).

    Returns:
        List of datetime objects within [range_start, range_end].
    """
    all_occurrences = get_occurrences(class_doc)
    return [dt for dt in all_occurrences if range_start <= dt <= range_end]


def validate_and_build_recurrence(
    data: dict, schedule_dt: datetime
) -> dict:
    """
    Validate raw recurrence input and return a clean dict for storage.

    Args:
        data:        Raw recurrence dict from the API request.
        schedule_dt: Parsed schedule datetime of the class.

    Returns:
        Cleaned recurrence dict ready for database storage.

    Raises:
        ValueError: If validation fails.
    """
    validate_recurrence_input(data, schedule_dt)
    return build_recurrence_dict(data)


def is_valid_occurrence(class_doc: dict, occurrence_date_str: str) -> bool:
    """
    Check whether a given date string matches a valid occurrence of a class.

    Args:
        class_doc:          Class dict from the repository.
        occurrence_date_str: ISO 8601 datetime string to check.

    Returns:
        True if the date is a valid occurrence, False otherwise.
    """
    try:
        target_dt = datetime.fromisoformat(occurrence_date_str)
    except (ValueError, TypeError):
        return False

    all_occurrences = get_occurrences(class_doc)
    return target_dt in all_occurrences
