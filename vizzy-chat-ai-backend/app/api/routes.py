import json

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import build_error_response, build_response
from app.db.session import get_db, ping_database
from app.schemas.base import APIResponse
from app.schemas.chat import (
    ChatRequest,
    ChatResponseData,
    GeneratePromptRequest,
    GeneratePromptResponseData,
    HistoryResponseData,
    StreamEventData,
)
from app.schemas.health import HealthData
from app.schemas.image import ImageGenerateRequest, ImageGenerateResponseData
from app.schemas.preference import PreferenceRequest, PreferenceResponseData
from app.services.chat_service import ChatService
from app.services.history_service import HistoryService
from app.services.image_service import ImageService
from app.services.preference_service import PreferenceService
from app.services.prompt_engine import PromptEngine

router = APIRouter()


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


@router.get("/health", response_model=APIResponse[HealthData], status_code=status.HTTP_200_OK)
async def health_check(request: Request) -> APIResponse[HealthData]:
    await ping_database()
    return build_response(
        request=request,
        data=HealthData(status="ok", service="Vizzy Chat API"),
        provider="system",
        metadata={"component": "health"},
    )


@router.post("/chat", response_model=APIResponse[ChatResponseData], status_code=status.HTTP_200_OK)
async def create_chat(
    payload: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ChatResponseData]:
    result = await ChatService(db).process_chat(payload)
    return build_response(
        request=request,
        data=result,
        provider=result.provider,
        metadata={
            "component": "chat",
            "pathway": result.classification.pathway,
            "confidence": result.classification.confidence,
        },
    )


@router.post("/chat/stream", status_code=status.HTTP_200_OK)
async def stream_chat(
    payload: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    service = ChatService(db)
    prepared, stream = await service.stream_chat(payload)

    async def event_generator():
        final_text_parts: list[str] = []
        active_provider = "mock"

        start_event = build_response(
            request=request,
            data=StreamEventData(
                event="start",
                classification=prepared.classification,
                image_prompts=prepared.prompt_bundle.image_prompts,
                copy_suggestions=prepared.prompt_bundle.copy_suggestions,
                next_suggestions=prepared.prompt_bundle.next_suggestions,
                recent_history_used=prepared.recent_history,
                preferences_used=prepared.preferences,
            ),
            provider="system",
            metadata={"component": "chat-stream"},
        )
        yield _sse("start", start_event.model_dump())

        try:
            async for token, provider_name in stream:
                active_provider = provider_name
                final_text_parts.append(token)
                token_event = build_response(
                    request=request,
                    data=StreamEventData(event="token", token=token),
                    provider=provider_name,
                    metadata={"component": "chat-stream"},
                )
                yield _sse("token", token_event.model_dump())

            final_response = ChatResponseData(
                classification=prepared.classification,
                generated_response="".join(final_text_parts).strip(),
                image_prompts=prepared.prompt_bundle.image_prompts,
                copy_suggestions=prepared.prompt_bundle.copy_suggestions,
                next_suggestions=prepared.prompt_bundle.next_suggestions,
                recent_history_used=prepared.recent_history,
                preferences_used=prepared.preferences,
                provider=active_provider,
            )
            await service.store_chat(payload, final_response)
            done_event = build_response(
                request=request,
                data=StreamEventData(
                    event="done",
                    classification=final_response.classification,
                    generated_response=final_response.generated_response,
                    image_prompts=final_response.image_prompts,
                    copy_suggestions=final_response.copy_suggestions,
                    next_suggestions=final_response.next_suggestions,
                    recent_history_used=final_response.recent_history_used,
                    preferences_used=final_response.preferences_used,
                ),
                provider=active_provider,
                metadata={"component": "chat-stream"},
            )
            yield _sse("done", done_event.model_dump())
        except Exception as exc:
            error_event = build_error_response(
                request=request,
                provider="system",
                code="stream_error",
                message="Streaming chat failed.",
                details=str(exc),
            )
            yield _sse("error", error_event.model_dump())

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get(
    "/history/{user_id}",
    response_model=APIResponse[HistoryResponseData],
    status_code=status.HTTP_200_OK,
)
async def get_history(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[HistoryResponseData]:
    result = await HistoryService(db).get_user_history(user_id)
    return build_response(
        request=request,
        data=result,
        provider="sqlite",
        metadata={"component": "history", "items_count": len(result.items)},
    )


@router.post(
    "/preferences",
    response_model=APIResponse[PreferenceResponseData],
    status_code=status.HTTP_200_OK,
)
async def save_preferences(
    payload: PreferenceRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PreferenceResponseData]:
    result = await PreferenceService(db).upsert_preferences(payload)
    return build_response(
        request=request,
        data=result,
        provider="sqlite",
        metadata={"component": "preferences", "action": "upsert"},
    )


@router.get(
    "/preferences/{user_id}",
    response_model=APIResponse[PreferenceResponseData],
    status_code=status.HTTP_200_OK,
)
async def get_preferences(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PreferenceResponseData]:
    result = await PreferenceService(db).get_preferences(user_id)
    return build_response(
        request=request,
        data=result,
        provider="sqlite",
        metadata={"component": "preferences", "action": "fetch"},
    )


@router.post(
    "/generate-prompt",
    response_model=APIResponse[GeneratePromptResponseData],
    status_code=status.HTTP_200_OK,
)
async def generate_prompt(
    payload: GeneratePromptRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GeneratePromptResponseData]:
    result = await PromptEngine(db).generate_prompt_bundle(payload)
    return build_response(
        request=request,
        data=result,
        provider="prompt-engine",
        metadata={
            "component": "generate-prompt",
            "intent": result.classification.intent,
        },
    )


@router.post(
    "/images/generate",
    response_model=APIResponse[ImageGenerateResponseData],
    status_code=status.HTTP_200_OK,
)
async def generate_images(
    payload: ImageGenerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ImageGenerateResponseData]:
    result = await ImageService(db).generate_images(payload)
    return build_response(
        request=request,
        data=result,
        provider=result.provider,
        metadata={"component": "images", "count": len(result.images), "model": result.model},
    )
