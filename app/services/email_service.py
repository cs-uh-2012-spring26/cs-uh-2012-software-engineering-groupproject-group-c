import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError


# ---------------------------------------------------------------------------
# Module-level SES client (created once, reused across requests)
# ---------------------------------------------------------------------------
_ses_client = None


def _get_client():
    global _ses_client
    if _ses_client is None:
        _ses_client = boto3.client(
            "ses",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
    return _ses_client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_email(to_address: str, subject: str, body: str) -> dict:
    """
    Send a plain-text email via AWS SES.

    Args:
        to_address: Recipient email address.
        subject:    Email subject line.
        body:       Plain-text body of the email.

    Returns:
        The raw SES response dict (contains 'MessageId' on success).

    Raises:
        RuntimeError: If SES_SENDER_EMAIL env var is not set.
        ClientError / BotoCoreError: On AWS-level failures.
    """
    sender = os.environ.get("SES_SENDER_EMAIL")
    if not sender:
        raise RuntimeError(
            "SES_SENDER_EMAIL environment variable is not set. "
            "Add a verified sender address to your environment."
        )

    client = _get_client()

    response = client.send_email(
        Source=sender,
        Destination={"ToAddresses": [to_address]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body":    {"Text": {"Data": body,    "Charset": "UTF-8"}},
        },
    )
    return response

def get_class_reminder_template(class_data: dict) -> tuple:
    """
    Constructs the subject and body for a class reminder.
    Separating this allows marketing/copy changes without touching the loop or API.
    """
    name = class_data['name']
    schedule = class_data['schedule']
    
    subject = f"Reminder: {name} on {schedule}"
    body = (
        f"Hello,\n\n"
        f"This is a reminder for the fitness class you booked:\n\n"
        f"  Class Name : {name}\n"
        f"  Instructor : {class_data['instructor']}\n"
        f"  Date/Time  : {schedule}\n"
        f"  Location   : {class_data['location']}\n"
        f"  Description: {class_data.get('description') or 'N/A'}\n"
        f"  Spots Filled: {class_data['enrolled']} / {class_data['capacity']}\n\n"
        f"See you there!\n"
    )
    return subject, body

def send_batch_reminders(class_data: dict):
    """Purely handles the loop and email transport."""
    booked_members = class_data.get('booked_members', [])
    sent, failed = [], []

    if not booked_members:
        return sent, failed

    subject, body = get_class_reminder_template(class_data)

    for member_email in booked_members:
        try:
            send_email(member_email, subject, body)
            sent.append(member_email)
        except Exception as exc:
            failed.append({'email': member_email, 'reason': str(exc)})
            
    return sent, failed