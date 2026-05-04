[![CI](https://github.com/Yashsh101/vizzy-chat-ai-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/Yashsh101/vizzy-chat-ai-backend/actions/workflows/ci.yml)

# Vizzy Chat AI Backend

FastAPI backend for a creative AI assistant with chat, prompt generation, chat history, preferences, streaming responses, and image generation support.

## Overview

This project was built as an AI backend internship assignment. It accepts natural-language creative requests, classifies intent, stores lightweight user memory, generates structured prompts, and returns consistent API responses suitable for a frontend client.

The codebase is intentionally small and modular:

- async FastAPI application
- SQLite with async SQLAlchemy
- memory layer for recent chat history and user preferences
- standardized responses and error handling
- SSE streaming endpoint
- Gemini/Imagen-ready provider layer with mock fallback

Repository: [github.com/Yashsh101/vizzy-chat-ai-backend](https://github.com/Yashsh101/vizzy-chat-ai-backend)

## Features

- `POST /api/chat` for structured AI chat responses
- `POST /api/chat/stream` for Server-Sent Events streaming
- `POST /api/generate-prompt` for prompt generation only
- `POST /api/images/generate` for image generation payloads
- `GET /api/history/{user_id}` for stored chat history
- `POST /api/preferences` and `GET /api/preferences/{user_id}` for user preferences
- `GET /api/health` for health checks
- consistent response envelope with `success`, `data`, `error`, `metadata`, `latency_ms`, and `provider`

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy asyncio
- aiosqlite
- Pydantic v2
- Google GenAI SDK
- Pytest
- Ruff
- Docker

## Project Structure

```text
app/
  api/
    routes.py
  core/
    config.py
    exceptions.py
    logging.py
    middleware.py
    responses.py
  db/
    base.py
    manage.py
    session.py
  models/
    chat.py
    preference.py
  schemas/
    base.py
    chat.py
    health.py
    image.py
    preference.py
  services/
    ai_service.py
    chat_service.py
    history_service.py
    image_service.py
    intent_classifier.py
    preference_service.py
    prompt_engine.py
  main.py
examples/
tests/
```

## Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create environment variables

```powershell
Copy-Item .env.example .env
```

### 4. Optional: initialize or reset the local database

```powershell
python -m app.db.manage init
python -m app.db.manage status --verbose
```

Reset only if the local SQLite schema is stale:

```powershell
python -m app.db.manage reset --yes
```

### 5. Run the backend

```powershell
uvicorn app.main:app --reload
```

Swagger docs:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Environment Variables

See [.env.example](C:/Users/syash/OneDrive/Desktop/vizzy-chat-ai-backend/.env.example).

Main variables:

- `APP_ENV`
- `DEBUG`
- `DATABASE_URL`
- `GEMINI_API_KEY`
- `GEMINI_TEXT_MODEL`
- `GEMINI_IMAGE_MODEL`
- `HISTORY_WINDOW`
- `ALLOWED_ORIGINS`

## API Endpoints

### Health

```bash
curl http://127.0.0.1:8000/api/health
```

### Chat

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d @examples/chat_request.json
```

### Streaming Chat

```bash
curl -N -X POST http://127.0.0.1:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"stream_user\",\"message\":\"Create a cinematic sci-fi poster with blue neon lighting\",\"user_type\":\"business\"}"
```

### Generate Prompt

```bash
curl -X POST http://127.0.0.1:8000/api/generate-prompt \
  -H "Content-Type: application/json" \
  -d @examples/generate_prompt_request.json
```

### Preferences

```bash
curl -X POST http://127.0.0.1:8000/api/preferences \
  -H "Content-Type: application/json" \
  -d @examples/preferences_request.json
```

### Image Generation

```bash
curl -X POST http://127.0.0.1:8000/api/images/generate \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"Create a clean ceramic mug hero shot\",\"user_type\":\"business\",\"count\":2,\"aspect_ratio\":\"1:1\"}"
```

## Response Format

All non-stream endpoints return:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2026-05-04T12:00:00+00:00"
  },
  "latency_ms": 12.3,
  "provider": "mock"
}
```

## Testing

Run checks:

```powershell
python -m ruff check .
python -m pytest
```

## Docker

Build:

```powershell
docker build -t vizzy-chat-ai-backend .
```

Run:

```powershell
docker run --env-file .env -p 8000:8000 vizzy-chat-ai-backend
```

## GitHub / About Section Guidance

If the GitHub repository “About” link is broken, fix it in the repository settings on GitHub:

1. Open the repository.
2. Click the gear icon in the “About” section.
3. Set the website/homepage to the correct deployed URL, API docs URL, or leave it blank if there is no deployment yet.

This repository itself now uses correct GitHub URLs in the README and CI badge.

## Notes

- The app runs without a Gemini key by falling back to mock providers.
- Local database files and cache folders should not be committed.
- The current structure is intentionally simple and suitable for internship review.
