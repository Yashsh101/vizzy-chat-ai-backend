[![CI](https://github.com/your-github-username/vizzy-chat-ai-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/your-github-username/vizzy-chat-ai-backend/actions/workflows/ci.yml)

# Vizzy Chat AI Backend

Real-time, memory-aware FastAPI backend for creative AI products with streaming chat, Gemini text generation, and Imagen-powered image generation.

## What This Project Solves

Most AI creative products fail in one of two ways:

- they expose raw model calls with no product-layer structure
- they feel responsive in demos, but break down when you need memory, streaming, image generation, stable configuration, and deployment hygiene

Vizzy Chat is the backend layer that closes that gap. It takes natural-language creative requests, classifies user intent, remembers recent context and saved preferences, generates polished prompts, streams responses in real time, and can create actual images through Gemini Imagen with a clean fallback path when credentials are not available.

## Key Features

- Async FastAPI backend with non-blocking routes and async SQLAlchemy
- Standardized API envelope with `success`, `data`, `error`, `metadata`, `latency_ms`, and `provider`
- Streaming chat over Server-Sent Events at `POST /api/chat/stream`
- Gemini text integration with mock fallback
- Imagen image generation at `POST /api/images/generate`
- Memory-aware responses using the last 3 chats and saved user preferences
- Intent classification with `intent`, `confidence`, `reasoning`, and `pathway`
- Request IDs, latency tracking, logging, validation, and structured errors
- Secure-ish container setup with non-root user and Docker healthcheck
- GitHub Actions CI for lint and tests

## Architecture

```text
Client
  |
  v
FastAPI Routes
  - /api/chat
  - /api/chat/stream
  - /api/images/generate
  - /api/history/{user_id}
  - /api/preferences
  - /api/generate-prompt
  |
  v
Service Layer
  - ChatService
  - ImageService
  - PromptEngine
  - IntentClassifier
  - AIService
  - HistoryService
  - PreferenceService
  |
  +--> Gemini text generation
  +--> Gemini Imagen generation
  +--> Mock fallback providers
  |
  v
Async SQLAlchemy + SQLite
  - chat_history
  - user_preferences
```

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy asyncio
- aiosqlite
- Pydantic v2
- Google GenAI SDK
- Pytest + pytest-asyncio
- Ruff
- Docker
- GitHub Actions

## Project Structure

```text
app/
  main.py
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
examples/
tests/
.github/workflows/ci.yml
```

## Setup on Windows

### 1. Create and activate a virtual environment

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

### 4. Initialize the local database

```powershell
python -m app.db.manage init
```

### 5. Run the API

```powershell
uvicorn app.main:app --reload
```

### 6. Open the docs

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

## Environment Variables

| Variable | Purpose | Example |
|---|---|---|
| `APP_NAME` | App display name | `Vizzy Chat API` |
| `APP_ENV` | Environment label | `development` |
| `DEBUG` | Debug-mode error details | `false` |
| `API_V1_PREFIX` | Route prefix | `/api` |
| `DATABASE_URL` | Async DB URL | `sqlite+aiosqlite:///./vizzy_chat.db` |
| `GEMINI_API_KEY` | Gemini API key | empty by default |
| `GEMINI_TEXT_MODEL` | Gemini text model | `gemini-2.5-flash` |
| `GEMINI_IMAGE_MODEL` | Imagen model | `imagen-3.0-generate-002` |
| `LOG_LEVEL` | Logger level | `INFO` |
| `HISTORY_WINDOW` | Number of past chat messages to use | `3` |
| `AUTO_RESET_DB_ON_SCHEMA_MISMATCH` | Dev-only schema reset behavior | `false` |
| `MOCK_STREAM_DELAY_MS` | Mock token streaming delay | `25` |
| `ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000,http://127.0.0.1:3000` |

## Database Management

Check schema status:

```powershell
python -m app.db.manage status --verbose
```

Reset the local database:

```powershell
python -m app.db.manage reset --yes
```

This is intentionally simpler than full Alembic for a lightweight local project, while still protecting you from silent SQLite schema drift.

## API Overview

### Health Check

```bash
curl http://127.0.0.1:8000/api/health
```

### Standard Chat

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d @examples/chat_request.json
```

### Streaming Chat

```bash
curl -N -X POST http://127.0.0.1:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "stream_user",
    "message": "Create a cinematic sci-fi poster with blue neon lighting",
    "user_type": "business"
  }'
```

The stream emits SSE events:

- `start`
- `token`
- `done`
- `error`

### Image Generation

```bash
curl -X POST http://127.0.0.1:8000/api/images/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a clean ceramic mug hero shot on a soft neutral studio background",
    "user_type": "business",
    "count": 2,
    "aspect_ratio": "1:1"
  }'
```

### Preferences

```bash
curl -X POST http://127.0.0.1:8000/api/preferences \
  -H "Content-Type: application/json" \
  -d @examples/preferences_request.json
```

### Prompt Generation

```bash
curl -X POST http://127.0.0.1:8000/api/generate-prompt \
  -H "Content-Type: application/json" \
  -d @examples/generate_prompt_request.json
```

## Response Contract

All non-stream endpoints return the same envelope:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2026-04-27T12:00:00+00:00"
  },
  "latency_ms": 12.41,
  "provider": "mock"
}
```

## Memory-Aware Workflow

Every chat request follows the same product-aware pipeline:

1. Load the last 3 chat messages for the user from SQLite.
2. Load saved preferences like style, tone, palette, or brand personality.
3. Classify the new request into a creative intent and pathway.
4. Generate polished prompts using the live request plus memory context.
5. Produce either a full response or an SSE token stream.
6. Persist the completed turn back into chat history.

This keeps the system simple enough to reason about while still feeling much closer to real AI product behavior.

## Image Generation Notes

- When `GEMINI_API_KEY` is available, the backend uses Imagen through the Google GenAI SDK.
- The current implementation returns base64-encoded images for easy local testing and frontend compatibility.
- When credentials are missing, the app falls back to a mock image provider so the endpoint remains usable.

Official Google references used for the implementation:

- [Gemini API libraries](https://ai.google.dev/gemini-api/docs/downloads)
- [Generating content and streaming](https://ai.google.dev/api/generate-content)
- [Imagen image generation](https://ai.google.dev/gemini-api/docs/imagen)

## Testing

Run lint:

```powershell
python -m ruff check .
```

Run tests:

```powershell
python -m pytest
```

Current coverage includes:

- async route coverage
- chat and history flows
- preferences persistence
- memory window behavior
- streaming SSE behavior
- image generation endpoint behavior
- AI fallback behavior

## Docker

Build the image:

```powershell
docker build -t vizzy-chat-backend .
```

Run the container:

```powershell
docker run --env-file .env -p 8000:8000 vizzy-chat-backend
```

Container features:

- non-root user
- `.dockerignore`
- healthcheck wired to `/api/health`

## GitHub Deployment

Initialize and push:

```powershell
git init
git add .
git commit -m "Upgrade Vizzy Chat to async streaming AI backend"
git branch -M main
git remote add origin https://github.com/<your-username>/vizzy-chat-ai-backend.git
git push -u origin main
```

After the first push, update the CI badge URL at the top of this README with your real GitHub username and repository name if needed.

## Interview Explanation

### What I Built

I upgraded a modular FastAPI backend into a production-grade AI backend with async infrastructure, real-time streaming chat, memory-aware responses, real image generation support, standardized APIs, testable fallbacks, containerization, and CI.

### Why It Matters

This demonstrates the engineering layer that sits between raw model APIs and a real product:

- product-friendly API contracts
- resilient provider integrations
- fast frontend-compatible streaming
- persistence and memory
- deployment hygiene
- async backend fundamentals

### How It Scales

- SQLite can be replaced by Postgres without changing the route layer.
- The AI and image providers can grow into multi-provider routing.
- SSE can evolve into websockets or realtime agents later.
- The memory layer can grow into summaries, vector retrieval, or workspace-level memory.
- CI, Docker, and pinned dependencies already support a team workflow.

## Roadmap

- Postgres + asyncpg for multi-user production deployment
- Alembic migrations for managed schema evolution
- provider routing between Gemini, OpenAI, and specialized image services
- background workers for long image jobs
- auth, rate limiting, and quota management
- richer observability with tracing and metrics
