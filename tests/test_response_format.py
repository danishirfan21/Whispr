"""Test user-facing response format is minimal and non-conversational."""
import pytest
from unittest.mock import patch


def test_transcript_is_pure_text(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Transcription response must be pure text with no formatting or labels."""
    mock_audio_transcribe.return_value = "This is the raw transcript."
    
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
    
    # Response must be pure transcript
    assert call['body'] == "This is the raw transcript."
    
    # Must not contain emojis
    assert "📝" not in call['body']
    assert "✅" not in call['body']
    assert "🎙️" not in call['body']
    
    # Must not contain labels or formatting
    assert "Transcript:" not in call['body']
    assert "*Transcript*" not in call['body']
    assert "Here is" not in call['body'].lower()
    assert "Result:" not in call['body']


def test_error_messages_are_minimal(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Error messages must be minimal and non-conversational."""
    # Force a transcription failure
    mock_audio_transcribe.return_value = None
    
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
    error_message = call['body']
    
    # Must be one of two allowed error messages
    allowed_errors = ["Could not transcribe audio.", "Audio processing failed."]
    assert error_message in allowed_errors
    
    # Must not contain emojis
    assert "⚠️" not in error_message
    assert "❌" not in error_message
    assert "⏱️" not in error_message
    
    # Must not be conversational
    assert "please" not in error_message.lower()
    assert "try again" not in error_message.lower()
    assert "sorry" not in error_message.lower()
    
    # Must not expose technical details
    assert "timeout" not in error_message.lower()
    assert "limit" not in error_message.lower()
    assert "size" not in error_message.lower()


def test_no_conversational_language_in_responses(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Responses must not contain conversational or assistant-like language."""
    mock_audio_transcribe.return_value = "Test message."
    
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
    message = call['body']
    
    # Forbidden conversational phrases
    forbidden_phrases = [
        "I ", "I've", "I'm", "I'll",
        "you", "your",
        "here is", "here's",
        "let me",
        "please",
        "thanks", "thank you",
        "sure", "okay",
        "help", "assist"
    ]
    
    message_lower = message.lower()
    for phrase in forbidden_phrases:
        assert phrase not in message_lower, f"Conversational phrase '{phrase}' found in response"
