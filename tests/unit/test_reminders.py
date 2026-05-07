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
        "password": "Password@123", "phone": "1234567890", "role": "Trainer",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={"email": "trainer_remind@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def member_token(client):
    client.post("/Authentication/register", json={
        "username": "MemberSam", "email": "member_remind@nyu.edu",
        "password": "Password@123", "phone": "1234567890", "role": "Member",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={"email": "member_remind@nyu.edu", "password": "Password@123"})
    return res.json["token"]

@pytest.fixture
def setup_class_empty(client, trainer_token):
    """Creates a non-recurring class with NO bookings."""
    payload = {
        "name": "Empty Class", "instructor": "TrainerRay",
        "schedule": "2027-04-10T08:00", "capacity": 10,
        "location": "Studio B", "description": "No one here yet"
    }
    res = client.post("/classes/", json=payload, headers={"Authorization": f"Bearer {trainer_token}"})
    return res.json["id"]

@pytest.fixture
def setup_class_booked(client, setup_class_empty, member_token):
    """Takes the empty class and books a member into it using occurrence_date."""
    client.post(
        f"/classes/{setup_class_empty}/book",
        json={"occurrence_date": "2027-04-10T08:00"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    return setup_class_empty

@pytest.fixture
def setup_recurring_class_booked(client, trainer_token, member_token):
    """Creates a recurring class and books a member for a specific occurrence."""
    payload = {
        "name": "Recurring Reminder Class", "instructor": "TrainerRay",
        "schedule": "2027-06-01T07:00", "capacity": 10,
        "location": "Studio C", "description": "Recurring class for reminders",
        "recurrence": {
            "frequency": "daily",
            "total_occurrences": 3,
        },
    }
    res = client.post("/classes/", json=payload, headers={"Authorization": f"Bearer {trainer_token}"})
    class_id = res.json["id"]

    # Get the first occurrence date
    list_res = client.get("/classes/")
    first_occ = list_res.json["classes"][0]["occurrence_date"]

    # Book the first occurrence
    client.post(
        f"/classes/{class_id}/book",
        json={"occurrence_date": first_occ},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    return {"class_id": class_id, "occurrence_date": first_occ}

# =========================================================================== #
# TESTS: POST /classes/<id>/send-reminder (non-recurring)
# =========================================================================== #
@patch('app.services.email_channel.send_email')
def test_send_reminder_success(mock_send_email, client, setup_class_booked, trainer_token):
    """Reminder sent successfully — verifies send_email is actually called."""
    mock_send_email.return_value = {'MessageId': 'mock-id-123'}
    res = client.post(
        f"/classes/{setup_class_booked}/send-reminder",
        json={"occurrence_date": "2027-04-10T08:00"},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
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
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_send_reminder_no_bookings(client, setup_class_empty, trainer_token):
    """Sending reminder with occurrence_date but no bookings for that occurrence."""
    res = client.post(
        f"/classes/{setup_class_empty}/send-reminder",
        json={"occurrence_date": "2027-04-10T08:00"},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert "No booked members for this class." in res.json["message"]

# =========================================================================== #
# TESTS: POST /classes/<id>/send-reminder (recurring with occurrence_date)
# =========================================================================== #

@patch('app.services.email_channel.send_email')
def test_send_reminder_recurring_with_occurrence(
    mock_send_email, client, setup_recurring_class_booked, trainer_token,
):
    """Reminder for a specific occurrence of a recurring class."""
    mock_send_email.return_value = {'MessageId': 'mock-id-456'}
    info = setup_recurring_class_booked
    res = client.post(
        f"/classes/{info['class_id']}/send-reminder",
        json={"occurrence_date": info["occurrence_date"]},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert res.status_code == HTTPStatus.OK
    assert mock_send_email.called
    assert res.json["results"]["total_sent"] == 1

@patch('app.services.email_channel.send_email')
def test_send_reminder_recurring_without_occurrence_sends_to_all(
    mock_send_email, client, setup_recurring_class_booked, trainer_token,
):
    """Reminder without occurrence_date sends to all booked members across occurrences."""
    mock_send_email.return_value = {'MessageId': 'mock-id-789'}
    info = setup_recurring_class_booked
    res = client.post(
        f"/classes/{info['class_id']}/send-reminder",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert res.status_code == HTTPStatus.OK
    assert mock_send_email.called

def test_send_reminder_recurring_no_bookings_for_occurrence(
    client, trainer_token,
):
    """Sending reminder for an occurrence with no bookings should fail."""
    payload = {
        "name": "No Booking Recur", "instructor": "TrainerRay",
        "schedule": "2027-06-01T07:00", "capacity": 10,
        "location": "Room Z",
        "recurrence": {"frequency": "daily", "total_occurrences": 3},
    }
    res = client.post("/classes/", json=payload,
                      headers={"Authorization": f"Bearer {trainer_token}"})
    class_id = res.json["id"]

    list_res = client.get("/classes/")
    occ2 = list_res.json["classes"][1]["occurrence_date"]

    res = client.post(
        f"/classes/{class_id}/send-reminder",
        json={"occurrence_date": occ2},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert "No booked members" in res.json["message"]