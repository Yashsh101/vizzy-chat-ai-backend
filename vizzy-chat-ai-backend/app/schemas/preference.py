from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PreferenceRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    preferences: dict[str, Any] = Field(default_factory=dict)


class PreferenceResponseData(BaseModel):
    user_id: str
    preferences: dict[str, Any]
    updated_at: datetime | None = None
