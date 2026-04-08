import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.email_service import send_email


@patch('app.services.email_service.boto3.client')
def test_send_email_success(mock_boto_client):
    """Test successful email sending via SES."""
    mock_ses = MagicMock()
    mock_boto_client.return_value = mock_ses
    mock_ses.send_email.return_value = {'MessageId': 'test-id-123'}

    with patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'fake-key',
        'AWS_SECRET_ACCESS_KEY': 'fake-secret',
        'AWS_REGION': 'us-east-1',
        'SES_SENDER_EMAIL': 'sender@test.com'
    }):
        import app.services.email_service as svc
        svc._ses_client = None

        result = send_email('recipient@test.com', 'Test Subject', 'Test Body')
        assert result['MessageId'] == 'test-id-123'


@patch('app.services.email_service.boto3.client')
def test_send_email_missing_sender(mock_boto_client):
    """Test RuntimeError when SES_SENDER_EMAIL is not set."""
    import app.services.email_service as svc
    svc._ses_client = None

    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match='SES_SENDER_EMAIL'):
            send_email('recipient@test.com', 'Subject', 'Body')


@patch('app.services.email_service.boto3.client')
def test_send_email_ses_failure(mock_boto_client):
    """Test that SES ClientError propagates correctly."""
    from botocore.exceptions import ClientError
    mock_ses = MagicMock()
    mock_boto_client.return_value = mock_ses
    mock_ses.send_email.side_effect = ClientError(
        {'Error': {'Code': 'MessageRejected', 'Message': 'Not verified'}},
        'SendEmail'
    )

    with patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'fake-key',
        'AWS_SECRET_ACCESS_KEY': 'fake-secret',
        'AWS_REGION': 'us-east-1',
        'SES_SENDER_EMAIL': 'sender@test.com'
    }):
        import app.services.email_service as svc
        svc._ses_client = None

        with pytest.raises(ClientError):
            send_email('recipient@test.com', 'Subject', 'Body')