import pytest

from app.schemas.chat import GeneratePromptRequest
from app.schemas.image import ImageGenerateRequest
from app.services.ai_service import AIService
from app.services.intent_classifier import IntentClassifier
from app.services.prompt_engine import PromptEngine


def test_intent_classifier_returns_confidence_reasoning_and_pathway():
    result = IntentClassifier().classify(
        "Create a premium skincare product hero shot with reflective glass"
    )

    assert result.intent == "product_visual"
    assert result.confidence >= 0.45
    assert "Matched keywords" in result.reasoning
    assert result.pathway == "product_visual_composition"


@pytest.mark.asyncio
async def test_prompt_engine_generates_context_aware_prompts():
    engine = PromptEngine(db=None)
    result = await engine.generate_prompt_bundle(
        GeneratePromptRequest(
            message="Create a neon cyberpunk cafe scene",
            user_type="home",
            context={"mood": "cinematic"},
        )
    )

    assert len(result.image_prompts) == 2
    assert "cinematic" in result.image_prompts[0]


@pytest.mark.asyncio
async def test_ai_service_falls_back_to_mock_without_gemini_key():
    service = AIService()
    result = await service.generate_chat_response(
        message="Create a playful kids room wall art concept",
        classification=IntentClassifier().classify("Create a playful kids room wall art concept"),
        image_prompts=["prompt 1", "prompt 2"],
        copy_suggestions=["copy 1", "copy 2"],
        next_suggestions=["next 1"],
        recent_history=[],
        preferences={},
    )

    assert result.provider == "mock"
    assert "request" in result.generated_response.lower()


@pytest.mark.asyncio
async def test_streaming_endpoint_emits_tokens(async_client):
    async with async_client.stream(
        "POST",
        "/api/chat/stream",
        json={
            "user_id": "stream_user",
            "message": "Create a cinematic sci-fi poster with blue neon lighting",
            "user_type": "business",
        },
    ) as response:
        body = ""
        async for chunk in response.aiter_text():
            body += chunk

    assert response.status_code == 200
    assert "event: start" in body
    assert "event: token" in body
    assert "event: done" in body


@pytest.mark.asyncio
async def test_image_generation_endpoint_returns_images(async_client):
    response = await async_client.post(
        "/api/images/generate",
        json=ImageGenerateRequest(
            prompt="Create a clean product hero image for a ceramic mug",
            user_type="business",
            count=2,
            aspect_ratio="1:1",
        ).model_dump(),
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert len(payload["data"]["images"]) == 2
    assert payload["data"]["images"][0]["image_base64"]
