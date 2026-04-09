from http import HTTPStatus
import pytest

# =========================================================================== #
# FIXTURES
# =========================================================================== #

@pytest.fixture
def trainer_token(client):
    client.post("/Authentication/register", json={
        "username": "TrainerDan", "email": "trainer_book@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Trainer"
    })
    res = client.post("/Authentication/login", json={"email": "trainer_book@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def member_token(client):
    client.post("/Authentication/register", json={
        "username": "MemberEve", "email": "member_book@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member"
    })
    res = client.post("/Authentication/login", json={"email": "member_book@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def member2_token(client):
    client.post("/Authentication/register", json={
        "username": "MemberFrank", "email": "member2_book@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member"
    })
    res = client.post("/Authentication/login", json={"email": "member2_book@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def setup_class(client, trainer_token):
    """Creates a class with a capacity of exactly 1 for testing 'class full'."""
    payload = {
        "name": "Capacity Test Yoga", "instructor": "TrainerDan",
        "schedule": "2027-03-10T08:00", "capacity": 1,
        "location": "Studio A", "description": "Small class"
    }
    res = client.post("/classes/", json=payload, headers={"Authorization": f"Bearer {trainer_token}"})
    return res.json["id"]

# =========================================================================== #
# TESTS: POST /classes/<id>/book
# =========================================================================== #

def test_book_class_success(client, setup_class, member_token):
    res = client.post(f"/classes/{setup_class}/book", headers={"Authorization": f"Bearer {member_token}"})
    assert res.status_code == HTTPStatus.OK

def test_book_class_no_token(client, setup_class):
    res = client.post(f"/classes/{setup_class}/book")
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_book_class_trainer_forbidden(client, setup_class, trainer_token):
    res = client.post(f"/classes/{setup_class}/book", headers={"Authorization": f"Bearer {trainer_token}"})
    assert res.status_code == HTTPStatus.FORBIDDEN
    assert "Only members can book" in res.json["message"]

def test_book_class_not_found(client, member_token):
    res = client.post("/classes/fake_invalid_id/book", headers={"Authorization": f"Bearer {member_token}"})
    assert res.status_code == HTTPStatus.NOT_FOUND
    assert "Class not found" in res.json["message"]

def test_book_class_duplicate(client, setup_class, member_token):
    # Member books the class the first time
    client.post(f"/classes/{setup_class}/book", headers={"Authorization": f"Bearer {member_token}"})
    
    # Member tries to book the exact same class again
    res = client.post(f"/classes/{setup_class}/book", headers={"Authorization": f"Bearer {member_token}"})
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_book_class_full(client, setup_class, member_token, member2_token):
    # First member books the only spot 
    client.post(f"/classes/{setup_class}/book", headers={"Authorization": f"Bearer {member_token}"})
    
    # Second member tries to book, but it's full
    res = client.post(f"/classes/{setup_class}/book", headers={"Authorization": f"Bearer {member2_token}"})
    assert res.status_code == HTTPStatus.BAD_REQUEST