"""Test configuration and fixtures."""
import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

# Set test environment variables before any imports
os.environ.setdefault('OPENAI_API_KEY', 'sk-test-key-for-testing')
os.environ.setdefault('TWILIO_ACCOUNT_SID', 'test_account_sid')
os.environ.setdefault('TWILIO_AUTH_TOKEN', 'test_auth_token')
os.environ.setdefault('TWILIO_SENDER_NUMBER', 'whatsapp:+15555555555')
os.environ.setdefault('VERIFY_TWILIO_SIGNATURE', 'false')


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock_client = Mock()
    mock_client.audio = Mock()
    mock_client.audio.transcriptions = Mock()
    mock_client.audio.transcriptions.create = AsyncMock()
    return mock_client


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client."""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "test_message_sid_12345"
    mock_client.messages.create.return_value = mock_message
    return mock_client


@pytest.fixture(autouse=True)
def mock_twilio_client_autouse():
    """Automatically mock get_twilio_client to prevent real Twilio API calls."""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "test_message_sid_12345"
    mock_client.messages.create.return_value = mock_message
    
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_twilio_send():
    """Mock the _send_twilio_message function to prevent real API calls."""
    with patch('app.twilio_webhook._send_twilio_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = Mock(sid="SM_test_message_id")
        yield mock_send


@pytest.fixture
def client():
    """FastAPI test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_audio_download():
    """Mock audio download function."""
    with patch('app.whisper_utils.download_audio') as mock:
        mock.return_value = "/tmp/test_audio.ogg"
        yield mock


@pytest.fixture
def mock_audio_transcribe():
    """Mock audio transcription function."""
    with patch('app.whisper_utils.transcribe_audio') as mock:
        mock.return_value = "This is a test transcript."
        yield mock


@pytest.fixture
def valid_whatsapp_form_data():
    """Valid WhatsApp audio message form data."""
    return {
        "Body": "",
        "From": "whatsapp:+15551234567",
        "MediaUrl0": "https://api.twilio.com/test/media.ogg",
        "MediaContentType0": "audio/ogg",
        "NumMedia": "1"
    }


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limits before each test."""
    from app.rate_limit import reset_rate_limits
    reset_rate_limits()
    yield
    reset_rate_limits()

