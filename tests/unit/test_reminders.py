from http import HTTPStatus
import pytest
from unittest.mock import patch, MagicMock
import os
from app.services.email_service import send_email

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
        "schedule": "2026-04-10T08:00", "capacity": 10,
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

@patch('builtins.print')
def test_send_reminder_success(mock_print, client, setup_class_booked, trainer_token):
    res = client.post(f"/classes/{setup_class_booked}/send-reminder", headers={"Authorization": f"Bearer {trainer_token}"})
    assert res.status_code == HTTPStatus.OK
    assert mock_print.called

def test_send_reminder_no_token(client, setup_class_booked):
    res = client.post(f"/classes/{setup_class_booked}/send-reminder")
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_send_reminder_member_forbidden(client, setup_class_booked, member_token):
    res = client.post(f"/classes/{setup_class_booked}/send-reminder", headers={"Authorization": f"Bearer {member_token}"})
    assert res.status_code == HTTPStatus.FORBIDDEN

def test_send_reminder_not_found(client, trainer_token):
    res = client.post("/classes/fake_invalid_id/send-reminder", headers={"Authorization": f"Bearer {trainer_token}"})
    assert res.status_code == HTTPStatus.NOT_FOUND

def test_send_reminder_no_bookings(client, setup_class_empty, trainer_token):
    res = client.post(f"/classes/{setup_class_empty}/send-reminder", headers={"Authorization": f"Bearer {trainer_token}"})
    assert res.status_code == HTTPStatus.OK
    assert "No members booked" in res.json["message"]

# =========================================================================== #
# TESTS: email_service.py
# =========================================================================== #

@patch('app.apis.email_service.boto3.client')
def test_send_email_success(mock_boto_client):
    """Test successful email sending via SES."""
    mock_ses = MagicMock()
    mock_boto_client.return_value = mock_ses
    mock_ses.send_email.return_value = {'MessageId': 'test-id-123'}

    with patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'fake-key',
        'AWS_SECRET_ACCESS_KEY': 'fake-secret',
        'AWS_REGION': 'us-east-1',
        'SES_SENDER_EMAIL': 'sender@test.com'
    }):
        import app.apis.email_service as svc
        svc._ses_client = None

        result = send_email('recipient@test.com', 'Test Subject', 'Test Body')
        assert result['MessageId'] == 'test-id-123'


@patch('app.apis.email_service.boto3.client')
def test_send_email_missing_sender(mock_boto_client):
    """Test RuntimeError when SES_SENDER_EMAIL is not set."""
    import app.apis.email_service as svc
    svc._ses_client = None

    with patch.dict(os.environ, {}, clear=True):
        try:
            send_email('recipient@test.com', 'Subject', 'Body')
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert 'SES_SENDER_EMAIL' in str(e)


@patch('app.apis.email_service.boto3.client')
def test_send_email_ses_failure(mock_boto_client):
    """Test that SES ClientError propagates correctly."""
    from botocore.exceptions import ClientError
    mock_ses = MagicMock()
    mock_boto_client.return_value = mock_ses
    mock_ses.send_email.side_effect = ClientError(
        {'Error': {'Code': 'MessageRejected', 'Message': 'Not verified'}},
        'SendEmail'
    )

    with patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'fake-key',
        'AWS_SECRET_ACCESS_KEY': 'fake-secret',
        'AWS_REGION': 'us-east-1',
        'SES_SENDER_EMAIL': 'sender@test.com'
    }):
        import app.apis.email_service as svc
        svc._ses_client = None

        try:
            send_email('recipient@test.com', 'Subject', 'Body')
            assert False, "Should have raised ClientError"
        except ClientError:
            pass