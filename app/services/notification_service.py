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
        """
        Args:
            channels: List of all available notification channels.
        """
        self.channels = {channel.channel_name: channel for channel in channels}

    def notify(self, to: str, subject: str, body: str, preferences: List[str]) -> dict:
        """
        Send notifications to all channels matching user preferences.

        Args:
            to:          Recipient identifier (email or chat_id).
            subject:     Notification subject/title.
            body:        Notification body content.
            preferences: List of channel names the user has selected
                         e.g. ['email'], ['telegram'], ['email', 'telegram']

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

            try:
                channel.send(to, subject, body)
                sent.append({'channel': preference, 'to': to})
            except Exception as exc:
                failed.append({
                    'channel': preference,
                    'to': to,
                    'reason': str(exc)
                })

        return {'sent': sent, 'failed': failed}