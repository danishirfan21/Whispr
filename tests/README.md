# Whispr Test Suite

## Purpose

Tests exist to **enforce Whispr's constraints**, not to maximize coverage.

These tests guard against:
- Accidental feature creep
- Introduction of state or memory
- WhatsApp policy violations
- Conversational behavior

## Philosophy

Whispr is a deterministic utility: **audio → text**

Tests fail loudly if:
- Non-audio starts being processed
- State is introduced
- Rate limiting logic changes
- User-facing behavior becomes conversational

## What We Test

### 1. Audio-Only Contract
- Text-only WhatsApp message → ignored (200, no outbound message)
- Image/video/document → ignored
- Audio message → processed

### 2. Statelessness
- One request does not affect another
- No memory or cached data between requests
- No conversation context

### 3. Rate Limiting
- Rate limiting applies ONLY to audio messages
- Non-audio messages must never consume rate-limit tokens
- Limits are per-user, not global

### 4. Security
- Invalid Twilio signature → rejected (when enabled)
- Valid Twilio signature → accepted
- Invalid phone numbers → rejected

### 5. Response Format
- Transcripts are pure text (no emojis, no labels)
- Error messages are minimal and non-conversational
- No assistant-like language

## What We DON'T Test

- ❌ Whisper transcription accuracy
- ❌ OpenAI internals
- ❌ Real API calls (everything is mocked)
- ❌ Integration or end-to-end tests
- ❌ Performance or load tests

## Running Tests

```bash
# Run the complete test suite (recommended)
python run_all_tests.py

# Alternative: Run with pytest (may have environment issues)
pytest -v
pytest tests/test_audio_only_contract.py

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

**Note:** `run_all_tests.py` is the primary test runner. It provides:
- Complete test isolation (no real API calls)
- Clear, structured output
- 12 tests covering all core constraints
- Fast execution (~1 second)

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                     # Fixtures and test configuration
├── test_audio_only_contract.py    # Audio-only enforcement
├── test_statelessness.py          # No memory between requests
├── test_rate_limiting.py          # Rate limit only audio
├── test_security.py               # Signature verification
└── test_response_format.py        # Minimal, non-conversational responses
```

## Key Fixtures (conftest.py)

- `client` - FastAPI TestClient
- `mock_twilio_client` - Mocked Twilio client (manual use)
- `mock_twilio_client_autouse` - Auto-applied mock (prevents real API calls)
- `mock_audio_download` - Mocked audio download
- `mock_audio_transcribe` - Mocked transcription
- `reset_rate_limits` - Clears rate limits before each test

All tests run completely offline with no real API calls.

## Adding New Tests

Only add tests that:
1. Enforce a core constraint
2. Prevent regression to conversational behavior
3. Guard against WhatsApp policy violations

Keep tests:
- Small and readable
- Focused on one behavior
- Fast (no real API calls)
- Boring (no clever tricks)

## WhatsApp 2026 Compliance

These tests help ensure Whispr remains compliant with WhatsApp's utility and automation policies by:
- Enforcing pure utility behavior (no conversation)
- Preventing state or memory
- Ensuring minimal user-facing messages
- Maintaining deterministic, predictable behavior
