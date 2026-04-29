from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    user_type: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    intent: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(default=0.0)
    reasoning: Mapped[str] = mapped_column(Text)
    pathway: Mapped[str] = mapped_column(String(100))
    generated_response: Mapped[str] = mapped_column(Text)
    image_prompts: Mapped[list[str]] = mapped_column(JSON)
    copy_suggestions: Mapped[list[str]] = mapped_column(JSON)
    next_suggestions: Mapped[list[str]] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(50), default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
