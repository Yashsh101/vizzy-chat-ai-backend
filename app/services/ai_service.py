import asyncio
import base64
from collections.abc import AsyncGenerator, Generator
import json
import logging
from typing import Any, Protocol

from starlette.concurrency import iterate_in_threadpool

from app.core.config import get_settings
from app.schemas.chat import ChatResponseData, IntentClassification
from app.schemas.image import GeneratedImageData, ImageGenerateRequest, ImageGenerateResponseData

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None
    types = None

logger = logging.getLogger("vizzy_chat.ai")

_MOCK_IMAGE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAn8B9oNcamcAAAAASUVORK5CYII="
)


class ImageProvider(Protocol):
    provider_name: str

    async def generate_images(self, request: ImageGenerateRequest) -> ImageGenerateResponseData:
        ...


class MockImageProvider:
    provider_name = "mock-image"

    async def generate_images(self, request: ImageGenerateRequest) -> ImageGenerateResponseData:
        revised_prompt = (
            f"Create {request.count} polished visual directions from this brief: {request.prompt}. "
            f"Aspect ratio: {request.aspect_ratio}. Context: {request.context or 'none'}."
        )
        return ImageGenerateResponseData(
            prompt=request.prompt,
            revised_prompt=revised_prompt,
            model="mock-image-generator",
            images=[
                GeneratedImageData(mime_type="image/png", image_base64=_MOCK_IMAGE_BASE64)
                for _ in range(request.count)
            ],
            provider=self.provider_name,
        )


class GeminiImagenProvider:
    provider_name = "gemini-imagen"

    def __init__(self, client: Any, model_name: str) -> None:
        self.client = client
        self.model_name = model_name

    async def generate_images(self, request: ImageGenerateRequest) -> ImageGenerateResponseData:
        def _generate() -> ImageGenerateResponseData:
            response = self.client.models.generate_images(
                model=self.model_name,
                prompt=request.prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=request.count,
                    aspect_ratio=request.aspect_ratio,
                ),
            )
            return ImageGenerateResponseData(
                prompt=request.prompt,
                revised_prompt=request.prompt,
                model=self.model_name,
                images=[
                    GeneratedImageData(
                        mime_type="image/png",
                        image_base64=base64.b64encode(generated.image.image_bytes).decode("utf-8"),
                    )
                    for generated in response.generated_images
                ],
                provider=self.provider_name,
            )

        return await asyncio.to_thread(_generate)


class AIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = self._build_client()

    def _build_client(self):
        if not self.settings.gemini_api_key or genai is None:
            return None
        return genai.Client(api_key=self.settings.gemini_api_key)

    def _image_provider(self) -> ImageProvider:
        if self.client is None or types is None:
            return MockImageProvider()
        return GeminiImagenProvider(self.client, self.settings.gemini_image_model)

    async def generate_chat_response(
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
                generated_response = await asyncio.to_thread(
                    self._generate_with_gemini,
                    message,
                    classification,
                    recent_history,
                    preferences,
                )
                provider = "gemini"
            except Exception as exc:  # pragma: no cover
                logger.exception("Gemini generation failed, falling back to mock mode: %s", exc)
                generated_response = self._generate_mock_text(
                    message=message,
                    classification=classification,
                    recent_history=recent_history,
                    preferences=preferences,
                )
                provider = "mock"
        else:
            generated_response = self._generate_mock_text(
                message=message,
                classification=classification,
                recent_history=recent_history,
                preferences=preferences,
            )
            provider = "mock"

        return ChatResponseData(
            classification=classification,
            generated_response=generated_response,
            image_prompts=image_prompts,
            copy_suggestions=copy_suggestions,
            next_suggestions=next_suggestions,
            recent_history_used=recent_history,
            preferences_used=preferences,
            provider=provider,
        )

    async def stream_text(
        self,
        message: str,
        classification: IntentClassification,
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> AsyncGenerator[tuple[str, str], None]:
        if self.client is not None:
            try:
                async for chunk in iterate_in_threadpool(
                    self._stream_with_gemini(
                        message=message,
                        classification=classification,
                        recent_history=recent_history,
                        preferences=preferences,
                    )
                ):
                    yield chunk, "gemini"
                return
            except Exception as exc:  # pragma: no cover
                logger.exception("Gemini streaming failed, falling back to mock stream: %s", exc)

        for token in self._tokenize_for_stream(
            self._generate_mock_text(
                message=message,
                classification=classification,
                recent_history=recent_history,
                preferences=preferences,
            )
        ):
            await asyncio.sleep(self.settings.mock_stream_delay_ms / 1000)
            yield token, "mock"

    async def generate_images(self, request: ImageGenerateRequest) -> ImageGenerateResponseData:
        provider = self._image_provider()
        return await provider.generate_images(request)

    def _build_text_prompt(
        self,
        message: str,
        classification: IntentClassification,
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> str:
        return (
            "You are Vizzy Chat, a creative AI strategist. Reply in 3 to 5 concise sentences. "
            "Explain the creative direction, mention what to prioritize visually or in copy, and be practical.\n"
            f"Intent: {classification.intent}\n"
            f"Confidence: {classification.confidence}\n"
            f"Pathway: {classification.pathway}\n"
            f"Reasoning: {classification.reasoning}\n"
            f"Recent history: {json.dumps(recent_history or ['No recent history'])}\n"
            f"Saved preferences: {json.dumps(preferences or {'note': 'none'})}\n"
            f"User request: {message}"
        )

    def _generate_with_gemini(
        self,
        message: str,
        classification: IntentClassification,
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> str:
        prompt = self._build_text_prompt(message, classification, recent_history, preferences)
        response = self.client.models.generate_content(
            model=self.settings.gemini_text_model,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini response did not include text output.")
        return text.strip()

    def _stream_with_gemini(
        self,
        message: str,
        classification: IntentClassification,
        recent_history: list[str],
        preferences: dict[str, Any],
    ) -> Generator[str, None, None]:
        prompt = self._build_text_prompt(message, classification, recent_history, preferences)
        response = self.client.models.generate_content_stream(
            model=self.settings.gemini_text_model,
            contents=prompt,
        )
        for chunk in response:
            text = getattr(chunk, "text", None)
            if text:
                yield text

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

    @staticmethod
    def _tokenize_for_stream(text: str) -> list[str]:
        return [f"{token} " for token in text.split()]
