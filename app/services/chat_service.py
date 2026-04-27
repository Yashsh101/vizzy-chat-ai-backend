from dataclasses import dataclass
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatHistory
from app.models.preference import UserPreference
from app.schemas.chat import ChatRequest, ChatResponseData, GeneratePromptResponseData, IntentClassification
from app.services.ai_service import AIService
from app.services.history_service import HistoryService
from app.services.intent_classifier import IntentClassifier
from app.services.prompt_engine import PromptEngine


@dataclass
class PreparedChat:
    classification: IntentClassification
    prompt_bundle: GeneratePromptResponseData
    recent_history: list[str]
    preferences: dict


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.intent_classifier = IntentClassifier()
        self.prompt_engine = PromptEngine(db)
        self.history_service = HistoryService(db)
        self.ai_service = AIService()

    async def prepare_chat(self, request: ChatRequest) -> PreparedChat:
        classification = self.intent_classifier.classify(request.message)
        recent_history = await self.history_service.get_recent_messages(request.user_id)
        preferences_record = await self.db.get(UserPreference, request.user_id)
        preferences = preferences_record.preferences if preferences_record else {}

        prompt_bundle = await self.prompt_engine.generate_prompt_bundle_from_chat(
            user_id=request.user_id,
            message=request.message,
            user_type=request.user_type,
            context=request.context,
            classification=classification,
            recent_history=recent_history,
            preferences=preferences,
        )

        return PreparedChat(
            classification=classification,
            prompt_bundle=prompt_bundle,
            recent_history=recent_history,
            preferences=preferences,
        )

    async def process_chat(self, request: ChatRequest) -> ChatResponseData:
        prepared = await self.prepare_chat(request)
        response = await self.ai_service.generate_chat_response(
            message=request.message,
            classification=prepared.classification,
            image_prompts=prepared.prompt_bundle.image_prompts,
            copy_suggestions=prepared.prompt_bundle.copy_suggestions,
            next_suggestions=prepared.prompt_bundle.next_suggestions,
            recent_history=prepared.recent_history,
            preferences=prepared.preferences,
        )
        await self.store_chat(request, response)
        return response

    async def stream_chat(
        self,
        request: ChatRequest,
    ) -> tuple[PreparedChat, AsyncGenerator[tuple[str, str], None]]:
        prepared = await self.prepare_chat(request)
        stream = self.ai_service.stream_text(
            message=request.message,
            classification=prepared.classification,
            recent_history=prepared.recent_history,
            preferences=prepared.preferences,
        )
        return prepared, stream

    async def store_chat(self, request: ChatRequest, response: ChatResponseData) -> None:
        record = ChatHistory(
            user_id=request.user_id,
            user_type=request.user_type,
            message=request.message,
            context=request.context,
            intent=response.classification.intent,
            confidence=response.classification.confidence,
            reasoning=response.classification.reasoning,
            pathway=response.classification.pathway,
            generated_response=response.generated_response,
            image_prompts=response.image_prompts,
            copy_suggestions=response.copy_suggestions,
            next_suggestions=response.next_suggestions,
            provider=response.provider,
        )
        self.db.add(record)
        await self.db.commit()
