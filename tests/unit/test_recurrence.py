"""
Unit tests for the recurrence model (pure logic — no DB or HTTP).
"""

from datetime import datetime, timedelta
import pytest

from app.models.recurrence import (
    RecurrenceFrequency,
    validate_recurrence_input,
    build_recurrence_dict,
    generate_occurrences,
)


# =========================================================================== #
# HELPERS
# =========================================================================== #

def _future(days=30):
    """Return an ISO datetime string N days in the future."""
    return (datetime.now() + timedelta(days=days)).isoformat()


def _future_dt(days=30):
    """Return a datetime object N days in the future."""
    return datetime.now() + timedelta(days=days)


SCHEDULE_DT = _future_dt(days=1)       # class starts tomorrow
SCHEDULE_STR = SCHEDULE_DT.isoformat()

# =========================================================================== #
# TESTS: validate_recurrence_input — happy paths
# =========================================================================== #


class TestValidateRecurrenceHappyPaths:
    """Validation should pass for well-formed inputs."""

    def test_daily_with_end_date(self):
        data = {"frequency": "daily", "end_date": _future(60)}
        validate_recurrence_input(data, SCHEDULE_DT)  # should not raise

    def test_weekly_with_days_and_count(self):
        data = {
            "frequency": "weekly",
            "days_of_week": ["monday", "wednesday"],
            "total_occurrences": 10,
        }
        validate_recurrence_input(data, SCHEDULE_DT)

    def test_weekly_with_days_and_end_date(self):
        data = {
            "frequency": "weekly",
            "days_of_week": ["friday"],
            "end_date": _future(90),
        }
        validate_recurrence_input(data, SCHEDULE_DT)

    def test_daily_with_count(self):
        data = {"frequency": "daily", "total_occurrences": 5}
        validate_recurrence_input(data, SCHEDULE_DT)


# =========================================================================== #
# TESTS: validate_recurrence_input — error paths
# =========================================================================== #


class TestValidateRecurrenceErrors:
    """Validation should raise ValueError for bad inputs."""

    def test_missing_end_condition(self):
        data = {"frequency": "daily"}
        with pytest.raises(ValueError, match="end condition"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_both_end_conditions(self):
        data = {
            "frequency": "daily",
            "end_date": _future(60),
            "total_occurrences": 5,
        }
        with pytest.raises(ValueError, match="not both"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_invalid_frequency(self):
        data = {"frequency": "monthly", "end_date": _future(60)}
        with pytest.raises(ValueError, match="Invalid frequency"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_weekly_missing_days(self):
        data = {"frequency": "weekly", "total_occurrences": 5}
        with pytest.raises(ValueError, match="days_of_week"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_invalid_day_name(self):
        data = {
            "frequency": "weekly",
            "days_of_week": ["funday"],
            "total_occurrences": 5,
        }
        with pytest.raises(ValueError, match="Invalid day name"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_end_date_in_past(self):
        data = {"frequency": "daily", "end_date": "2020-01-01T08:00"}
        with pytest.raises(ValueError, match="future"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_end_date_before_schedule(self):
        # end_date is in the future but before schedule
        early_end = (SCHEDULE_DT - timedelta(hours=1)).isoformat()
        # Use a schedule far in the future so end_date is still in the future
        far_schedule = _future_dt(days=90)
        near_end = _future(days=60)
        with pytest.raises(ValueError, match="after the class schedule"):
            validate_recurrence_input(
                {"frequency": "daily", "end_date": near_end},
                far_schedule,
            )

    def test_invalid_end_date_format(self):
        data = {"frequency": "daily", "end_date": "not-a-date"}
        with pytest.raises(ValueError, match="Invalid end_date format"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_non_positive_count(self):
        data = {"frequency": "daily", "total_occurrences": 0}
        with pytest.raises(ValueError, match="positive integer"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_negative_count(self):
        data = {"frequency": "daily", "total_occurrences": -3}
        with pytest.raises(ValueError, match="positive integer"):
            validate_recurrence_input(data, SCHEDULE_DT)

    def test_non_dict_input(self):
        with pytest.raises(ValueError, match="JSON object"):
            validate_recurrence_input("not a dict", SCHEDULE_DT)


# =========================================================================== #
# TESTS: build_recurrence_dict
# =========================================================================== #


class TestBuildRecurrenceDict:
    """build_recurrence_dict should produce clean, normalised dicts."""

    def test_daily_with_end_date(self):
        data = {"frequency": "Daily", "end_date": "2027-06-01T08:00"}
        result = build_recurrence_dict(data)
        assert result["frequency"] == "daily"
        assert result["end_date"] == "2027-06-01T08:00"
        assert "total_occurrences" not in result

    def test_weekly_with_count_and_days(self):
        data = {
            "frequency": "WEEKLY",
            "days_of_week": ["Monday", " Wednesday "],
            "total_occurrences": 10,
        }
        result = build_recurrence_dict(data)
        assert result["frequency"] == "weekly"
        assert result["days_of_week"] == ["monday", "wednesday"]
        assert result["total_occurrences"] == 10
        assert "end_date" not in result


# =========================================================================== #
# TESTS: generate_occurrences
# =========================================================================== #


class TestGenerateOccurrences:
    """generate_occurrences should produce correct datetime lists."""

    def test_daily_with_count(self):
        start = datetime(2027, 3, 1, 8, 0)
        recurrence = {"frequency": "daily", "total_occurrences": 5}
        result = generate_occurrences(recurrence, start)
        assert len(result) == 5
        # First occurrence is the start date itself
        assert result[0] == start
        # Each subsequent occurrence is one day later
        for i in range(1, 5):
            assert result[i] == start + timedelta(days=i)

    def test_daily_with_end_date(self):
        start = datetime(2027, 3, 1, 8, 0)
        end = datetime(2027, 3, 5, 8, 0)
        recurrence = {"frequency": "daily", "end_date": end.isoformat()}
        result = generate_occurrences(recurrence, start)
        assert len(result) == 5  # Mar 1–5 inclusive
        assert result[-1] == end

    def test_weekly_on_specific_days(self):
        # Start on a Monday
        start = datetime(2027, 3, 1, 8, 0)  # 2027-03-01 is a Monday
        recurrence = {
            "frequency": "weekly",
            "days_of_week": ["monday", "wednesday"],
            "total_occurrences": 4,
        }
        result = generate_occurrences(recurrence, start)
        assert len(result) == 4
        # All occurrences should be on Monday (0) or Wednesday (2)
        for dt in result:
            assert dt.weekday() in (0, 2)

    def test_weekly_with_end_date(self):
        start = datetime(2027, 3, 1, 8, 0)  # Monday
        end = datetime(2027, 3, 15, 23, 59)
        recurrence = {
            "frequency": "weekly",
            "days_of_week": ["monday"],
            "end_date": end.isoformat(),
        }
        result = generate_occurrences(recurrence, start)
        # Mondays: Mar 1, 8, 15
        assert len(result) == 3
        assert all(dt.weekday() == 0 for dt in result)

    def test_after_filter(self):
        start = datetime(2027, 3, 1, 8, 0)
        recurrence = {"frequency": "daily", "total_occurrences": 10}
        cutoff = datetime(2027, 3, 5, 8, 0)
        result = generate_occurrences(recurrence, start, after=cutoff)
        # Should only include Mar 6–10 (5 occurrences after the cutoff)
        assert len(result) == 5
        assert all(dt > cutoff for dt in result)
