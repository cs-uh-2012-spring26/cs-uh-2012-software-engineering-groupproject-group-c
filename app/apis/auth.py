from typing import List
from app.services.notification_channel import NotificationChannel


class NotificationService:
    """
    Orchestrator for the Strategy Pattern.
    Dispatches notifications only to channels matching
    the user's preferences. Adding a new channel requires
    only registering it here — no other code changes needed.
    """

    def __init__(self, channels: List[NotificationChannel]):
        self.channels = {channel.channel_name: channel for channel in channels}

    def notify(self, to: str, subject: str, body: str,
               preferences: List[str],
               telegram_chat_id: str = None) -> dict:
        """
        Send notifications to all channels matching user preferences.

        Args:
            to:               Recipient email address.
            subject:          Notification subject/title.
            body:             Notification body content.
            preferences:      List of channel names the user selected.
            telegram_chat_id: Telegram chat_id if telegram is in preferences.

        Returns:
            Dict with sent and failed lists.
        """
        sent = []
        failed = []

        for preference in preferences:
            channel = self.channels.get(preference)
            if channel is None:
                failed.append({
                    'channel': preference,
                    'to': to,
                    'reason': f"Unknown channel: {preference}"
                })
                continue

            # Use correct recipient identifier per channel
            if preference == 'telegram':
                if not telegram_chat_id:
                    failed.append({
                        'channel': 'telegram',
                        'to': to,
                        'reason': 'No telegram_chat_id configured for this user'
                    })
                    continue
                recipient = telegram_chat_id
            else:
                recipient = to

            try:
                channel.send(recipient, subject, body)
                sent.append({'channel': preference, 'to': recipient})
            except Exception as exc:
                failed.append({
                    'channel': preference,
                    'to': recipient,
                    'reason': str(exc)
                })

        return {'sent': sent, 'failed': failed}