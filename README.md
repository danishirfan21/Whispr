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
- Sends the **verbatim transcript back**, plus an **English translation** appended automatically when the voice note isn't in English
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

### 3. Deploy to Production

### 3. Deploy to Production

#### Option A: Vercel (Recommended - Free Serverless)

**✅ You're on the `vercel-deployment` branch - optimized for Vercel!**

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Add environment variables** in Vercel Dashboard → Settings → Environment Variables:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `TWILIO_ACCOUNT_SID` - From Twilio Console
   - `TWILIO_AUTH_TOKEN` - From Twilio Console  
   - `TWILIO_SENDER_NUMBER` - WhatsApp sandbox number (e.g., `whatsapp:+14155238886`)

4. **Redeploy** after adding env vars:
   ```bash
   vercel --prod
   ```

5. **Your webhook URL:** `https://your-app.vercel.app/webhook/whatsapp`

**Vercel Benefits:**
- ✅ Free tier (no credit card required)
- ✅ Auto-scaling
- ✅ Global CDN
- ✅ Zero maintenance

**Limitations:**
- ⏱️ 60-second timeout
- 📦 Best for audio < 5 minutes
- ❄️ Cold starts possible

---

#### Option B: Render/Railway (Traditional Server)

For longer audio files or persistent rate limiting, use the `main` branch:

```bash
git checkout main
```

**Render/Railway Config:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:** Same as Vercel

---

### 4. Configure WhatsApp Webhook

**In Twilio Console → WhatsApp Sandbox Settings:**

Set "When a message comes in" to your webhook URL:

**Vercel:**
```
https://your-app.vercel.app/webhook/whatsapp
```

**Render/Other:**
```
https://your-domain.com/webhook/whatsapp
```

**Method:** POST

---

## Usage

1. Send a voice note to your WhatsApp sandbox number
2. Receive the transcribed text automatically
3. That's it!
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
- ✅ Stateless (no history, no memory, no file writes)
- ✅ WhatsApp-policy-friendly
- ✅ Self-hosted
- ✅ Vercel-compatible (serverless ready)
- ✅ No feature creep

---

## Serverless Constraints (Vercel Branch)

This branch is optimized for serverless deployment with inherent limitations:

- ⏱️ **Max execution time**: ~60 seconds (Vercel timeout)
- 📦 **Large audio files may timeout**: Keep voice notes under 5 minutes
- ❄️ **Cold starts possible**: First request after inactivity may be slower
- 🔄 **Stateless by design**: No persistent storage, rate limiting resets
- 🔁 **Auto-retry**: 3 attempts with exponential backoff for reliability

For longer audio files or persistent rate limiting, use the `main` branch on Render/Railway.

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /webhook/whatsapp` | Twilio webhook (audio only) |
| `GET /health` | Health check |

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
MAX_REQUESTS_PER_HOUR=20  # Only effective on traditional servers (not Vercel)
VERIFY_TWILIO_SIGNATURE=false  # Set to true for production with proper webhook verification
ENABLE_RATE_LIMITING=false  # Recommended false for Vercel (in-memory state resets)
```

**Branch Differences:**
- `vercel-deployment` - Stateless, no file I/O, optimized for serverless
- `main` - Traditional server deployment with file system support

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