from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

UserType = Literal["home", "business"]


class IntentClassification(BaseModel):
    intent: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    pathway: str


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=3, max_length=2000)
    user_type: UserType
    context: dict[str, Any] | None = None


class ChatHistoryItem(BaseModel):
    user_id: str
    user_type: str
    message: str
    context: dict[str, Any] | None
    classification: IntentClassification
    generated_response: str
    image_prompts: list[str]
    copy_suggestions: list[str]
    next_suggestions: list[str]
    provider: str
    created_at: datetime


class ChatResponseData(BaseModel):
    classification: IntentClassification
    generated_response: str
    image_prompts: list[str]
    copy_suggestions: list[str]
    next_suggestions: list[str]
    recent_history_used: list[str]
    preferences_used: dict[str, Any]
    provider: str


class HistoryResponseData(BaseModel):
    user_id: str
    items: list[ChatHistoryItem]


class GeneratePromptRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=2000)
    user_type: UserType
    context: dict[str, Any] | None = None
    intent: str | None = None
    user_id: str | None = Field(default=None, min_length=1, max_length=100)


class GeneratePromptResponseData(BaseModel):
    classification: IntentClassification
    image_prompts: list[str]
    copy_suggestions: list[str]
    next_suggestions: list[str]
