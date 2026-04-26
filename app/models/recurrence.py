"""
Recurrence data model and validation logic.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from dateutil.rrule import rrule, DAILY, WEEKLY, MO, TU, WE, TH, FR, SA, SU


class RecurrenceFrequency(Enum):
    """Supported recurrence frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"


# Maps lowercase day names to dateutil weekday constants
WEEKDAY_MAP = {
    "monday": MO,
    "tuesday": TU,
    "wednesday": WE,
    "thursday": TH,
    "friday": FR,
    "saturday": SA,
    "sunday": SU,
}

# Maps RecurrenceFrequency to dateutil rrule frequency constants
_FREQ_MAP = {
    RecurrenceFrequency.DAILY: DAILY,
    RecurrenceFrequency.WEEKLY: WEEKLY,
}


def validate_recurrence_input(data: dict, schedule_dt: datetime) -> None:
    """
    Validate a raw recurrence input dictionary.

    """
    if not isinstance(data, dict):
        raise ValueError("Recurrence must be a JSON object.")

    # --- frequency ---
    frequency_str = data.get("frequency", "").strip().lower()
    try:
        frequency = RecurrenceFrequency(frequency_str)
    except ValueError:
        allowed = [f.value for f in RecurrenceFrequency]
        raise ValueError(
            f"Invalid frequency '{frequency_str}'. Must be one of {allowed}."
        )

    # --- end condition: exactly one of end_date / total_occurrences ---
    has_end_date = "end_date" in data and data["end_date"] is not None
    has_count = (
        "total_occurrences" in data and data["total_occurrences"] is not None
    )

    if not has_end_date and not has_count:
        raise ValueError(
            "Recurrence must have an end condition: "
            "provide either 'end_date' or 'total_occurrences'."
        )
    if has_end_date and has_count:
        raise ValueError(
            "Provide only one end condition: "
            "'end_date' or 'total_occurrences', not both."
        )

    # --- end_date validation ---
    if has_end_date:
        try:
            end_dt = datetime.fromisoformat(data["end_date"])
        except (ValueError, TypeError):
            raise ValueError(
                "Invalid end_date format. Must be ISO 8601 "
                "(e.g., '2026-06-01T08:00')."
            )
        if end_dt <= datetime.now():
            raise ValueError("end_date must be in the future.")
        if end_dt <= schedule_dt:
            raise ValueError("end_date must be after the class schedule date.")

    # --- total_occurrences validation ---
    if has_count:
        count = data["total_occurrences"]
        if not isinstance(count, int) or count <= 0:
            raise ValueError(
                "total_occurrences must be a positive integer."
            )

    # --- days_of_week (required for WEEKLY, forbidden for DAILY) ---
    days = data.get("days_of_week")
    if frequency == RecurrenceFrequency.WEEKLY:
        if not days or not isinstance(days, list) or len(days) == 0:
            raise ValueError(
                "days_of_week is required for weekly recurrence "
                "and must be a non-empty list."
            )
        for day in days:
            if day.strip().lower() not in WEEKDAY_MAP:
                raise ValueError(
                    f"Invalid day name '{day}'. "
                    f"Must be one of {list(WEEKDAY_MAP.keys())}."
                )


def build_recurrence_dict(data: dict) -> dict:
    """
    Build a cleaned recurrence dict suitable for database storage.

    Args:
        data: Raw (already validated) recurrence input.

    Returns:
        Cleaned dict with normalised values.
    """
    frequency_str = data["frequency"].strip().lower()
    result = {"frequency": frequency_str}

    if "end_date" in data and data["end_date"] is not None:
        result["end_date"] = data["end_date"].strip()

    if "total_occurrences" in data and data["total_occurrences"] is not None:
        result["total_occurrences"] = int(data["total_occurrences"])

    days = data.get("days_of_week")
    if days and isinstance(days, list):
        result["days_of_week"] = [d.strip().lower() for d in days]

    return result


def generate_occurrences(
    recurrence: dict,
    schedule_dt: datetime,
    after: Optional[datetime] = None,
) -> List[datetime]:
    """
    Dynamically generate occurrence datetimes from a recurrence rule.

    Args:
        recurrence:  Stored recurrence dict (frequency, end_date or
                     total_occurrences, days_of_week).
        schedule_dt: The base schedule datetime of the class.
        after:       If provided, only return occurrences strictly after
                     this datetime (useful for future-only queries).

    Returns:
        Sorted list of datetime objects representing each occurrence.
    """
    frequency = RecurrenceFrequency(recurrence["frequency"])
    freq_const = _FREQ_MAP[frequency]

    kwargs = {
        "freq": freq_const,
        "dtstart": schedule_dt,
    }

    # End condition
    if "end_date" in recurrence:
        kwargs["until"] = datetime.fromisoformat(recurrence["end_date"])
    elif "total_occurrences" in recurrence:
        kwargs["count"] = recurrence["total_occurrences"]

    # Weekly: restrict to specified weekdays
    if frequency == RecurrenceFrequency.WEEKLY:
        days = recurrence.get("days_of_week", [])
        kwargs["byweekday"] = [WEEKDAY_MAP[d] for d in days]

    rule = rrule(**kwargs)
    occurrences = list(rule)

    if after is not None:
        occurrences = [dt for dt in occurrences if dt > after]

    return occurrences
