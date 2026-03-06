from http import HTTPStatus
import pytest

# Helper fixture for a valid registration payload
@pytest.fixture
def valid_register_payload():
    return {
        "username": "Ahmed",
        "email": "ahmed@gmail.com",
        "password": "StrongPassword@123",
        "phone": "1234567890",
        "role": "Member"
    }

# --------------------------------------------------------------------------- #
# REGISTRATION TESTS
# --------------------------------------------------------------------------- #

def test_register_success(client, valid_register_payload):
    response = client.post("/Authentication/register", json=valid_register_payload)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json['message'] == 'User registered successfully'
    assert 'user_id' in response.json

def test_register_missing_fields(client, valid_register_payload):
    # Remove password to simulate missing field
    del valid_register_payload['password']
    response = client.post("/Authentication/register", json=valid_register_payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Missing required fields: password" in response.json['message']

def test_register_weak_password(client, valid_register_payload):
    valid_register_payload['password'] = "weak"
    response = client.post("/Authentication/register", json=valid_register_payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "password must be at least 8 characters long" in response.json['message']

def test_register_invalid_phone(client, valid_register_payload):
    valid_register_payload['phone'] = "12345" # Not 10 digits
    response = client.post("/Authentication/register", json=valid_register_payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid phone number format" in response.json['message']

def test_register_invalid_role(client, valid_register_payload):
    valid_register_payload['role'] = "SuperAdmin" # Not in allowed list
    response = client.post("/Authentication/register", json=valid_register_payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid role" in response.json['message']

def test_register_duplicate_email(client, valid_register_payload):
    # Register once
    client.post("/Authentication/register", json=valid_register_payload)
    # Register again with the same email
    response = client.post("/Authentication/register", json=valid_register_payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Email already registered" in response.json['message']

# --------------------------------------------------------------------------- #
# LOGIN TESTS
# --------------------------------------------------------------------------- #

def test_login_success(client, valid_register_payload):
    # Register first
    client.post("/Authentication/register", json=valid_register_payload)
    
    # Login
    login_payload = {
        "email": valid_register_payload["email"],
        "password": valid_register_payload["password"]
    }
    response = client.post("/Authentication/login", json=login_payload)
    assert response.status_code == HTTPStatus.OK
    assert "token" in response.json
    assert response.json["role"] == "member" # Notice in users.py it saves role as lowercase

def test_login_missing_fields(client):
    response = client.post("/Authentication/login", json={"email": "ahmed@gmail.com"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Missing required fields: password" in response.json['message']

def test_login_invalid_credentials(client, valid_register_payload):
    client.post("/Authentication/register", json=valid_register_payload)
    
    # Try wrong password
    login_payload = {
        "email": valid_register_payload["email"],
        "password": "WrongPassword@123"
    }
    response = client.post("/Authentication/login", json=login_payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Invalid email or password" in response.json['message']