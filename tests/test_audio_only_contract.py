"""Test audio-only contract enforcement."""
import pytest
from unittest.mock import patch, AsyncMock


def test_text_only_message_ignored(client, mock_twilio_client):
    """Text-only WhatsApp message must be ignored (no processing, no response)."""
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "Hello, this is a text message",
                "From": "whatsapp:+15551234567",
                "NumMedia": "0"
            }
        )
    
    assert response.status_code == 200
    # Verify no outbound message was sent
    mock_twilio_client.messages.create.assert_not_called()


def test_image_message_ignored(client, mock_twilio_client):
    """Image messages must be ignored."""
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/image.jpg",
                "MediaContentType0": "image/jpeg",
                "NumMedia": "1"
            }
        )
    
    assert response.status_code == 200
    mock_twilio_client.messages.create.assert_not_called()


def test_video_message_ignored(client, mock_twilio_client):
    """Video messages must be ignored."""
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/video.mp4",
                "MediaContentType0": "video/mp4",
                "NumMedia": "1"
            }
        )
    
    assert response.status_code == 200
    mock_twilio_client.messages.create.assert_not_called()


def test_document_message_ignored(client, mock_twilio_client):
    """Document messages must be ignored."""
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/document.pdf",
                "MediaContentType0": "application/pdf",
                "NumMedia": "1"
            }
        )
    
    assert response.status_code == 200
    mock_twilio_client.messages.create.assert_not_called()


def test_audio_message_processed(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Audio messages must be processed and transcription sent back."""
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
    # Verify audio was downloaded
    mock_audio_download.assert_called_once()
    # Verify audio was transcribed
    mock_audio_transcribe.assert_called_once()
    # Verify transcript was sent back
    mock_twilio_client.messages.create.assert_called_once()
    call_kwargs = mock_twilio_client.messages.create.call_args[1]
    assert call_kwargs['body'] == "This is a test transcript."
    assert call_kwargs['to'] == "whatsapp:+15551234567"


def test_multiple_media_only_processes_first_audio(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """When multiple media files sent, only first is processed if it's audio."""
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/audio.ogg",
                "MediaContentType0": "audio/ogg",
                "MediaUrl1": "https://api.twilio.com/test/image.jpg",
                "MediaContentType1": "image/jpeg",
                "NumMedia": "2"
            }
        )
    
    assert response.status_code == 200
    # Should process the first audio file
    mock_audio_download.assert_called_once()
    mock_audio_transcribe.assert_called_once()
    mock_twilio_client.messages.create.assert_called_once()
