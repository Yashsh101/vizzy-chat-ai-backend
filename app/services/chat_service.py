from sqlalchemy.orm import Session

from app.models.chat import ChatHistory
from app.models.preference import UserPreference
from app.schemas.chat import ChatRequest, ChatResponseData
from app.services.ai_service import AIService
from app.services.history_service import HistoryService
from app.services.intent_classifier import IntentClassifier
from app.services.prompt_engine import PromptEngine


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.intent_classifier = IntentClassifier()
        self.prompt_engine = PromptEngine(db)
        self.history_service = HistoryService(db)
        self.ai_service = AIService()

    def process_chat(self, request: ChatRequest) -> ChatResponseData:
        classification = self.intent_classifier.classify(request.message)
        recent_history = self.history_service.get_recent_messages(request.user_id)
        preferences_record = self.db.get(UserPreference, request.user_id)
        preferences = preferences_record.preferences if preferences_record else {}

        prompt_bundle = self.prompt_engine.generate_prompt_bundle_from_chat(
            user_id=request.user_id,
            message=request.message,
            user_type=request.user_type,
            context=request.context,
            classification=classification,
            recent_history=recent_history,
            preferences=preferences,
        )

        response = self.ai_service.generate_chat_response(
            message=request.message,
            classification=classification,
            image_prompts=prompt_bundle.image_prompts,
            copy_suggestions=prompt_bundle.copy_suggestions,
            next_suggestions=prompt_bundle.next_suggestions,
            recent_history=recent_history,
            preferences=preferences,
        )

        self._store_chat(request, response)
        return response

    def _store_chat(self, request: ChatRequest, response: ChatResponseData) -> None:
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
        self.db.commit()
