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
def member2_token(client):
    """Registers a second Member and returns their JWT token."""
    client.post("/Authentication/register", json={
        "username": "RecurMember2", "email": "recur_member2@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={
        "email": "recur_member2@nyu.edu", "password": "Password@123"
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


@pytest.fixture
def capacity_one_recurring_payload():
    """Payload for a daily recurring class with capacity=1."""
    return {
        "name": "VIP Training",
        "instructor": "RecurTrainer",
        "schedule": "2027-06-01T07:00",
        "capacity": 1,
        "location": "Private Room",
        "description": "One-on-one sessions",
        "recurrence": {
            "frequency": "daily",
            "total_occurrences": 3,
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

    def test_all_classes_use_bookings_by_occurrence(
        self, client, trainer_token, daily_recurring_payload,
    ):
        """All classes (recurring and non-recurring) use bookings_by_occurrence."""
        # Recurring class
        res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.CREATED
        assert "bookings_by_occurrence" in res.json
        assert res.json["bookings_by_occurrence"] == {}

        # Non-recurring class
        payload = {
            "name": "Single Class",
            "instructor": "RecurTrainer",
            "schedule": "2027-06-01T10:00",
            "capacity": 10,
            "location": "Room 1",
        }
        res2 = client.post(
            "/classes/", json=payload, headers=_headers(trainer_token),
        )
        assert res2.status_code == HTTPStatus.CREATED
        assert "bookings_by_occurrence" in res2.json
        assert res2.json["bookings_by_occurrence"] == {}


# =========================================================================== #
# TESTS: GET /classes/ — Expanded occurrences
# =========================================================================== #

class TestGetClassesWithOccurrences:

    def test_recurring_class_shows_expanded_occurrences(
        self, client, trainer_token, daily_recurring_payload,
    ):
        client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        res = client.get("/classes/")
        assert res.status_code == HTTPStatus.OK
        classes = res.json["classes"]
        assert len(classes) == 5
        for entry in classes:
            assert "occurrence_date" in entry
            assert entry["name"] == "Morning Run"
            assert "enrolled" in entry
            assert entry["enrolled"] == 0

    def test_non_recurring_class_has_occurrence_date(
        self, client, trainer_token,
    ):
        """Non-recurring classes also have occurrence_date = schedule."""
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
        # Non-recurring class now also has occurrence_date
        assert classes[0]["occurrence_date"] == "2027-06-01T11:00"
        assert classes[0]["enrolled"] == 0

    def test_mixed_recurring_and_single_classes(
        self, client, trainer_token, daily_recurring_payload,
    ):
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
        # All entries have occurrence_date
        for entry in classes:
            assert "occurrence_date" in entry


# =========================================================================== #
# TESTS: POST /classes/<id>/book — Booking occurrences
# =========================================================================== #

class TestBookOccurrence:

    def test_book_specific_occurrence(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        list_res = client.get("/classes/")
        first_occurrence = list_res.json["classes"][0]["occurrence_date"]

        res = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": first_occurrence},
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.OK
        assert res.json["message"] == "Booking successful."
        assert res.json["enrolled"] == 1

    def test_book_without_occurrence_date_rejected(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        """Booking without occurrence_date should always be rejected."""
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        res = client.post(
            f"/classes/{class_id}/book",
            json={},
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST

    def test_book_invalid_occurrence_date_rejected(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        res = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": "2099-12-25T08:00"},
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "not a valid occurrence" in res.json["message"]

    def test_book_non_recurring_class_with_occurrence_date(
        self, client, trainer_token, member_token,
    ):
        """Non-recurring classes: use the schedule date as occurrence_date."""
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
            json={"occurrence_date": "2027-06-01T15:00"},
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.OK

    # --- Bug #1 Fix: Per-occurrence capacity is independent ---

    def test_capacity_independent_per_occurrence(
        self, client, trainer_token, member_token, member2_token,
        capacity_one_recurring_payload,
    ):
        """Booking occurrence 1 to capacity should NOT block occurrence 2."""
        create_res = client.post(
            "/classes/", json=capacity_one_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        list_res = client.get("/classes/")
        occ1 = list_res.json["classes"][0]["occurrence_date"]
        occ2 = list_res.json["classes"][1]["occurrence_date"]

        # Member 1 books occurrence 1 (fills it, capacity=1)
        res1 = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member_token),
        )
        assert res1.status_code == HTTPStatus.OK
        assert res1.json["enrolled"] == 1

        # Member 2 books occurrence 2 → should succeed
        res2 = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ2},
            headers=_headers(member2_token),
        )
        assert res2.status_code == HTTPStatus.OK
        assert res2.json["enrolled"] == 1

    def test_occurrence_full_rejects_booking(
        self, client, trainer_token, member_token, member2_token,
        capacity_one_recurring_payload,
    ):
        """Booking a full occurrence should be rejected."""
        create_res = client.post(
            "/classes/", json=capacity_one_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        list_res = client.get("/classes/")
        occ1 = list_res.json["classes"][0]["occurrence_date"]

        client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member_token),
        )

        res = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member2_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "full" in res.json["message"].lower()

    # --- Bug #3 Fix: Same member can book multiple occurrences ---

    def test_same_member_books_multiple_occurrences(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        """A member can book different occurrences of the same class."""
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        list_res = client.get("/classes/")
        occ1 = list_res.json["classes"][0]["occurrence_date"]
        occ2 = list_res.json["classes"][1]["occurrence_date"]

        res1 = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member_token),
        )
        assert res1.status_code == HTTPStatus.OK

        res2 = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ2},
            headers=_headers(member_token),
        )
        assert res2.status_code == HTTPStatus.OK

    def test_duplicate_booking_same_occurrence_rejected(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        """Booking the same occurrence twice should be rejected."""
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        list_res = client.get("/classes/")
        occ1 = list_res.json["classes"][0]["occurrence_date"]

        client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member_token),
        )

        res = client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "already booked" in res.json["message"].lower()

    # --- Bug #2 Fix: Verify occurrence is recorded in DB ---

    def test_booking_records_occurrence_in_public_listing(
        self, client, trainer_token, member_token, daily_recurring_payload,
    ):
        """After booking, public listing shows per-occurrence enrolled count."""
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        list_res = client.get("/classes/")
        occ1 = list_res.json["classes"][0]["occurrence_date"]
        occ2 = list_res.json["classes"][1]["occurrence_date"]

        client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member_token),
        )

        list_res = client.get("/classes/")
        classes = list_res.json["classes"]

        booked_occ = [c for c in classes if c["occurrence_date"] == occ1][0]
        unbooked_occ = [c for c in classes if c["occurrence_date"] == occ2][0]

        assert booked_occ["enrolled"] == 1
        assert unbooked_occ["enrolled"] == 0

    # --- Occurrence-scoped members endpoint ---

    def test_get_members_for_specific_occurrence(
        self, client, trainer_token, member_token, member2_token,
        daily_recurring_payload,
    ):
        """POST /classes/<id>/members with occurrence_date returns that occurrence's members."""
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        list_res = client.get("/classes/")
        occ1 = list_res.json["classes"][0]["occurrence_date"]
        occ2 = list_res.json["classes"][1]["occurrence_date"]

        client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member_token),
        )
        client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ2},
            headers=_headers(member2_token),
        )

        res = client.post(
            f"/classes/{class_id}/members",
            json={"occurrence_date": occ1},
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.OK
        assert "recur_member@nyu.edu" in res.json["booked_members"]
        assert "recur_member2@nyu.edu" not in res.json["booked_members"]
        assert res.json["occurrence_date"] == occ1

    def test_get_members_all_occurrences(
        self, client, trainer_token, member_token, member2_token,
        daily_recurring_payload,
    ):
        """POST /classes/<id>/members without occurrence_date returns all members."""
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        list_res = client.get("/classes/")
        occ1 = list_res.json["classes"][0]["occurrence_date"]
        occ2 = list_res.json["classes"][1]["occurrence_date"]

        client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ1},
            headers=_headers(member_token),
        )
        client.post(
            f"/classes/{class_id}/book",
            json={"occurrence_date": occ2},
            headers=_headers(member2_token),
        )

        res = client.post(
            f"/classes/{class_id}/members",
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.OK
        assert len(res.json["booked_members"]) == 2


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

    def test_update_recurrence_also_updates_schedule(
        self, client, trainer_token, daily_recurring_payload,
    ):
        """Bug #4 fix: updating recurrence also updates the schedule (dtstart)."""
        create_res = client.post(
            "/classes/", json=daily_recurring_payload,
            headers=_headers(trainer_token),
        )
        class_id = create_res.json["id"]

        new_rule = {
            "frequency": "daily",
            "total_occurrences": 3,
        }
        res = client.patch(
            f"/classes/{class_id}/recurrence",
            json=new_rule,
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.OK
        assert res.json["class"]["schedule"] is not None

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
            "/classes/000000000000000000000000/recurrence",
            json={"frequency": "daily", "total_occurrences": 5},
            headers=_headers(trainer_token),
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert "Class not found" in res.json["message"]
