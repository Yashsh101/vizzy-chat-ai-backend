from app.services.ai_service import AIService
from app.services.intent_classifier import IntentClassifier
from app.services.prompt_engine import PromptEngine
from app.schemas.chat import GeneratePromptRequest


def test_intent_classifier_returns_confidence_reasoning_and_pathway():
    result = IntentClassifier().classify(
        "Create a premium skincare product hero shot with reflective glass"
    )

    assert result.intent == "product_visual"
    assert result.confidence >= 0.45
    assert "Matched keywords" in result.reasoning
    assert result.pathway == "product_visual_composition"


def test_prompt_engine_generates_context_aware_prompts():
    engine = PromptEngine(db=None)
    result = engine.generate_prompt_bundle(
        GeneratePromptRequest(
            message="Create a neon cyberpunk cafe scene",
            user_type="home",
            context={"mood": "cinematic"},
        )
    )

    assert len(result.image_prompts) == 2
    assert "cinematic" in result.image_prompts[0]


def test_ai_service_falls_back_to_mock_without_gemini_key():
    service = AIService()
    result = service.generate_chat_response(
        message="Create a playful kids room wall art concept",
        classification=IntentClassifier().classify("Create a playful kids room wall art concept"),
        image_prompts=["prompt 1", "prompt 2"],
        copy_suggestions=["copy 1", "copy 2"],
        next_suggestions=["next 1"],
        recent_history=[],
        preferences={},
    )

    assert result.provider == "mock"
    assert "creative" in result.generated_response.lower() or "request" in result.generated_response.lower()
