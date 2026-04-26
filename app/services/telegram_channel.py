import os
import requests
from app.services.notification_channel import NotificationChannel


class TelegramChannel(NotificationChannel):
    """
    Concrete Strategy for Telegram notifications.
    Uses the Telegram Bot API to send messages.
    """

    TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    @property
    def channel_name(self) -> str:
        return 'telegram'

    def send(self, to: str, subject: str, body: str) -> dict:
        """
        Send a Telegram message to a user.

        Args:
            to:      Recipient's Telegram chat_id.
            subject: Used as the message title.
            body:    Main content of the message.

        Returns:
            Telegram API response dict.

        Raises:
            RuntimeError: If TELEGRAM_BOT_TOKEN is not set.
            requests.HTTPError: If the Telegram API returns an error.
        """
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN environment variable is not set."
            )

        url = self.TELEGRAM_API_URL.format(token=token)
        message = f"*{subject}*\n\n{body}"

        response = requests.post(url, json={
            "chat_id": to,
            "text": message,
            "parse_mode": "Markdown"
        })

        response.raise_for_status()
        return response.json()