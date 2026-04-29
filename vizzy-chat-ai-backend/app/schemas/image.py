from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.chat import UserType


class ImageGenerateRequest(BaseModel):
    user_id: str | None = Field(default=None, min_length=1, max_length=100)
    prompt: str = Field(..., min_length=3, max_length=4000)
    user_type: UserType = "home"
    count: int = Field(default=1, ge=1, le=4)
    aspect_ratio: Literal["1:1", "3:4", "4:3", "9:16", "16:9"] = "1:1"
    context: dict[str, Any] | None = None


class GeneratedImageData(BaseModel):
    mime_type: str
    image_base64: str


class ImageGenerateResponseData(BaseModel):
    prompt: str
    revised_prompt: str
    model: str
    images: list[GeneratedImageData]
    provider: str
