"""Test security - signature verification."""
import pytest
from unittest.mock import patch, Mock


def test_invalid_signature_rejected(client, mock_twilio_client):
    """Requests with invalid Twilio signature must be rejected when verification enabled."""
    with patch('app.config.settings.verify_twilio_signature', True), \
         patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client), \
         patch('app.twilio_webhook.verify_twilio_signature') as mock_verify:
        
        # Mock signature verification to fail
        mock_verify.return_value = False
        
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/audio.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            },
            headers={"X-Twilio-Signature": "invalid_signature"}
        )
        
        # Should return 403 Forbidden
        assert response.status_code == 403
        # No message should be sent
        mock_twilio_client.messages.create.assert_not_called()


def test_valid_signature_accepted(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Requests with valid Twilio signature must be accepted when verification enabled."""
    with patch('app.config.settings.verify_twilio_signature', True), \
         patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client), \
         patch('app.twilio_webhook.verify_twilio_signature') as mock_verify:
        
        # Mock signature verification to succeed
        mock_verify.return_value = True
        
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "whatsapp:+15551234567",
                "MediaUrl0": "https://api.twilio.com/test/audio.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            },
            headers={"X-Twilio-Signature": "valid_signature"}
        )
        
        # Should process normally
        assert response.status_code == 200
        # Transcript should be sent
        mock_twilio_client.messages.create.assert_called_once()
        call = mock_twilio_client.messages.create.call_args[1]
        assert call['body'] == "This is a test transcript."


def test_signature_verification_disabled_by_default_in_tests(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """When signature verification disabled, requests without signature should be processed."""
    # Note: conftest.py sets verify_twilio_signature=False by default
    
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
            # No X-Twilio-Signature header
        )
        
        # Should process normally
        assert response.status_code == 200
        mock_twilio_client.messages.create.assert_called_once()


def test_invalid_phone_number_rejected(client, mock_twilio_client):
    """Requests with invalid phone number format must be rejected."""
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": "invalid_number",  # Invalid format
                "MediaUrl0": "https://api.twilio.com/test/audio.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            }
        )
        
        # Should return 400 Bad Request
        assert response.status_code == 400
        # No message should be sent
        mock_twilio_client.messages.create.assert_not_called()
