from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    """
    Abstract base class for the Strategy Pattern.
    Each concrete channel (Email, Telegram, SMS etc.)
    implements this interface. Adding a new channel
    requires only a new class with no changes to existing code.
    """

    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> dict:
        """
        Send a notification to a recipient.

        Args:
            to:      Recipient identifier (email address,
                     telegram chat_id, phone number etc.)
            subject: Subject or title of the notification.
            body:    Main content of the notification.

        Returns:
            A dict containing the result of the send operation.
        """
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """
        Returns the identifier string for this channel.
        Used to match against user preferences e.g. 'email', 'telegram'.
        """
        pass