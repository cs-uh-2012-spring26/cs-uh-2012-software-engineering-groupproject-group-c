from app.services.notification_channel import NotificationChannel
from app.services.email_service import send_email


class EmailChannel(NotificationChannel):
    """
    Concrete Strategy for email notifications.
    Wraps the existing email_service.send_email function.
    """

    @property
    def channel_name(self) -> str:
        return 'email'

    def send(self, to: str, subject: str, body: str) -> dict:
        """
        Send an email notification using AWS SES.

        Args:
            to:      Recipient email address.
            subject: Email subject line.
            body:    Plain-text email body.

        Returns:
            SES response dict containing MessageId on success.
        """
        return send_email(to, subject, body)