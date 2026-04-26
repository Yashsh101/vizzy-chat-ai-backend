import logging
from typing import Any

from app.core.config import get_settings
from app.schemas.chat import ChatResponseData, IntentClassification

try:
    from google import genai
except ImportError:  # pragma: no cover - exercised via fallback tests
    genai = None

logger = logging.getLogger("vizzy_chat.ai")


class AIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = self._build_client()

    def _build_client(self):
        if not self.settings.gemini_api_key or genai is None:
            return None
        return genai.Client(api_key=self.settings.gemini_api_key)

    def generate_chat_response(
        self,
        message: str,
        classification: IntentClassification,
        image_prompts: list[str],
        copy_suggestions: list[str],
        next_suggestions: list[str],
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> ChatResponseData:
        if self.client is not None:
            try:
                response_text = self._generate_with_gemini(
                    message=message,
                    classification=classification,
                    recent_history=recent_history,
                    preferences=preferences,
                )
                provider = "gemini"
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.exception("Gemini generation failed, falling back to mock mode: %s", exc)
                response_text = self._generate_mock_text(
                    message=message,
                    classification=classification,
                    recent_history=recent_history,
                    preferences=preferences,
                )
                provider = "mock"
        else:
            response_text = self._generate_mock_text(
                message=message,
                classification=classification,
                recent_history=recent_history,
                preferences=preferences,
            )
            provider = "mock"

        return ChatResponseData(
            classification=classification,
            generated_response=response_text,
            image_prompts=image_prompts,
            copy_suggestions=copy_suggestions,
            next_suggestions=next_suggestions,
            recent_history_used=recent_history,
            preferences_used=preferences,
            provider=provider,
        )

    def _generate_with_gemini(
        self,
        message: str,
        classification: IntentClassification,
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> str:
        prompt = (
            "You are Vizzy Chat, a creative AI strategist. Reply in 3 to 5 concise sentences. "
            "Explain the creative direction, mention what to prioritize visually or in copy, and be practical.\n"
            f"Intent: {classification.intent}\n"
            f"Confidence: {classification.confidence}\n"
            f"Pathway: {classification.pathway}\n"
            f"Reasoning: {classification.reasoning}\n"
            f"Recent history: {recent_history or ['No recent history']}\n"
            f"Saved preferences: {preferences or {'note': 'none'}}\n"
            f"User request: {message}"
        )
        response = self.client.models.generate_content(
            model=self.settings.gemini_model,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini response did not include text output.")
        return text.strip()

    @staticmethod
    def _generate_mock_text(
        message: str,
        classification: IntentClassification,
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> str:
        history_line = (
            f"I also considered your recent requests around {', '.join(recent_history[:2])}. "
            if recent_history
            else ""
        )
        preference_line = (
            f"Your saved preferences point toward {preferences}. "
            if preferences
            else ""
        )
        return (
            f"I’ve mapped this request to {classification.intent.replace('_', ' ')} with a "
            f"{classification.pathway.replace('_', ' ')} workflow. "
            f"{history_line}{preference_line}"
            f"For this brief, prioritize a clear focal point, a cohesive style direction, and copy that directly supports the visual concept. "
            f"Your original request was: {message}"
        )
