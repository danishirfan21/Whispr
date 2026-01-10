"""Test statelessness - no memory or cached data between requests."""
import pytest
from unittest.mock import patch, AsyncMock


def test_sequential_requests_independent(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Sequential audio requests from same user must be independent."""
    
    # First request
    mock_audio_transcribe.return_value = "First transcript."
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response1 = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/audio1.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            }
        )
    
    assert response1.status_code == 200
    first_call = mock_twilio_client.messages.create.call_args[1]
    assert first_call['body'] == "First transcript."
    
    # Reset mock
    mock_twilio_client.messages.create.reset_mock()
    
    # Second request - different transcript
    mock_audio_transcribe.return_value = "Second transcript."
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response2 = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/audio2.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            }
        )
    
    assert response2.status_code == 200
    second_call = mock_twilio_client.messages.create.call_args[1]
    # Must return second transcript, not first
    assert second_call['body'] == "Second transcript."
    assert second_call['body'] != "First transcript."


def test_different_users_independent(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Requests from different users must not affect each other."""
    
    # User A request
    mock_audio_transcribe.return_value = "User A transcript."
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response_a = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551111111",
                "MediaUrl0": "https://api.twilio.com/test/audioA.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            }
        )
    
    assert response_a.status_code == 200
    call_a = mock_twilio_client.messages.create.call_args[1]
    assert call_a['body'] == "User A transcript."
    assert call_a['to'] == "whatsapp:+15551111111"
    
    # Reset mock
    mock_twilio_client.messages.create.reset_mock()
    
    # User B request
    mock_audio_transcribe.return_value = "User B transcript."
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response_b = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15552222222",
                "MediaUrl0": "https://api.twilio.com/test/audioB.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            }
        )
    
    assert response_b.status_code == 200
    call_b = mock_twilio_client.messages.create.call_args[1]
    # User B must get their own transcript, not User A's
    assert call_b['body'] == "User B transcript."
    assert call_b['to'] == "whatsapp:+15552222222"
    assert call_b['body'] != "User A transcript."


def test_no_conversation_context(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Transcription must not reference previous messages or context."""
    
    # Send text message first (ignored)
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        client.post(
            "/webhook/whatsapp",
            data={
                "Body": "What is the weather like?",
                "From": "whatsapp:+15551234567",
                "NumMedia": "0"
            }
        )
    
    # Send audio - should only return transcript, no reference to previous text
    mock_audio_transcribe.return_value = "Please tell me about Python."
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/audio.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            }
        )
    
    assert response.status_code == 200
    call = mock_twilio_client.messages.create.call_args[1]
    # Response must be pure transcript only
    assert call['body'] == "Please tell me about Python."
    # No conversational context or reference to weather
    assert "weather" not in call['body'].lower()
