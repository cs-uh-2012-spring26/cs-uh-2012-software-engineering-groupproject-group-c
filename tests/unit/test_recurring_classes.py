"""
Integration tests for recurring class features via the Flask test client.
"""

from http import HTTPStatus
import pytest


# =========================================================================== #
# FIXTURES
# =========================================================================== #

@pytest.fixture
def trainer_token(client):
    """Registers a Trainer and returns their JWT token."""
    client.post("/Authentication/register", json={
        "username": "RecurTrainer", "email": "recur_trainer@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Trainer",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={
        "email": "recur_trainer@nyu.edu", "password": "Password@123"
    })
    return res.json["token"]


@pytest.fixture
def member_token(client):
    """Registers a Member and returns their JWT token."""
    client.post("/Authentication/register", json={
        "username": "RecurMember", "email": "recur_member@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={
        "email": "recur_member@nyu.edu", "password": "Password@123"
    })
    return res.json["token"]


@pytest.fixture
def daily_recurring_payload():
    """Payload for a daily recurring class with total_occurrences."""
    return {
        "name": "Morning Run",
        "instructor": "RecurTrainer",
        "schedule": "2027-06-01T07:00",
        "capacity": 15,
        "location": "Track Field",
        "description": "Daily morning run",
        "recurrence": {
            "frequency": "daily",
            "total_occurrences": 5,
        },
    }


@pytest.fixture
def weekly_recurring_payload():
    """Payload for a weekly recurring class on Monday & Wednesday."""
    return {
        "name": "Yoga Flow",
        "instructor": "RecurTrainer",
        "schedule": "2027-06-02T09:00",
        "capacity": 20,
        "location": "Studio B",
        "description": "Weekly yoga on Mon & Wed",
        "recurrence": {
            "frequency": "weekly",
            "days_of_week": ["monday", "wednesday"],
            "end_date": "2027-07-01T09:00",
        },
    }


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# =========================================================================== #
# TESTS: POST /classes/ — Creating recurring classes
# =========================================================================== #

class TestCreateRecurringClass:

    def test_create_daily_recurring_class(
        self, client, trainer_token, daily_recurring_payload,
    ):
        res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.CREATED
        data = res.json
        assert "id" in data
        assert data["recurrence"]["frequency"] == "daily"
        assert data["recurrence"]["total_occurrences"] == 5

    def test_create_weekly_recurring_class(
        self, client, trainer_token, weekly_recurring_payload,
    ):
        res = client.post(
            "/classes/", json=weekly_recurring_payload,
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.CREATED
        data = res.json
        assert data["recurrence"]["frequency"] == "weekly"
        assert data["recurrence"]["days_of_week"] == ["monday", "wednesday"]

    def test_create_class_without_recurrence_still_works(
        self, client, trainer_token,
    ):
        """Backward compatibility: creating a non-recurring class."""
        payload = {
            "name": "Single Class",
            "instructor": "RecurTrainer",
            "schedule": "2027-06-01T10:00",
            "capacity": 10,
            "location": "Room 1",
        }
        res = client.post(
            "/classes/", json=payload, headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.CREATED
        assert "recurrence" not in res.json

    def test_create_recurring_class_missing_end_condition(
        self, client, trainer_token,
    ):
        payload = {
            "name": "Bad Class",
            "instructor": "RecurTrainer",
            "schedule": "2027-06-01T08:00",
            "capacity": 10,
            "location": "Room X",
            "recurrence": {"frequency": "daily"},
        }
        res = client.post(
            "/classes/", json=payload, headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "end condition" in res.json["message"]

    def test_create_recurring_class_invalid_frequency(
        self, client, trainer_token,
    ):
        payload = {
            "name": "Bad Class",
            "instructor": "RecurTrainer",
            "schedule": "2027-06-01T08:00",
            "capacity": 10,
            "location": "Room X",
            "recurrence": {
                "frequency": "monthly",
                "total_occurrences": 3,
            },
        }
        res = client.post(
            "/classes/", json=payload, headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "Invalid frequency" in res.json["message"]

    def test_create_recurring_class_both_end_conditions(
        self, client, trainer_token,
    ):
        payload = {
            "name": "Bad Class",
            "instructor": "RecurTrainer",
            "schedule": "2027-06-01T08:00",
            "capacity": 10,
            "location": "Room X",
            "recurrence": {
                "frequency": "daily",
                "end_date": "2027-07-01T08:00",
                "total_occurrences": 10,
            },
        }
        res = client.post(
            "/classes/", json=payload, headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "not both" in res.json["message"]


# =========================================================================== #
# TESTS: GET /classes/ — Expanded occurrences
# =========================================================================== #

class TestGetClassesWithOccurrences:

    def test_recurring_class_shows_expanded_occurrences(
        self, client, trainer_token, daily_recurring_payload,
    ):
        # Create a daily recurring class with 5 occurrences
        client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        res = client.get("/classes/")
        assert res.status_code == HTTPStatus.OK
        classes = res.json["classes"]
        # Should have 5 expanded occurrence entries
        assert len(classes) == 5
        # Each entry should have an occurrence_date
        for entry in classes:
            assert "occurrence_date" in entry
            assert entry["name"] == "Morning Run"

    def test_non_recurring_class_has_no_occurrence_date(
        self, client, trainer_token,
    ):
        payload = {
            "name": "Single Pilates",
            "instructor": "RecurTrainer",
            "schedule": "2027-06-01T11:00",
            "capacity": 10,
            "location": "Room 2",
        }
        client.post(
            "/classes/", json=payload, headers=_headers(trainer_token),
        )
        res = client.get("/classes/")
        assert res.status_code == HTTPStatus.OK
        classes = res.json["classes"]
        assert len(classes) == 1
        assert "occurrence_date" not in classes[0]

    def test_mixed_recurring_and_single_classes(
        self, client, trainer_token, daily_recurring_payload,
    ):
        # Create one recurring (5 occurrences) and one single class
        client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        single_payload = {
            "name": "Single Spin",
            "instructor": "RecurTrainer",
            "schedule": "2027-06-10T08:00",
            "capacity": 10,
            "location": "Room 3",
        }
        client.post(
            "/classes/", json=single_payload,
            headers=_headers(trainer_token),
        )
        res = client.get("/classes/")
        classes = res.json["classes"]
        # 5 recurring + 1 single = 6 total entries
        assert len(classes) == 6


# =========================================================================== #
# TESTS: POST /classes/<id>/book — Booking occurrences
# =========================================================================== #

class TestBookOccurrence:

    def test_book_specific_occurrence(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        # Create recurring class
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        # Get the first occurrence date from the listing
        list_res = client.get("/classes/")
        first_occurrence = list_res.json["classes"][0]["occurrence_date"]

        # Book that specific occurrence
        res = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": first_occurrence},
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.OK
        assert res.json["message"] == "Booking successful."

    def test_book_recurring_class_without_occurrence_date_rejected(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        # Book without specifying an occurrence date
        res = client.post(
            f"/classes/{class_id}/book",
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "occurrence_date is required" in res.json["message"]

    def test_book_invalid_occurrence_date_rejected(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        # Try to book a date that is NOT a valid occurrence
        res = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": "2099-12-25T08:00"},
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "not a valid occurrence" in res.json["message"]

    def test_book_non_recurring_class_without_occurrence_date_works(
        self, client, trainer_token, member_token,
    ):
        """Non-recurring classes should still book normally (no occurrence_date)."""
        payload = {
            "name": "One-off Boxing",
            "instructor": "RecurTrainer",
            "schedule": "2027-06-01T15:00",
            "capacity": 10,
            "location": "Gym",
        }
        create_res = client.post(
            "/classes/", json=payload, headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        res = client.post(
            f"/classes/{class_id}/book",
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.OK


# =========================================================================== #
# TESTS: PATCH /classes/<id>/recurrence — Update recurrence
# =========================================================================== #

class TestUpdateRecurrence:

    def test_update_recurrence_success(
        self, client, trainer_token, daily_recurring_payload,
    ):
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        new_rule = {
            "frequency": "weekly",
            "days_of_week": ["tuesday", "thursday"],
            "total_occurrences": 8,
        }
        res = client.patch(
            f"/classes/{class_id}/recurrence",
            json=new_rule,
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.OK
        assert "Recurrence updated" in res.json["message"]
        assert res.json["class"]["recurrence"]["frequency"] == "weekly"

    def test_update_recurrence_member_forbidden(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        res = client.patch(
            f"/classes/{class_id}/recurrence",
            json={"frequency": "daily", "total_occurrences": 3},
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.FORBIDDEN

    def test_update_recurrence_invalid_rule(
        self, client, trainer_token, daily_recurring_payload,
    ):
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        # Missing end condition
        res = client.patch(
            f"/classes/{class_id}/recurrence",
            json={"frequency": "daily"},
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST

    def test_update_recurrence_class_not_found(
        self, client, trainer_token,
    ):
        res = client.patch(
            "/classes/nonexistent_id_123/recurrence",
            json={"frequency": "daily", "total_occurrences": 5},
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "Class not found" in res.json["message"]
