from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chat import ChatHistory
from app.schemas.chat import ChatHistoryItem, HistoryResponseData, IntentClassification


class HistoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def get_recent_messages(self, user_id: str) -> list[str]:
        query = (
            select(ChatHistory.message)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(self.settings.history_window)
        )
        return list(reversed(self.db.scalars(query).all()))

    def get_user_history(self, user_id: str) -> HistoryResponseData:
        query = (
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.asc())
        )
        items = self.db.scalars(query).all()
        return HistoryResponseData(
            user_id=user_id,
            items=[
                ChatHistoryItem(
                    user_id=item.user_id,
                    user_type=item.user_type,
                    message=item.message,
                    context=item.context,
                    classification=IntentClassification(
                        intent=item.intent,
                        confidence=item.confidence,
                        reasoning=item.reasoning,
                        pathway=item.pathway,
                    ),
                    generated_response=item.generated_response,
                    image_prompts=item.image_prompts,
                    copy_suggestions=item.copy_suggestions,
                    next_suggestions=item.next_suggestions,
                    provider=item.provider,
                    created_at=item.created_at,
                )
                for item in items
            ],
        )
