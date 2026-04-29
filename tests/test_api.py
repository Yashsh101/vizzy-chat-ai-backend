import pytest


@pytest.mark.asyncio
async def test_health_endpoint_returns_standardized_response(async_client):
    response = await async_client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["provider"] == "system"
    assert "latency_ms" in payload


@pytest.mark.asyncio
async def test_chat_endpoint_returns_enveloped_response(async_client):
    response = await async_client.post(
        "/api/chat",
        json={
            "user_id": "user_1",
            "message": "Design a promotional poster for a summer smoothie launch",
            "user_type": "business",
            "context": {"platform": "instagram"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["classification"]["intent"] == "poster_design"
    assert payload["data"]["classification"]["pathway"] == "creative_visual_generation"
    assert len(payload["data"]["image_prompts"]) == 3  # Updated to 3 prompts
    assert payload["provider"] == "mock"


@pytest.mark.asyncio
async def test_chat_stream_endpoint_returns_sse_events(async_client):
    response = await async_client.post(
        "/api/chat/stream",
        json={
            "user_id": "stream_user",
            "message": "Hello",
            "user_type": "business",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Read the streaming response
    content = b""
    async for chunk in response.aiter_bytes():
        content += chunk
    
    text = content.decode("utf-8")
    assert "event: start" in text
    assert "event: token" in text
    assert "event: done" in text
    assert '"event": "done"' in text


@pytest.mark.asyncio
async def test_history_endpoint_returns_saved_chat_items(async_client):
    await async_client.post(
        "/api/chat",
        json={
            "user_id": "history_user",
            "message": "Create a cozy home wall art concept with soft watercolor florals",
            "user_type": "home",
        },
    )

    response = await async_client.get("/api/history/history_user")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["user_id"] == "history_user"
    assert len(payload["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_generate_prompt_endpoint_returns_classification_and_prompts(async_client):
    response = await async_client.post(
        "/api/generate-prompt",
        json={
            "message": "Create a luxury storefront signage concept in brushed gold",
            "user_type": "business",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["classification"]["intent"] == "signage"
    assert len(payload["data"]["next_suggestions"]) >= 1


@pytest.mark.asyncio
async def test_preferences_missing_user_returns_standardized_error(async_client):
    response = await async_client.get("/api/preferences/missing-user")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "not_found"
