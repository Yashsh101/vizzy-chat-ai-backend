from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.base import APIResponse
from app.schemas.chat import (
    ChatRequest,
    ChatResponseData,
    GeneratePromptRequest,
    GeneratePromptResponseData,
    HistoryResponseData,
)
from app.schemas.health import HealthData
from app.schemas.preference import PreferenceRequest, PreferenceResponseData
from app.services.chat_service import ChatService
from app.services.history_service import HistoryService
from app.services.preference_service import PreferenceService
from app.services.prompt_engine import PromptEngine
from app.core.responses import build_response

router = APIRouter()


@router.get("/health", response_model=APIResponse[HealthData], status_code=status.HTTP_200_OK)
def health_check(request: Request) -> APIResponse[HealthData]:
    return build_response(
        request=request,
        data=HealthData(status="ok", service="Vizzy Chat API"),
        provider="system",
        metadata={"component": "health"},
    )


@router.post("/chat", response_model=APIResponse[ChatResponseData], status_code=status.HTTP_200_OK)
def create_chat(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> APIResponse[ChatResponseData]:
    result = ChatService(db).process_chat(payload)
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


@router.get(
    "/history/{user_id}",
    response_model=APIResponse[HistoryResponseData],
    status_code=status.HTTP_200_OK,
)
def get_history(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> APIResponse[HistoryResponseData]:
    result = HistoryService(db).get_user_history(user_id)
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
def save_preferences(
    payload: PreferenceRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> APIResponse[PreferenceResponseData]:
    result = PreferenceService(db).upsert_preferences(payload)
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
def get_preferences(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> APIResponse[PreferenceResponseData]:
    result = PreferenceService(db).get_preferences(user_id)
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
def generate_prompt(
    payload: GeneratePromptRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> APIResponse[GeneratePromptResponseData]:
    result = PromptEngine(db).generate_prompt_bundle(payload)
    return build_response(
        request=request,
        data=result,
        provider="prompt-engine",
        metadata={
            "component": "generate-prompt",
            "intent": result.classification.intent,
        },
    )
