import pytest


@pytest.mark.asyncio
async def test_preferences_round_trip(async_client):
    payload = {
        "user_id": "pref_user",
        "preferences": {"style": "minimal", "palette": "earth tones"},
    }

    save_response = await async_client.post("/api/preferences", json=payload)
    fetch_response = await async_client.get("/api/preferences/pref_user")

    assert save_response.status_code == 200
    assert fetch_response.status_code == 200
    assert fetch_response.json()["data"]["preferences"]["style"] == "minimal"


@pytest.mark.asyncio
async def test_chat_uses_recent_history_in_response(async_client):
    await async_client.post(
        "/api/chat",
        json={
            "user_id": "memory_user",
            "message": "Create a rustic bakery brand poster",
            "user_type": "business",
        },
    )

    second_response = await async_client.post(
        "/api/chat",
        json={
            "user_id": "memory_user",
            "message": "Now make a matching product visual for pastry boxes",
            "user_type": "business",
        },
    )

    payload = second_response.json()
    assert second_response.status_code == 200
    assert payload["data"]["recent_history_used"] == ["Create a rustic bakery brand poster"]


@pytest.mark.asyncio
async def test_chat_uses_last_three_messages_only(async_client):
    messages = [
        "Create a playful toy store window poster",
        "Design a matching quote poster for the campaign",
        "Build a moodboard for pastel retail interiors",
        "Now create product visuals for boxed gift sets",
    ]

    latest_response = None
    for message in messages:
        latest_response = await async_client.post(
            "/api/chat",
            json={
                "user_id": "window_user",
                "message": message,
                "user_type": "business",
            },
        )

    payload = latest_response.json()
    assert latest_response.status_code == 200
    assert payload["data"]["recent_history_used"] == messages[0:3]
