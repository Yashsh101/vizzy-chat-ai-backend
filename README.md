# Vizzy Chat AI Backend

Production-ready FastAPI backend for a memory-aware creative AI platform that turns natural-language ideas into structured visual and copy generation workflows.

## Problem Statement

Creative users often know what they want to make, but they do not naturally think in the prompt structures that AI systems need. Businesses have the same problem at a different scale: they want quick visual directions, campaign ideas, product visuals, signage concepts, and copy suggestions without building a custom creative pipeline from scratch.

Vizzy Chat solves that backend problem. It accepts plain-English creative requests, classifies the user’s intent, remembers recent context and saved preferences, generates polished prompts, and routes the request through Gemini when available or a safe mock mode when it is not.

## Key Features

- FastAPI backend with clean modular architecture
- Standardized API response envelope across all endpoints
- Intent classification with `intent`, `confidence`, `reasoning`, and `pathway`
- Prompt engine for polished image and copy generation prompts
- Memory-aware responses using the last 3 chats and saved user preferences
- SQLite persistence for chat history and preferences
- Gemini integration with graceful fallback to mock mode
- Structured error handling, request IDs, latency tracking, logging, and CORS
- Local database init, status, and reset commands
- Interview-ready tests, docs, and example payloads

## Architecture Diagram

```text
Client / Frontend
        |
        v
FastAPI Routes (app/api/routes.py)
        |
        v
Service Layer
  - ChatService
  - PromptEngine
  - IntentClassifier
  - AIService
  - HistoryService
  - PreferenceService
        |
        +------------------> Gemini API (optional)
        |                         |
        |                         v
        |                    AI-generated text
        |
        +------------------> Mock fallback mode
        |
        v
SQLite via SQLAlchemy
  - chat_history
  - user_preferences
```

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic v2
- Google Gemini via `google-genai`
- Pytest
- Uvicorn
- Docker

## Folder Structure

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
    preference.py
  services/
    ai_service.py
    chat_service.py
    history_service.py
    intent_classifier.py
    preference_service.py
    prompt_engine.py
docs/
  screenshots/
examples/
tests/
```

## Setup and Run Steps for Windows

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create environment file

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

### 6. Open docs

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health endpoint: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

## Database Initialization and Reset

This project includes a clean local database management flow to handle SQLite schema drift during development.

### Check schema status

```powershell
python -m app.db.manage status --verbose
```

### Recreate the local database

```powershell
python -m app.db.manage reset --yes
```

### Notes

- The startup initializer checks for missing columns such as `confidence`, `reasoning`, and `pathway`.
- In development, if `AUTO_RESET_DB_ON_SCHEMA_MISMATCH=true`, stale local SQLite tables are automatically recreated.
- No secrets are stored in the database management commands.
- This project intentionally documents a reset-db workflow instead of adding full Alembic complexity, which keeps the repo simpler for an internship submission while still fixing the schema mismatch problem cleanly.

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `APP_NAME` | FastAPI app title | `Vizzy Chat API` |
| `APP_ENV` | App environment | `development` |
| `DEBUG` | Enables debug-mode error details | `true` |
| `API_V1_PREFIX` | API prefix | `/api` |
| `DATABASE_URL` | SQLite connection string | `sqlite:///./vizzy_chat.db` |
| `GEMINI_API_KEY` | Gemini API key | empty by default |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.5-flash` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HISTORY_WINDOW` | Number of recent chats to use | `3` |
| `AUTO_RESET_DB_ON_SCHEMA_MISMATCH` | Auto-recreate stale local DB schema in development | `true` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000,http://127.0.0.1:3000` |

## API Documentation

All endpoints return the same response envelope:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {
    "request_id": "9d7d3f4d-0b9d-4a53-b722-dcb157eb57a6",
    "timestamp": "2026-04-27T08:15:30.000000+00:00"
  },
  "latency_ms": 12.41,
  "provider": "mock"
}
```

### `GET /api/health`

Response example:

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "Vizzy Chat API"
  },
  "error": null,
  "metadata": {
    "component": "health"
  },
  "latency_ms": 1.11,
  "provider": "system"
}
```

### `POST /api/chat`

Sample request file: [examples/chat_request.json](C:/Users/syash/OneDrive/Desktop/vizzy-chat-ai-backend/examples/chat_request.json)

Request example:

```json
{
  "user_id": "demo_user",
  "message": "Create a premium coffee shop poster with warm lighting and hand-drawn lettering",
  "user_type": "business",
  "context": {
    "platform": "instagram",
    "goal": "launch weekend offer"
  }
}
```

Response example:

```json
{
  "success": true,
  "data": {
    "classification": {
      "intent": "poster_design",
      "confidence": 0.83,
      "reasoning": "Matched keywords ['poster'] which strongly suggest poster design.",
      "pathway": "creative_visual_generation"
    },
    "generated_response": "I’ve mapped this request to poster design...",
    "image_prompts": [
      "Create a polished poster design concept...",
      "Create a second variation..."
    ],
    "copy_suggestions": [
      "Write a strategic, brand-ready, and persuasive headline...",
      "Write a concise supporting line..."
    ],
    "next_suggestions": [
      "Request a minimalist poster variation",
      "Ask for social caption ideas"
    ],
    "recent_history_used": [],
    "preferences_used": {},
    "provider": "mock"
  },
  "error": null,
  "metadata": {
    "component": "chat"
  },
  "latency_ms": 15.8,
  "provider": "mock"
}
```

### `GET /api/history/{user_id}`

Returns stored chat records with classification metadata, prompts, and provider details.

### `POST /api/preferences`

Sample request file: [examples/preferences_request.json](C:/Users/syash/OneDrive/Desktop/vizzy-chat-ai-backend/examples/preferences_request.json)

Request example:

```json
{
  "user_id": "demo_user",
  "preferences": {
    "style": "minimal premium",
    "palette": "warm neutrals",
    "brand_personality": "modern and welcoming"
  }
}
```

### `GET /api/preferences/{user_id}`

Returns saved preferences for a user.

### `POST /api/generate-prompt`

Sample request file: [examples/generate_prompt_request.json](C:/Users/syash/OneDrive/Desktop/vizzy-chat-ai-backend/examples/generate_prompt_request.json)

Request example:

```json
{
  "message": "Design a modern bookstore storefront sign in matte black and brass",
  "user_type": "business",
  "context": {
    "location": "high street retail"
  }
}
```

## Memory-Aware Workflow

Vizzy Chat uses two lightweight memory sources:

1. Recent chat history
2. Saved user preferences

For each `POST /api/chat` request:

1. The backend loads the user’s last 3 chat messages from SQLite.
2. It fetches saved preferences such as style, palette, or brand voice.
3. The prompt engine merges the live request, recent history, and saved preferences.
4. The AI response includes both better prompts and a more context-aware reply.

This approach is simple, explainable, and easy to scale later into richer memory systems.

## Screenshots

Add these before publishing the repo:

- `docs/screenshots/swagger-ui.png`
- `docs/screenshots/chat-response.png`
- `docs/screenshots/pytest-passing.png`

## Testing Instructions

Run the full suite:

```powershell
python -m pytest
```

The tests cover:

- health endpoint
- chat endpoint
- prompt generation
- preferences round-trip
- history retrieval
- memory window behavior
- intent classification
- AI fallback behavior

## Deployment and GitHub Push Steps

### Docker

```powershell
docker build -t vizzy-chat-backend .
docker run -p 8000:8000 vizzy-chat-backend
```

### Push to GitHub

```powershell
git init
git add .
git commit -m "Build production-ready Vizzy Chat FastAPI backend"
git branch -M main
git remote add origin https://github.com/<your-username>/vizzy-chat-ai-backend.git
git push -u origin main
```

### GitHub Readiness Checklist

- `.env` is ignored
- no API keys are committed
- local SQLite files are ignored
- sample payloads are included
- tests pass
- Dockerfile is included
- README explains setup, architecture, and interview story

## Interview Explanation

### What I Built

I built a modular FastAPI backend for a conversational creative AI platform. It accepts natural-language creative requests, classifies intent, remembers recent chats and preferences, generates polished prompts, and responds through Gemini or a safe mock fallback.

### Why It Matters

This backend shows the core skills expected in a backend plus AI internship:

- API design
- service-layer architecture
- persistence and memory
- AI provider integration
- graceful fallbacks
- testing and documentation

### How It Scales

The current code is deliberately simple, but it is structured to scale:

- SQLite can be replaced with Postgres
- the AI service can support multiple providers
- the memory layer can expand into summarization or vector retrieval
- background workers can handle heavy generation jobs
- auth and rate limiting can be added without reworking the architecture

## Future Roadmap

- Postgres and Alembic for multi-environment deployments
- OpenAI and image API adapters behind the same AI interface
- async job queue for long-running generation tasks
- richer user profiles and brand-kit memory
- analytics, tracing, and rate limiting
- auth, RBAC, and multi-tenant workspace support
