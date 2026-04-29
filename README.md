# Vizzy Chat AI Backend

[![CI](https://github.com/your-github-username/vizzy-chat-ai-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/your-github-username/vizzy-chat-ai-backend/actions/workflows/ci.yml)

## System Overview

Vizzy Chat is a production-grade AI backend that transforms raw AI model calls into a structured, memory-aware, streaming-enabled creative assistant. Unlike typical demo projects, this system demonstrates real-world engineering practices: async architecture, comprehensive error handling, observability, rate limiting, and scalable data persistence.

**What makes this stand out:** This isn't just another FastAPI tutorial—it's a complete AI product backend that handles the complexities of user memory, real-time streaming, intent classification, and multi-modal generation while maintaining clean code and robust testing.

## Problem Solved

Modern AI products often fail at the "product layer"—they expose model APIs directly without:
- **Memory & Context**: Remembering user preferences and conversation history
- **Streaming UX**: Real-time token-by-token responses
- **Intent Understanding**: Classifying user requests for better responses
- **Production Readiness**: Logging, rate limiting, error handling, and deployment
- **Fallback Safety**: Graceful degradation when AI services fail

Vizzy Chat solves these by providing a complete backend that turns natural language into structured creative outputs.

## Key Features

### 🚀 Core Capabilities
- **Real-time Streaming Chat**: Server-Sent Events with `start` → `token` → `done` flow
- **Memory-Aware Responses**: Incorporates last 3 conversations and user preferences
- **Intent Classification**: Routes requests through creative pathways (posters, campaigns, etc.)
- **Multi-Modal Generation**: Text prompts + image generation via Gemini Imagen
- **Style Tone Detection**: Automatically detects luxury/minimal/bold tones

### 🏗️ Production Engineering
- **Async FastAPI**: Non-blocking routes with async SQLAlchemy
- **Structured Logging**: JSON-formatted logs with request IDs and latency
- **Rate Limiting**: In-memory limiter (10 req/min per client)
- **Request Tracking**: UUID request IDs in logs and responses
- **Comprehensive Testing**: 13+ tests covering API, services, and memory
- **Docker Ready**: Multi-stage build with health checks

### 📊 API Design
- **Standardized Envelope**: `success`/`data`/`error`/`metadata`/`latency_ms`/`provider`
- **Streaming Events**: Proper SSE with event types and structured payloads
- **Error Handling**: Typed errors with codes and details
- **Validation**: Pydantic schemas with detailed error messages

## Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Apps   │────│   FastAPI Routes │────│  Service Layer  │
│                 │    │                  │    │                 │
│ • Web Frontend  │    │ • /api/chat      │    │ • ChatService   │
│ • Mobile App    │    │ • /api/chat/stream│    │ • PromptEngine  │
│ • API Consumers │    │ • /api/images    │    │ • IntentClassifier│
└─────────────────┘    │ • /api/history   │    │ • AIService     │
                       │ • /api/health    │    │ • HistoryService│
                       └──────────────────┘    │ • PreferenceSvc │
                                                └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Gemini AI      │    │ Async SQLAlchemy │    │   Mock Fallback │
│                 │    │                  │    │                 │
│ • Text Gen      │◄───│ • chat_history   │────│ • Safe responses│
│ • Image Gen     │    │ • user_preferences│    │ • No crashes   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Streaming Explanation

Streaming responses use Server-Sent Events for real-time UX:

```javascript
// Client-side consumption
const eventSource = new EventSource('/api/chat/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event === 'start') {
    // Show loading, display classification
  } else if (data.event === 'token') {
    // Append token to response text
  } else if (data.event === 'done') {
    // Complete response, show full data
  }
};
```

Each event includes full metadata, request ID, and latency tracking.

## Memory System

The backend maintains two types of memory:

### Conversation History
- Stores last 3 user messages per user
- Influences prompt generation and suggestions
- Persisted in SQLite with timestamps

### User Preferences
- Long-term style preferences (e.g., "always use warm colors")
- Saved via `/api/preferences` endpoint
- Merged with conversation context

## API Examples

### Chat Request
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "designer_123",
    "message": "Create a luxury coffee shop poster with warm lighting",
    "user_type": "business",
    "context": {"platform": "instagram"}
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "classification": {
      "intent": "poster_design",
      "confidence": 0.83,
      "pathway": "creative_visual_generation"
    },
    "generated_response": "I've mapped this to poster design...",
    "image_prompts": ["Create a polished poster...", "...second variation...", "...third alternative..."],
    "copy_suggestions": ["Write a strategic headline...", "...supporting line..."],
    "next_suggestions": ["Request minimalist variation..."],
    "recent_history_used": ["previous messages..."],
    "preferences_used": {}
  },
  "metadata": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-04-29T15:42:01Z",
    "component": "chat"
  },
  "latency_ms": 45.2,
  "provider": "mock"
}
```

### Streaming Chat
```bash
curl -N http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_1", "message": "Hello"}'
```

**Output:**
```
event: start
data: {"event": "start", "classification": {...}}

event: token
data: {"event": "token", "token": "I "}

event: token
data: {"event": "token", "token": "have "}

...

event: done
data: {"event": "done", "generated_response": "Full response..."}
```

## Setup Instructions

### Prerequisites
- Python 3.12+
- Docker (optional)

### Local Development
```bash
# Clone and setup
git clone https://github.com/your-github-username/vizzy-chat-ai-backend
cd vizzy-chat-ai-backend

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start server
uvicorn app.main:app --reload

# Visit http://localhost:8000/docs for API docs
```

### Docker
```bash
# Build and run
docker build -t vizzy-chat .
docker run -p 8000:8000 vizzy-chat

# Health check
curl http://localhost:8000/api/health
```

### Configuration
Set environment variables:
- `GEMINI_API_KEY`: For real AI generation (optional, uses mock fallback)
- `LOG_LEVEL`: INFO/DEBUG/etc.

## Interview Explanation

**Why this project stands out:**

1. **Real Product Thinking**: Most candidates build CRUD APIs or simple ML demos. This shows you understand building AI *products*—memory, streaming, UX considerations.

2. **Production Practices**: Request IDs, structured logging, rate limiting, async patterns—these are what senior engineers implement.

3. **Scalable Architecture**: Clean separation of concerns, dependency injection, comprehensive testing. Easy to extend with new AI providers or features.

4. **Error Handling**: Graceful fallbacks, typed errors, no crashes. Shows reliability thinking.

5. **Performance**: Async everywhere, streaming responses, efficient queries. Handles real load.

**What interviewers will ask:**
- How does streaming work? (SSE, async generators)
- Memory implementation? (SQLAlchemy relationships, context merging)
- Testing strategy? (Service layer mocking, async fixtures)
- Deployment considerations? (Docker, health checks, env config)

**Tech Stack Rationale:**
- FastAPI: Async, auto-docs, validation
- SQLAlchemy Async: Non-blocking DB
- Pydantic: Type safety
- SSE: Real-time UX without WebSockets complexity
- Docker: Consistent deployment

## Future Roadmap

- [ ] Redis for distributed rate limiting
- [ ] PostgreSQL for production DB
- [ ] Authentication/Authorization
- [ ] Metrics collection (Prometheus)
- [ ] Multi-region deployment
- [ ] Advanced prompt engineering with few-shot examples

---

**Built with production intent. Ready for real users.**
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
