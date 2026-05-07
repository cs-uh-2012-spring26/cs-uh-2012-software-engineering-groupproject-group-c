from http import HTTPStatus
import pytest

# =========================================================================== #
# FIXTURES
# =========================================================================== #

@pytest.fixture
def trainer_token(client):
    client.post("/Authentication/register", json={
        "username": "TrainerDan", "email": "trainer_book@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Trainer",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={"email": "trainer_book@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def member_token(client):
    client.post("/Authentication/register", json={
        "username": "MemberEve", "email": "member_book@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={"email": "member_book@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def member2_token(client):
    client.post("/Authentication/register", json={
        "username": "MemberFrank", "email": "member2_book@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={"email": "member2_book@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def setup_class(client, trainer_token):
    """Creates a non-recurring class with capacity of 1 for testing 'class full'.
    Returns (class_id, occurrence_date) tuple."""
    payload = {
        "name": "Capacity Test Yoga", "instructor": "TrainerDan",
        "schedule": "2027-03-10T08:00", "capacity": 1,
        "location": "Studio A", "description": "Small class"
    }
    res = client.post("/classes/", json=payload, headers={"Authorization": f"Bearer {trainer_token}"})
    class_id = res.json["id"]
    # For non-recurring classes, occurrence_date = schedule
    occurrence_date = "2027-03-10T08:00"
    return class_id, occurrence_date

# =========================================================================== #
# TESTS: POST /classes/<id>/book  (non-recurring classes with occurrence_date)
# =========================================================================== #

def test_book_class_success(client, setup_class, member_token):
    class_id, occ = setup_class
    res = client.post(
        f"/classes/{class_id}/book",
        json={"occurrence_date": occ},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == HTTPStatus.OK

def test_book_class_no_token(client, setup_class):
    class_id, occ = setup_class
    res = client.post(f"/classes/{class_id}/book", json={"occurrence_date": occ})
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_book_class_trainer_forbidden(client, setup_class, trainer_token):
    class_id, occ = setup_class
    res = client.post(
        f"/classes/{class_id}/book",
        json={"occurrence_date": occ},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert res.status_code == HTTPStatus.FORBIDDEN
    assert "Access denied. Role should be: ['member']" in res.json["message"]

def test_book_class_not_found(client, member_token):
    res = client.post(
        "/classes/fake_invalid_id/book",
        json={"occurrence_date": "2027-03-10T08:00"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_book_class_missing_occurrence_date(client, setup_class, member_token):
    """Booking without occurrence_date should be rejected."""
    class_id, _ = setup_class
    res = client.post(
        f"/classes/{class_id}/book",
        json={},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_book_class_duplicate(client, setup_class, member_token):
    class_id, occ = setup_class
    # First booking
    client.post(
        f"/classes/{class_id}/book",
        json={"occurrence_date": occ},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    # Duplicate booking
    res = client.post(
        f"/classes/{class_id}/book",
        json={"occurrence_date": occ},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_book_class_full(client, setup_class, member_token, member2_token):
    class_id, occ = setup_class
    # First member books the only spot
    client.post(
        f"/classes/{class_id}/book",
        json={"occurrence_date": occ},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    # Second member tries to book — full
    res = client.post(
        f"/classes/{class_id}/book",
        json={"occurrence_date": occ},
        headers={"Authorization": f"Bearer {member2_token}"},
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST