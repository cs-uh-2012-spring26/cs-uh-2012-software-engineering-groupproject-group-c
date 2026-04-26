import pytest
from unittest.mock import MagicMock
from app.services.notification_service import NotificationService


def make_channel(name):
    """Helper to create a mock channel with a given name."""
    channel = MagicMock()
    channel.channel_name = name
    return channel


# =========================================================================== #
# TESTS: NotificationService
# =========================================================================== #

def test_notify_email_only():
    """Dispatches only to email channel when preference is email."""
    email_channel = make_channel('email')
    telegram_channel = make_channel('telegram')
    service = NotificationService([email_channel, telegram_channel])

    result = service.notify(
        to='member@test.com',
        subject='Subject',
        body='Body',
        preferences=['email']
    )

    email_channel.send.assert_called_once_with('member@test.com', 'Subject', 'Body')
    telegram_channel.send.assert_not_called()
    assert len(result['sent']) == 1
    assert len(result['failed']) == 0


def test_notify_telegram_only():
    """Dispatches only to telegram channel when preference is telegram."""
    email_channel = make_channel('email')
    telegram_channel = make_channel('telegram')
    service = NotificationService([email_channel, telegram_channel])

    result = service.notify(
        to='member@test.com',
        subject='Subject',
        body='Body',
        preferences=['telegram'],
        telegram_chat_id='123456789'
    )

    telegram_channel.send.assert_called_once_with('123456789', 'Subject', 'Body')
    email_channel.send.assert_not_called()
    assert len(result['sent']) == 1
    assert len(result['failed']) == 0


def test_notify_both_channels():
    """Dispatches to both channels when both are in preferences."""
    email_channel = make_channel('email')
    telegram_channel = make_channel('telegram')
    service = NotificationService([email_channel, telegram_channel])

    result = service.notify(
        to='member@test.com',
        subject='Subject',
        body='Body',
        preferences=['email', 'telegram'],
        telegram_chat_id='123456789'
    )

    email_channel.send.assert_called_once()
    telegram_channel.send.assert_called_once()
    assert len(result['sent']) == 2
    assert len(result['failed']) == 0


def test_notify_telegram_without_chat_id():
    """Records failure when telegram is preferred but no chat_id provided."""
    telegram_channel = make_channel('telegram')
    service = NotificationService([telegram_channel])

    result = service.notify(
        to='member@test.com',
        subject='Subject',
        body='Body',
        preferences=['telegram'],
        telegram_chat_id=None
    )

    telegram_channel.send.assert_not_called()
    assert len(result['failed']) == 1
    assert 'No telegram_chat_id' in result['failed'][0]['reason']


def test_notify_unknown_channel():
    """Records failure for unknown channel preference."""
    email_channel = make_channel('email')
    service = NotificationService([email_channel])

    result = service.notify(
        to='member@test.com',
        subject='Subject',
        body='Body',
        preferences=['sms']
    )

    assert len(result['failed']) == 1
    assert 'Unknown channel' in result['failed'][0]['reason']


def test_notify_channel_send_failure():
    """Records failure gracefully when channel.send() raises exception."""
    email_channel = make_channel('email')
    email_channel.send.side_effect = Exception("SMTP error")
    service = NotificationService([email_channel])

    result = service.notify(
        to='member@test.com',
        subject='Subject',
        body='Body',
        preferences=['email']
    )

    assert len(result['sent']) == 0
    assert len(result['failed']) == 1
    assert 'SMTP error' in result['failed'][0]['reason']