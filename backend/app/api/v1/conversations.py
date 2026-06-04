import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.controllers.conversation_controller import ConversationController
from backend.app.dependencies.container import get_conversation_service
from backend.app.infrastructure.clerk.auth import require_user
from backend.app.infrastructure.database.session import get_db_session
from backend.app.schemas.conversation import (
    ConversationCreateSchema,
    ConversationDetailSchema,
    ConversationSummarySchema,
)
from backend.app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_controller(
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationController:
    return ConversationController(service)


@router.get("", response_model=list[ConversationSummarySchema])
async def list_conversations(
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    controller: ConversationController = Depends(get_conversation_controller),
):
    return await controller.list(session, user["clerk_user_id"])


@router.post("", response_model=ConversationSummarySchema)
async def create_conversation(
    body: ConversationCreateSchema,
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    controller: ConversationController = Depends(get_conversation_controller),
):
    return await controller.create(session, user["clerk_user_id"], body)


@router.get("/{conversation_id}", response_model=ConversationDetailSchema)
async def get_conversation(
    conversation_id: str,
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    controller: ConversationController = Depends(get_conversation_controller),
):
    detail = await controller.get(session, conversation_id, user["clerk_user_id"])
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return detail


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    controller: ConversationController = Depends(get_conversation_controller),
):
    ok = await controller.delete(session, conversation_id, user["clerk_user_id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}
