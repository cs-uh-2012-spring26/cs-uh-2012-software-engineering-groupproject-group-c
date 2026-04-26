import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.email_channel import EmailChannel
from app.services.telegram_channel import TelegramChannel


# =========================================================================== #
# TESTS: EmailChannel
# =========================================================================== #

def test_email_channel_name():
    """EmailChannel returns correct channel name."""
    channel = EmailChannel()
    assert channel.channel_name == 'email'


@patch('app.services.email_channel.send_email')
def test_email_channel_send_success(mock_send_email):
    """EmailChannel.send() calls send_email with correct args."""
    mock_send_email.return_value = {'MessageId': 'test-123'}
    channel = EmailChannel()
    result = channel.send('test@example.com', 'Subject', 'Body')
    mock_send_email.assert_called_once_with('test@example.com', 'Subject', 'Body')
    assert result == {'MessageId': 'test-123'}


@patch('app.services.email_channel.send_email')
def test_email_channel_send_failure(mock_send_email):
    """EmailChannel.send() propagates exceptions from send_email."""
    mock_send_email.side_effect = RuntimeError("SES error")
    channel = EmailChannel()
    with pytest.raises(RuntimeError, match="SES error"):
        channel.send('test@example.com', 'Subject', 'Body')


# =========================================================================== #
# TESTS: TelegramChannel
# =========================================================================== #

def test_telegram_channel_name():
    """TelegramChannel returns correct channel name."""
    channel = TelegramChannel()
    assert channel.channel_name == 'telegram'


def test_telegram_channel_missing_token():
    """TelegramChannel.send() raises RuntimeError when token not set."""
    channel = TelegramChannel()
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
            channel.send('123456', 'Subject', 'Body')


@patch('app.services.telegram_channel.requests.post')
def test_telegram_channel_send_success(mock_post):
    """TelegramChannel.send() calls Telegram API correctly."""
    mock_response = MagicMock()
    mock_response.json.return_value = {'ok': True, 'result': {}}
    mock_post.return_value = mock_response

    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'fake-token'}):
        channel = TelegramChannel()
        result = channel.send('123456789', 'Test Subject', 'Test Body')

    mock_post.assert_called_once()
    call_json = mock_post.call_args[1]['json']
    assert call_json['chat_id'] == '123456789'
    assert 'Test Subject' in call_json['text']
    assert result == {'ok': True, 'result': {}}


@patch('app.services.telegram_channel.requests.post')
def test_telegram_channel_send_failure(mock_post):
    """TelegramChannel.send() raises HTTPError on API failure."""
    import requests
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("Bad Request")
    mock_post.return_value = mock_response

    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'fake-token'}):
        channel = TelegramChannel()
        with pytest.raises(requests.HTTPError):
            channel.send('123456789', 'Subject', 'Body')