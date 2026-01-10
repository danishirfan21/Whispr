"""Test rate limiting applies only to audio messages."""
import pytest
from unittest.mock import patch


def test_text_messages_do_not_consume_rate_limit(client, mock_twilio_client):
    """Text messages must never consume rate-limit tokens."""
    from app.rate_limit import check_rate_limit
    
    user_id = "whatsapp:+15551234567"
    
    # Check initial rate limit status
    initial_allowed = True
    
    # Send many text messages
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        for i in range(25):  # More than default rate limit
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "Body": f"Text message {i}",
                    "From": user_id,
                    "NumMedia": "0"
                }
            )
            assert response.status_code == 200
    
    # User should still be able to send audio (rate limit not consumed)
    import asyncio
    still_allowed = asyncio.run(check_rate_limit(user_id.replace("whatsapp:", "")))
    assert still_allowed, "Text messages consumed rate limit tokens"


def test_non_audio_media_does_not_consume_rate_limit(client, mock_twilio_client):
    """Non-audio media must never consume rate-limit tokens."""
    from app.rate_limit import check_rate_limit
    
    user_id = "whatsapp:+15551234567"
    
    # Send many image/video messages
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        for i in range(25):  # More than default rate limit
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "Body": "",
                    "From": user_id,
                    "MediaUrl0": f"https://api.twilio.com/test/image{i}.jpg",
                    "MediaContentType0": "image/jpeg",
                    "NumMedia": "1"
                }
            )
            assert response.status_code == 200
    
    # User should still be able to send audio (rate limit not consumed)
    import asyncio
    still_allowed = asyncio.run(check_rate_limit(user_id.replace("whatsapp:", "")))
    assert still_allowed, "Non-audio media consumed rate limit tokens"


def test_audio_messages_consume_rate_limit(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Audio messages must consume rate-limit tokens."""
    from app.config import settings
    
    user_id = "whatsapp:+15551234567"
    max_requests = settings.max_requests_per_hour
    
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        # Send max_requests audio messages
        for i in range(max_requests):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "Body": "",
                    "From": user_id,
                    "MediaUrl0": f"https://api.twilio.com/test/audio{i}.ogg",
                    "MediaContentType0": "audio/ogg",
                    "NumMedia": "1"
                }
            )
            assert response.status_code == 200
        
        # Next audio request should be rate limited
        mock_twilio_client.messages.create.reset_mock()
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": user_id,
                "MediaUrl0": "https://api.twilio.com/test/audio_extra.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            }
        )
        
        assert response.status_code == 200
        # Should send error message
        mock_twilio_client.messages.create.assert_called_once()
        call = mock_twilio_client.messages.create.call_args[1]
        assert call['body'] == "Audio processing failed."


def test_rate_limit_per_user(client, mock_twilio_client, mock_audio_download, mock_audio_transcribe):
    """Rate limits must be enforced per user, not globally."""
    from app.config import settings
    
    user_a = "whatsapp:+15551111111"
    user_b = "whatsapp:+15552222222"
    max_requests = settings.max_requests_per_hour
    
    with patch('app.twilio_webhook.get_twilio_client', return_value=mock_twilio_client):
        # User A hits rate limit
        for i in range(max_requests):
            client.post(
                "/webhook/whatsapp",
                data={
                    "Body": "",
                    "From": user_a,
                    "MediaUrl0": f"https://api.twilio.com/test/audioA{i}.ogg",
                    "MediaContentType0": "audio/ogg",
                    "NumMedia": "1"
                }
            )
        
        # User B should still be able to send audio
        mock_twilio_client.messages.create.reset_mock()
        response = client.post(
            "/webhook/whatsapp",
            data={
                "Body": "",
                "From": user_b,
                "MediaUrl0": "https://api.twilio.com/test/audioB.ogg",
                "MediaContentType0": "audio/ogg",
                "NumMedia": "1"
            }
        )
        
        assert response.status_code == 200
        # User B should get transcript (not rate limited)
        call = mock_twilio_client.messages.create.call_args[1]
        assert call['body'] == "This is a test transcript."
        assert call['body'] != "Audio processing failed."
