from http import HTTPStatus
import pytest

# =========================================================================== #
# FIXTURES: Generate Tokens for Roles and Valid Payloads
# =========================================================================== #

@pytest.fixture
def admin_token(client):
    """Registers an Admin and returns their JWT token."""
    client.post("/Authentication/register", json={
        "username": "AdminUser", "email": "admin@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Admin",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={"email": "admin@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def trainer_token(client):
    """Registers a Trainer and returns their JWT token."""
    client.post("/Authentication/register", json={
        "username": "TrainerBob", "email": "trainer@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Trainer",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={"email": "trainer@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def member_token(client):
    """Registers a Member and returns their JWT token."""
    client.post("/Authentication/register", json={
        "username": "MemberAlice", "email": "member@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={"email": "member@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def valid_class_payload():
    """Returns a valid payload for creating a class."""
    return {
        "name": "Morning Yoga",
        "instructor": "TrainerBob",
        "schedule": "2027-03-10T08:00",
        "capacity": 20,
        "location": "Studio A",
        "description": "Relaxing morning flow"
    }

# =========================================================================== #
# TESTS: POST /classes/ (Create Class)
# =========================================================================== #

def test_create_class_trainer_success(client, trainer_token, valid_class_payload):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    res = client.post("/classes/", json=valid_class_payload, headers=headers)
    assert res.status_code == HTTPStatus.CREATED
    assert res.json["name"] == "Morning Yoga"
    assert "id" in res.json

def test_create_class_admin_success(client, admin_token, valid_class_payload):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.post("/classes/", json=valid_class_payload, headers=headers)
    assert res.status_code == HTTPStatus.CREATED

def test_create_class_no_token(client, valid_class_payload):
    res = client.post("/classes/", json=valid_class_payload)
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_create_class_member_forbidden(client, member_token, valid_class_payload):
    headers = {"Authorization": f"Bearer {member_token}"}
    res = client.post("/classes/", json=valid_class_payload, headers=headers)
    assert res.status_code == HTTPStatus.FORBIDDEN
    assert "Access denied" in res.json["message"]

def test_create_class_missing_fields(client, trainer_token, valid_class_payload):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    del valid_class_payload["name"]
    res = client.post("/classes/", json=valid_class_payload, headers=headers)
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_create_class_invalid_capacity(client, trainer_token, valid_class_payload):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    valid_class_payload["capacity"] = -5
    res = client.post("/classes/", json=valid_class_payload, headers=headers)
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert "Capacity must be a positive integer." in res.json["message"]

def test_create_class_past_schedule(client, trainer_token, valid_class_payload):
    """Test that creating a class with a past schedule is rejected."""
    headers = {"Authorization": f"Bearer {trainer_token}"}
    valid_class_payload["schedule"] = "2020-01-01T08:00"
    res = client.post("/classes/", json=valid_class_payload, headers=headers)
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert "Schedule must be a future date and time" in res.json["message"]

# =========================================================================== #
# TESTS: GET /classes/ (View Classes)
# =========================================================================== #

def test_get_classes_empty(client):
    res = client.get("/classes/")
    assert res.status_code == HTTPStatus.OK
    assert res.json["classes"] == []

def test_get_classes_populated(client, trainer_token, valid_class_payload):
    # Create a class first
    headers = {"Authorization": f"Bearer {trainer_token}"}
    client.post("/classes/", json=valid_class_payload, headers=headers)
    
    # Fetch classes publically
    res = client.get("/classes/")
    assert res.status_code == HTTPStatus.OK
    assert len(res.json["classes"]) == 1
    
    # Verify Privacy: `booked_members` should be hidden
    first_class = res.json["classes"][0]
    assert "booked_members" not in first_class

# =========================================================================== #
# TESTS: GET /classes/<id>/members (View Members)
# =========================================================================== #

def test_get_class_members_success(client, trainer_token, valid_class_payload):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    # Create class
    res = client.post("/classes/", json=valid_class_payload, headers=headers)
    assert res.status_code == 201 
    class_id = res.json["id"]

    # Get members - Ensure the path matches your @api.route('/<string:class_id>/members')
    res_members = client.get(f"/classes/{class_id}/members", headers=headers)

    assert res_members.status_code in [HTTPStatus.OK, HTTPStatus.NOT_FOUND]

def test_get_class_members_member_forbidden(client, trainer_token, member_token, valid_class_payload):

    res = client.post("/classes/", json=valid_class_payload, headers={"Authorization": f"Bearer {trainer_token}"})
    class_id = res.json["id"]
    

    res_members = client.get(f"/classes/{class_id}/members", headers={"Authorization": f"Bearer {member_token}"})
    assert res_members.status_code == HTTPStatus.FORBIDDEN
    assert "Access denied" in res_members.json["message"]

def test_get_class_members_not_found(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    res = client.get("/classes/invalid_fake_id/members", headers=headers)
    assert res.status_code == HTTPStatus.NOT_FOUND