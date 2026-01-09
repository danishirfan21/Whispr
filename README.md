# 🎙️ Audio-to-Text Service

**Pure audio transcription using OpenAI Whisper** — Just audio in, text out.

## What It Does

- Receives audio files via WhatsApp
- Transcribes using OpenAI Whisper
- Sends transcript back
- **Ignores everything else** (text messages, images, videos, etc.)

## Quick Setup

### 1. Get API Keys

**OpenAI:**
- Go to [OpenAI Platform](https://platform.openai.com/api-keys)
- Create API key (starts with `sk-`)

**Twilio:**
- Go to [Twilio Console](https://console.twilio.com/)
- Copy `Account SID` and `Auth Token`
- Setup [WhatsApp Sandbox](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)

### 2. Install & Run

```bash
# Clone and install
git clone <repository-url>
cd audio-to-text
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
uvicorn app.main:app --reload
```

### 3. Configure Webhook

**Local testing (with ngrok):**
```bash
ngrok http 8000
# Set webhook URL in Twilio: https://your-ngrok-url.ngrok.io/webhook/whatsapp
```

**Production:**
```
# Set webhook URL in Twilio: https://yourdomain.com/webhook/whatsapp
```

## Usage

1. Send audio file to your WhatsApp number
2. Receive transcript back
3. That's it!

**What gets ignored:**
- Text messages (silently ignored)
- Images (silently ignored)
- Videos (silently ignored)  
- Documents (silently ignored)

## Features

- ✅ **Pure audio-to-text** - No AI features, no summaries, no chat
- ✅ **Rate limiting** - 20 requests/hour (configurable)
- ✅ **Secure** - Input validation, file size limits
- ✅ **Simple** - Does one thing well

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /webhook/whatsapp` | Twilio webhook (processes audio only) |
| `GET /health` | Health check |
| `GET /admin/stats` | System statistics |
| `POST /admin/cleanup` | Clean old data |

## Configuration

Only 4 environment variables required:

```bash
OPENAI_API_KEY=sk-your-key
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_SENDER_NUMBER=whatsapp:+14155238886
```

Optional settings (with defaults):
- `MAX_REQUESTS_PER_HOUR=20` - Rate limit
- `VERIFY_TWILIO_SIGNATURE=false` - Webhook security

## How It Works

```
1. Audio file → WhatsApp
2. Download audio → Twilio API
3. Transcribe → OpenAI Whisper API
4. Send transcript → WhatsApp
5. Delete audio file
```

**Processing limits:**
- Max file size: 25MB
- Min duration: 2 seconds
- Timeout: 30 seconds

## Deployment

Deploy to any Python hosting:
- **Render** (recommended)
- Railway
- Heroku
- Any VPS

Just set environment variables and deploy!

## License

MIT License