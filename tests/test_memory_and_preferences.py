def test_preferences_round_trip(client):
    payload = {
        "user_id": "pref_user",
        "preferences": {"style": "minimal", "palette": "earth tones"},
    }

    save_response = client.post("/api/preferences", json=payload)
    fetch_response = client.get("/api/preferences/pref_user")

    assert save_response.status_code == 200
    assert fetch_response.status_code == 200
    assert fetch_response.json()["data"]["preferences"]["style"] == "minimal"


def test_chat_uses_recent_history_in_response(client):
    client.post(
        "/api/chat",
        json={
            "user_id": "memory_user",
            "message": "Create a rustic bakery brand poster",
            "user_type": "business",
        },
    )

    second_response = client.post(
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


def test_chat_uses_last_three_messages_only(client):
    messages = [
        "Create a playful toy store window poster",
        "Design a matching quote poster for the campaign",
        "Build a moodboard for pastel retail interiors",
        "Now create product visuals for boxed gift sets",
    ]

    for message in messages:
        response = client.post(
            "/api/chat",
            json={
                "user_id": "window_user",
                "message": message,
                "user_type": "business",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"]["recent_history_used"] == messages[0:3]
