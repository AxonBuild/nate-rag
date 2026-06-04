import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.controllers.chat_controller import ChatController
from backend.app.dependencies.container import get_chat_service
from backend.app.infrastructure.clerk.auth import require_user
from backend.app.schemas.chat import ChatRequestSchema, ChatResponseSchema
from backend.app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_controller(
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatController:
    return ChatController(chat_service)


@router.post("/", response_model=ChatResponseSchema)
async def chat(
    request: ChatRequestSchema,
    controller: ChatController = Depends(get_chat_controller),
):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        return await controller.chat(request)
    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stream")
async def chat_stream(
    request: ChatRequestSchema,
    user: dict[str, str] = Depends(require_user),
    controller: ChatController = Depends(get_chat_controller),
):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    return StreamingResponse(
        controller.stream_events(request, user["clerk_user_id"]),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
