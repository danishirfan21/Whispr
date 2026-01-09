# 🎙️ Whispr — WhatsApp Audio-to-Text Utility

Never listen to long WhatsApp voice notes again.  
Whispr converts WhatsApp audio messages into text.  
That's all it does.

**Audio in → text out.**

---

## What Whispr Is

Whispr is a **minimal, self-hosted WhatsApp utility** that:

- Receives **audio messages only**
- Transcribes them using **OpenAI Whisper**
- Sends the **verbatim transcript back**
- **Silently ignores everything else**

No chat.  
No summaries.  
No memory.  
No automation.

This design is intentional and aligned with **WhatsApp 2026 utility and automation policies**.

---

## What Whispr Is Not

Whispr is **not**:

- a chatbot
- a voice assistant
- a conversational AI
- a summarization tool
- a workflow engine

If you send anything other than audio, **Whispr does nothing**.

---

## Why This Exists

WhatsApp voice notes are often:

- long  
- inconvenient  
- impossible to skim  
- hard to use in public or at work  

Whispr removes the need to listen.

Once you have text, you can:

- read it  
- search it  
- copy it  
- forward it  
- paste it into ChatGPT or any other tool  

Whispr stops at transcription by design.

---

## Quick Setup

### 1. Get API Keys

#### OpenAI
- https://platform.openai.com/api-keys
- Create an API key (`sk-...`)

#### Twilio
- https://console.twilio.com/
- Copy:
  - Account SID
  - Auth Token
- Set up WhatsApp Sandbox:  
  https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

---

### 2. Install & Run Locally

```bash
git clone <repository-url>
cd whispr
pip install -r requirements.txt

cp .env.example .env
# add your API keys

uvicorn app.main:app --reload
```

---

### 3. Configure WhatsApp Webhook

**Local testing (ngrok):**

```bash
ngrok http 8000
```

Set webhook URL in Twilio:
```
https://your-ngrok-url.ngrok.io/webhook/whatsapp
```

**Production:**
```
https://yourdomain.com/webhook/whatsapp
```

---

## Usage

1. Send a voice note to your WhatsApp number
2. Receive the transcribed text
3. Done

---

## Silently Ignored Inputs

- Text messages
- Images
- Videos
- Documents
- Stickers
- Locations
- Contacts

This is intentional to keep behavior predictable and compliant.

---

## Features

- ✅ Pure audio-to-text
- ✅ Stateless (no history, no memory)
- ✅ WhatsApp-policy-friendly
- ✅ Self-hosted
- ✅ Rate-limited
- ✅ No feature creep

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /webhook/whatsapp` | Twilio webhook (audio only) |
| `GET /health` | Health check |
| `GET /admin/stats` | Rate-limit stats |
| `POST /admin/cleanup` | Cleanup old temp files |

---

## Configuration

### Required (4 variables)

```bash
OPENAI_API_KEY
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_SENDER_NUMBER
```

### Optional

```bash
MAX_REQUESTS_PER_HOUR=20
VERIFY_TWILIO_SIGNATURE=false
```

---

## How It Works

1. WhatsApp audio message
2. Twilio webhook → Whispr
3. Audio download
4. Whisper transcription
5. Transcript sent back
6. Audio deleted

---

## Limits

- Max file size: 25MB
- Min duration: 2 seconds
- Processing timeout: 30 seconds

---

## Deployment

Whispr runs on any Python hosting:

- Render (recommended)
- Railway
- Heroku
- VPS
- Docker
- Kubernetes

Set environment variables and deploy.

---

## Non-Goals (Important)

Whispr will **never** include:

- Chat or conversational AI
- Summarization
- Memory or context
- Intent detection
- Commands or workflows

These are deliberately excluded to keep Whispr simple, safe, and reliable.

---

## License

MIT License