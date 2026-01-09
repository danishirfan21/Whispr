# 🏗️ Architecture - Pure Audio-to-Text Service

## Overview

This is a **pure audio-to-text transcription service**. It does exactly one thing:
1. Receives audio files via WhatsApp
2. Transcribes them using OpenAI Whisper
3. Sends the transcript back

Everything else is ignored.

## Design Philosophy

**Extreme Simplicity**
- No AI features (no chat, no summaries, no intelligence)
- No conversation memory
- No state management
- No button interactions
- No text processing
- Pure utility: audio in → text out

## File Structure

```
app/
├── main.py              # FastAPI app (60 lines)
├── twilio_webhook.py    # Webhook handler (170 lines)
├── whisper_utils.py     # Audio processing (140 lines)
├── config.py            # Settings (30 lines)
├── constants.py         # Constants (20 lines)
├── deps.py              # DI (15 lines)
├── utils.py             # Utilities (5 lines)
├── validators.py        # Validation (15 lines)
├── rate_limit.py        # Rate limiting (70 lines)
├── middleware.py        # Logging (15 lines)
└── health.py            # Health checks (40 lines)

Total: ~580 lines of actual code
```

## Request Flow

### Audio Message Flow

```
1. WhatsApp → Twilio → /webhook/whatsapp
2. Validate: phone number, rate limit
3. Check: Is it audio? (if not → ignore silently)
4. Download: Audio file from Twilio
5. Transcribe: OpenAI Whisper API
6. Validate: Duration, quality checks
7. Send: Transcript via WhatsApp
8. Cleanup: Delete audio file
```

### Non-Audio Message Flow

```
1. WhatsApp → Twilio → /webhook/whatsapp
2. Validate: phone number, rate limit
3. Check: Is it audio? NO
4. Return: Empty 200 response (ignore silently)
```

## What Gets Ignored

**Silently ignored (no response sent):**
- Text messages
- Images
- Videos
- Documents
- Stickers
- Locations
- Contacts
- Any non-audio media

**Why silent?** 
- Clean user experience
- No confusion
- No unnecessary messages
- Users learn: audio only

## API Design

### Webhook Endpoint

```
POST /webhook/whatsapp
- Accepts: Twilio webhook payload
- Processes: Audio files only
- Returns: 200 (empty response)
- Side effect: Sends transcript via WhatsApp
```

### Admin Endpoints

```
GET /health          - Service health
GET /admin/stats     - Rate limit stats
POST /admin/cleanup  - Clean old data
```

## Security Features

1. **Phone Number Validation**
   - WhatsApp format required
   - Prevents invalid requests

2. **Rate Limiting**
   - Token bucket algorithm
   - 20 requests/hour default
   - Per-user limits

3. **File Size Limits**
   - Max 25MB audio files
   - Prevents abuse

4. **Input Validation**
   - URL validation
   - Filename security
   - Path traversal prevention

5. **Optional Signature Verification**
   - Twilio webhook signatures
   - Disabled by default for simplicity

## Quality Controls

**Audio Quality Checks:**
- Min duration: 2 seconds (prevents noise)
- Max words/second: 2.5 (detects gibberish)
- Timeout: 30 seconds (prevents hanging)

**Rejection Reasons:**
- Too short (< 2 seconds)
- Too fast (likely gibberish)
- Download failed
- Transcription failed
- Timeout

## Error Handling

**User-Facing Errors:**
```
⚠️ Rate limit exceeded
⏱️ Audio processing timeout
❌ Could not transcribe audio
⚠️ Only audio files supported
❌ Processing error occurred
```

**Logging:**
- Request ID for tracing
- Processing time metrics
- Error details with context
- Quality check results

## Dependencies

**Core (10 packages):**
```
fastapi      - Web framework
uvicorn      - ASGI server
pydantic     - Settings management
openai       - Whisper API
twilio       - WhatsApp integration
aiohttp      - HTTP client
anyio        - Async utilities
python-dotenv - Environment
python-multipart - Form data
```

**No unnecessary dependencies:**
- No database
- No Redis
- No Celery
- No complex queue systems

## Scalability

**Current Design:**
- Stateless (scales horizontally)
- In-memory rate limiting (simple, fast)
- No database (no bottleneck)
- Async/await throughout

**Scaling Considerations:**
- Add Redis for distributed rate limiting
- Add queue system for heavy load
- Current design handles 100s of requests/day easily

## Configuration

**Required (4 env vars):**
```bash
OPENAI_API_KEY
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_SENDER_NUMBER
```

**Optional (defaults provided):**
```bash
MAX_REQUESTS_PER_HOUR=20
VERIFY_TWILIO_SIGNATURE=false
```

## Deployment

**Works on:**
- Render
- Railway
- Heroku
- Any Python hosting
- Docker
- Kubernetes

**Requirements:**
- Python 3.8+
- 512MB RAM minimum
- HTTPS endpoint (for Twilio)

## Monitoring

**Built-in:**
- Request logging (timing, status)
- Health checks (OpenAI, Twilio)
- Rate limit stats
- Error tracking

**Metrics Available:**
- Requests per user
- Processing times
- Success/failure rates
- Active users

## Future Considerations

**If you want to add features later:**

❌ **Don't add:**
- Conversation memory
- AI chat features
- Complex workflows
- State management

✅ **Could add:**
- Language detection
- Multiple output formats
- Batch processing
- Webhook retries
- Database logging (analytics)

## Philosophy

> "Do one thing and do it well."
> - Unix Philosophy

This service transcribes audio. That's it. That's the feature.

No feature creep. No complexity. Just audio → text.