from http import HTTPStatus
import pytest


# =========================================================================== #
# FIXTURES
# =========================================================================== #

@pytest.fixture
def member_token(client):
    client.post("/Authentication/register", json={
        "username": "PrefMember",
        "email": "pref_member@nyu.edu",
        "password": "Password@123",
        "phone": "1234567890",
        "role": "Member",
        "notification_preferences": ["email"]
    })
    res = client.post("/Authentication/login", json={
        "email": "pref_member@nyu.edu",
        "password": "Password@123"
    })
    return res.json["token"]


# =========================================================================== #
# TESTS: PATCH /Authentication/preferences
# =========================================================================== #

def test_update_preferences_email_only(client, member_token):
    """Member can update preferences to email only."""
    res = client.patch("/Authentication/preferences",
        json={"notification_preferences": ["email"]},
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert res.status_code == HTTPStatus.OK
    assert res.json["notification_preferences"] == ["email"]


def test_update_preferences_telegram(client, member_token):
    """Member can update preferences to include telegram with chat_id."""
    res = client.patch("/Authentication/preferences",
        json={
            "notification_preferences": ["email", "telegram"],
            "telegram_chat_id": "123456789"
        },
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert res.status_code == HTTPStatus.OK
    assert "telegram" in res.json["notification_preferences"]
    assert res.json["telegram_chat_id"] == "123456789"


def test_update_preferences_telegram_missing_chat_id(client, member_token):
    """Returns 400 when telegram selected but no chat_id provided."""
    res = client.patch("/Authentication/preferences",
        json={"notification_preferences": ["telegram"]},
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert "telegram_chat_id" in res.json["message"]


def test_update_preferences_invalid_channel(client, member_token):
    """Returns 400 for unknown notification channel."""
    res = client.patch("/Authentication/preferences",
        json={"notification_preferences": ["sms"]},
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST


def test_update_preferences_no_token(client):
    """Returns 400 when no token provided."""
    res = client.patch("/Authentication/preferences",
        json={"notification_preferences": ["email"]}
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST


def test_register_with_telegram_preferences(client):
    """User can register with telegram preferences and chat_id."""
    res = client.post("/Authentication/register", json={
        "username": "TelegramUser",
        "email": "telegram_user@nyu.edu",
        "password": "Password@123",
        "phone": "1234567890",
        "role": "Member",
        "notification_preferences": ["email", "telegram"],
        "telegram_chat_id": "987654321"
    })
    assert res.status_code == HTTPStatus.CREATED


def test_register_with_invalid_channel(client):
    """Returns 400 when registering with invalid notification channel."""
    res = client.post("/Authentication/register", json={
        "username": "BadUser",
        "email": "bad_user@nyu.edu",
        "password": "Password@123",
        "phone": "1234567890",
        "role": "Member",
        "notification_preferences": ["sms"]
    })
    assert res.status_code == HTTPStatus.BAD_REQUEST


def test_register_telegram_without_chat_id(client):
    """Returns 400 when registering with telegram but no chat_id."""
    res = client.post("/Authentication/register", json={
        "username": "NoIdUser",
        "email": "noid_user@nyu.edu",
        "password": "Password@123",
        "phone": "1234567890",
        "role": "Member",
        "notification_preferences": ["telegram"]
    })
    assert res.status_code == HTTPStatus.BAD_REQUEST