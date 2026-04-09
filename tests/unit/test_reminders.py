from http import HTTPStatus
import pytest
from unittest.mock import patch

# =========================================================================== #
# FIXTURES
# =========================================================================== #

@pytest.fixture
def trainer_token(client):
    client.post("/Authentication/register", json={
        "username": "TrainerRay", "email": "trainer_remind@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Trainer"
    })
    res = client.post("/Authentication/login", json={"email": "trainer_remind@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def member_token(client):
    client.post("/Authentication/register", json={
        "username": "MemberSam", "email": "member_remind@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member"
    })
    res = client.post("/Authentication/login", json={"email": "member_remind@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def setup_class_empty(client, trainer_token):
    """Creates a class with NO bookings."""
    payload = {
        "name": "Empty Class", "instructor": "TrainerRay",
        "schedule": "2027-04-10T08:00", "capacity": 10,
        "location": "Studio B", "description": "No one here yet"
    }
    res = client.post("/classes/", json=payload, headers={"Authorization": f"Bearer {trainer_token}"})
    return res.json["id"]

@pytest.fixture
def setup_class_booked(client, setup_class_empty, member_token):
    """Takes the empty class and books a member into it."""
    client.post(f"/classes/{setup_class_empty}/book", headers={"Authorization": f"Bearer {member_token}"})
    return setup_class_empty

# =========================================================================== #
# TESTS: POST /classes/<id>/send-reminder
# =========================================================================== #

@patch('app.apis.classes.send_email')
def test_send_reminder_success(mock_send_email, client, setup_class_booked, trainer_token):
    """Reminder sent successfully — verifies send_email is actually called."""
    mock_send_email.return_value = {'MessageId': 'mock-id-123'}
    res = client.post(f"/classes/{setup_class_booked}/send-reminder",
                      headers={"Authorization": f"Bearer {trainer_token}"})
    assert res.status_code == HTTPStatus.OK
    assert mock_send_email.called

def test_send_reminder_no_token(client, setup_class_booked):
    res = client.post(f"/classes/{setup_class_booked}/send-reminder")
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_send_reminder_member_forbidden(client, setup_class_booked, member_token):
    res = client.post(f"/classes/{setup_class_booked}/send-reminder",
                      headers={"Authorization": f"Bearer {member_token}"})
    assert res.status_code == HTTPStatus.FORBIDDEN

def test_send_reminder_not_found(client, trainer_token):
    res = client.post("/classes/fake_invalid_id/send-reminder",
                      headers={"Authorization": f"Bearer {trainer_token}"})
    assert res.status_code == HTTPStatus.NOT_FOUND

def test_send_reminder_no_bookings(client, setup_class_empty, trainer_token):
    res = client.post(f"/classes/{setup_class_empty}/send-reminder",
                      headers={"Authorization": f"Bearer {trainer_token}"})
    assert res.status_code == HTTPStatus.OK
    assert "No members booked" in res.json["message"]