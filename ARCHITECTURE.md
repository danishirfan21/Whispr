# 🏗️ Whispr Architecture — WhatsApp-Compliant Audio-to-Text Utility (2026)

## Overview

Whispr is a **minimal, WhatsApp-policy-compliant audio-to-text utility**.

It is intentionally designed to do **exactly one thing**:

1. Receive WhatsApp audio messages  
2. Transcribe them into text using OpenAI Whisper  
3. Send the transcript back to the sender  

Whispr **does not** provide conversational AI, memory, summaries, or automated responses.

This design is intentional and aligned with **WhatsApp’s 2026 automation and utility policies**.


## Design Philosophy

### Policy-First by Design

Whispr is built as a **transformation utility**, not an AI agent.

WhatsApp 2026 policy strongly favors:
- Stateless services
- Deterministic transformations
- User-initiated actions
- No interpretation or decision-making

Whispr complies by enforcing:
- No conversation memory
- No contextual understanding
- No intent detection
- No automatic follow-ups
- No AI “personality”

### Extreme Simplicity

- Audio in → text out
- One request = one transformation
- No state beyond the request lifecycle
- No branching logic based on user input
- No feature inference

If a message is not audio, it is ignored.


## WhatsApp 2026 Policy Alignment

Whispr intentionally restricts its behavior to remain compliant with WhatsApp’s upcoming platform policies.

### Allowed
- Media transformation (audio → text)
- User-initiated requests
- Stateless processing
- Deterministic outputs
- Utility-style responses

### Explicitly Not Supported
- Conversational AI
- Chat memory or history
- Summarization or interpretation
- Question answering
- Multi-turn workflows
- Command processing
- Attachments beyond audio

These limitations are **deliberate safeguards**, not missing features.


## What Gets Ignored (By Design)

Whispr silently ignores all non-audio input.

Ignored inputs include:
- Text messages
- Images
- Videos
- Documents
- Stickers
- Locations
- Contacts
- Commands or keywords

### Why Silent Ignoring?

- Prevents accidental policy violations
- Avoids conversational expectations
- Keeps user mental model simple
- Reinforces: “This tool only handles audio”


## Philosophy

Whispr follows two principles:

1. **Unix Philosophy**  
   “Do one thing and do it well.”

2. **WhatsApp Utility Principle**  
   “Transform user-provided content without interpretation.”

Whispr is not an assistant.
It is not a chatbot.
It is not intelligent.

It is a small, reliable utility that removes the need to listen to long WhatsApp voice messages.

Audio → Text.
Nothing more.
