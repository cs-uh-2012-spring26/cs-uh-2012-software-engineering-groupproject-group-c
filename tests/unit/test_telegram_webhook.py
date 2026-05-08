"""Tests for the Telegram webhook endpoint and related DB functions."""

import pytest
from unittest.mock import patch, MagicMock


MEMBER = {
    'username': 'testmember',
    'email': 'member@test.com',
    'password': 'SecurePass123!',
    'role': 'member',
    'phone': '0501234567'
}


# ---------------------------------------------------------------------------
# Webhook endpoint tests
# ---------------------------------------------------------------------------

class TestTelegramWebhookNoData:

    def test_no_body_returns_no_data(self, client):
        """Empty body is rejected by Flask-RESTX before reaching handler."""
        response = client.post('/telegram/webhook', data='',
                            content_type='application/json')
        assert response.status_code == 400

    def test_missing_chat_id_returns_no_chat_id(self, client):
        """Message with no chat object returns 'no chat_id'."""
        response = client.post('/telegram/webhook', json={'message': {}})
        assert response.status_code == 200
        assert response.get_json()['status'] == 'no chat_id'


class TestTelegramWebhookContactSharing:

    def test_contact_shared_user_found_links_account(self, client):
        """When user shares contact and phone matches, chat_id is saved."""
        payload = {
            'message': {
                'chat': {'id': 123456},
                'contact': {'phone_number': '+971501234567'}
            }
        }
        mock_user = {'email': 'member@test.com', 'role': 'member'}

        with patch('app.apis.telegram_webhook.users_db.get_user_by_phone',
                   return_value=mock_user) as mock_get, \
             patch('app.apis.telegram_webhook.users_db.update_chat_id') as mock_update, \
             patch('app.apis.telegram_webhook.requests.post') as mock_post:

            mock_post.return_value = MagicMock(status_code=200)
            response = client.post('/telegram/webhook', json=payload)

        assert response.status_code == 200
        assert response.get_json()['status'] == 'ok'
        mock_get.assert_called_once_with('1501234567')  # normalized: no +, last 10 digits
        mock_update.assert_called_once_with('member@test.com', '123456')

    def test_contact_shared_user_not_found_sends_error(self, client):
        """When phone number doesn't match any user, chat_id is not updated."""
        payload = {
            'message': {
                'chat': {'id': 999},
                'contact': {'phone_number': '0000000000'}
            }
        }

        with patch('app.apis.telegram_webhook.users_db.get_user_by_phone',
                   return_value=None), \
             patch('app.apis.telegram_webhook.users_db.update_chat_id') as mock_update, \
             patch('app.apis.telegram_webhook.requests.post'):

            response = client.post('/telegram/webhook', json=payload)

        assert response.status_code == 200
        assert response.get_json()['status'] == 'ok'
        mock_update.assert_not_called()

    def test_contact_shared_no_token_still_returns_ok(self, client):
        """If TELEGRAM_BOT_TOKEN is missing, webhook still returns ok gracefully."""
        payload = {
            'message': {
                'chat': {'id': 123},
                'contact': {'phone_number': '+971501234567'}
            }
        }
        mock_user = {'email': 'member@test.com'}

        with patch('app.apis.telegram_webhook.users_db.get_user_by_phone',
                   return_value=mock_user), \
             patch('app.apis.telegram_webhook.users_db.update_chat_id'), \
             patch('app.apis.telegram_webhook.os.environ.get', return_value=None):

            response = client.post('/telegram/webhook', json=payload)

        assert response.status_code == 200
        assert response.get_json()['status'] == 'ok'


class TestTelegramWebhookNonContactMessage:

    def test_non_contact_message_asks_for_contact(self, client):
        """Any message without contact triggers the contact request."""
        payload = {
            'message': {
                'chat': {'id': 777},
                'text': 'Hello'
            }
        }

        with patch('app.apis.telegram_webhook.requests.post') as mock_post, \
            patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'fake-token'}):
            mock_post.return_value = MagicMock(status_code=200)
            response = client.post('/telegram/webhook', json=payload)

        assert response.status_code == 200
        assert response.get_json()['status'] == 'ok'
        mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# DB function tests
# ---------------------------------------------------------------------------

class TestGetUserByPhone:

    def test_get_user_by_phone_found(self, client):
        """Returns user when phone number matches."""
        client.post('/Authentication/register', json=MEMBER)
        import app.db.users as users_db
        user = users_db.get_user_by_phone('0501234567')
        assert user is not None
        assert user['email'] == MEMBER['email']

    def test_get_user_by_phone_not_found(self, client):
        """Returns None when phone number has no match."""
        import app.db.users as users_db
        user = users_db.get_user_by_phone('0000000000')
        assert user is None


class TestUpdateChatId:

    def test_update_chat_id_success(self, client):
        """Stores telegram chat_id for an existing user."""
        client.post('/Authentication/register', json=MEMBER)
        import app.db.users as users_db
        updated = users_db.update_chat_id(MEMBER['email'], '999888777')
        assert updated is not None
        prefs = users_db.get_user_preferences(MEMBER['email'])
        assert prefs['telegram_chat_id'] == '999888777'