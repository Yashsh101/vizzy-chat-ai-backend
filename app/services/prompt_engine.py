from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import UserPreference
from app.schemas.chat import (
    GeneratePromptRequest,
    GeneratePromptResponseData,
    IntentClassification,
)
from app.services.intent_classifier import IntentClassifier


class PromptEngine:
    def __init__(self, db: AsyncSession | None) -> None:
        self.db = db
        self.intent_classifier = IntentClassifier()

    async def generate_prompt_bundle(self, request: GeneratePromptRequest) -> GeneratePromptResponseData:
        classification = (
            self.intent_classifier.classify(request.message)
            if request.intent is None
            else self._classification_from_intent(request.intent)
        )
        preferences = await self._load_preferences(request.user_id) if request.user_id else {}
        context = dict(request.context or {})
        return self._build_bundle(
            message=request.message,
            user_type=request.user_type,
            classification=classification,
            context=context,
            recent_history=[],
            preferences=preferences,
        )

    async def generate_prompt_bundle_from_chat(
        self,
        user_id: str,
        message: str,
        user_type: str,
        context: dict[str, Any] | None,
        classification: IntentClassification,
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> GeneratePromptResponseData:
        merged_context = dict(context or {})
        if not preferences:
            loaded_preferences = await self._load_preferences(user_id)
            if loaded_preferences:
                preferences = loaded_preferences

        return self._build_bundle(
            message=message,
            user_type=user_type,
            classification=classification,
            context=merged_context,
            recent_history=recent_history,
            preferences=preferences,
        )

    def _detect_tone(self, message: str) -> str:
        message_lower = message.lower()
        if any(word in message_lower for word in ["luxury", "premium", "elegant", "sophisticated"]):
            return "luxury"
        elif any(word in message_lower for word in ["minimal", "clean", "simple", "modern"]):
            return "minimal"
        elif any(word in message_lower for word in ["bold", "vibrant", "dynamic", "striking"]):
            return "bold"
        else:
            return "balanced"

    def _build_bundle(
        self,
        message: str,
        user_type: str,
        classification: IntentClassification,
        context: dict[str, Any],
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> GeneratePromptResponseData:
        tone = self._detect_tone(message)
        creative_context = self._serialize_context(context, recent_history, preferences)
        audience = "home lifestyle audience" if user_type == "home" else "business marketing audience"
        image_prompts = [
            (
                f"Create a polished {classification.intent.replace('_', ' ')} concept for a {audience}. "
                f"User brief: {message}. "
                f"Creative pathway: {classification.pathway}. "
                f"Style tone: {tone}. "
                f"Use this context: {creative_context}. "
                "Aim for strong composition, premium detail, and execution-ready clarity."
            ),
            (
                f"Create a second variation for this {classification.intent.replace('_', ' ')} request: {message}. "
                f"Keep the same objective but shift the art direction while respecting this context: {creative_context}. "
                f"Style tone: {tone}."
            ),
            (
                f"Create a third alternative for this {classification.intent.replace('_', ' ')} request: {message}. "
                f"Focus on a different creative approach with style tone {tone}, using context: {creative_context}."
            ),
        ]
        copy_tone = (
            "warm, personal, and inspiring"
            if user_type == "home"
            else "strategic, brand-ready, and persuasive"
        )
        copy_suggestions = [
            f"Write a {copy_tone} headline that supports this brief: {message}",
            f"Write a concise supporting line aligned with the {classification.intent.replace('_', ' ')} direction.",
        ]
        next_suggestions = self._next_steps(classification.intent)
        return GeneratePromptResponseData(
            classification=classification,
            image_prompts=image_prompts,
            copy_suggestions=copy_suggestions,
            next_suggestions=next_suggestions,
        )

    async def _load_preferences(self, user_id: str) -> dict[str, Any]:
        if self.db is None:
            return {}
        record = await self.db.get(UserPreference, user_id)
        return record.preferences if record else {}

    def _classification_from_intent(self, intent: str) -> IntentClassification:
        template = self.intent_classifier.RULES.get(intent, self.intent_classifier.RULES["general_creative_help"])
        return IntentClassification(
            intent=intent,
            confidence=0.8 if intent in self.intent_classifier.RULES else 0.55,
            reasoning="Intent was supplied directly by the request payload.",
            pathway=template.pathway,
        )

    @staticmethod
    def _serialize_context(
        context: dict[str, Any],
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> str:
        parts: list[str] = []
        if context:
            parts.append(f"request context={context}")
        if recent_history:
            parts.append(f"recent history={recent_history}")
        if preferences:
            parts.append(f"user preferences={preferences}")
        return "; ".join(parts) if parts else "no extra context provided"

    @staticmethod
    def _next_steps(intent: str) -> list[str]:
        options = {
            "poster_design": ["Request a minimalist poster variation", "Ask for social caption ideas"],
            "brand_campaign": ["Ask for campaign slogan options", "Request channel-specific adaptations"],
            "product_visual": ["Ask for e-commerce hero shot prompts", "Request packaging copy ideas"],
            "moodboard": ["Ask for a richer palette direction", "Request material or texture cues"],
        }
        return options.get(intent, ["Ask for another visual style", "Request shorter or bolder copy"])
