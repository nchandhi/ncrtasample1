# FastAPI Realtime Chat Backend

WebSocket-based API for Azure OpenAI Realtime chat (text and audio).

## Setup

1. Install dependencies:
```bash
cd api
pip install -r requirements.txt
```

2. Configure `.env` (use parent folder's .env)

3. Run server:
```bash
python main.py
```

Server runs on `http://localhost:8000`

## Endpoints

- `GET /` - Health check
- `WS /ws/text` - Text chat WebSocket
- `WS /ws/audio` - Audio chat WebSocket

## WebSocket Protocol

**Text Chat (`/ws/text`):**
- Client sends: `{"type": "message", "text": "hello"}`
- Server sends: `{"type": "text_delta", "delta": "..."}`
- Server sends: `{"type": "response_done"}`

**Audio Chat (`/ws/audio`):**
- Client sends: `{"type": "audio", "audio": "base64..."}`
- Server sends: `{"type": "audio_delta", "delta": "base64..."}`
- Server sends: `{"type": "user_transcript", "text": "..."}`
- Server sends: `{"type": "assistant_transcript_delta", "delta": "..."}`
- Server sends: `{"type": "response_done"}`
