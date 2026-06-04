"""Conversation CRUD for chat persistence."""
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import conversations as conv_db
from src.db.database import get_db_session
from src.server.clerk_auth import require_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=500)


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    metadata: Optional[dict[str, Any]] = None


class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageOut]


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
):
    rows = await conv_db.list_conversations(session, user["clerk_user_id"])
    return [conv_db.conversation_to_dict(c) for c in rows]


@router.post("", response_model=ConversationSummary)
async def create_conversation(
    body: ConversationCreate,
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
):
    conv = await conv_db.create_conversation(
        session, user["clerk_user_id"], title=body.title.strip() or "New conversation"
    )
    logger.info("[chat] created conversation id=%s user=%s", conv.id, user["clerk_user_id"])
    return conv_db.conversation_to_dict(conv)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
):
    conv = await conv_db.get_conversation(session, conversation_id, user["clerk_user_id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await conv_db.conversation_detail_dict(session, conv)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
):
    ok = await conv_db.delete_conversation(session, conversation_id, user["clerk_user_id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    logger.info("[chat] deleted conversation id=%s", conversation_id)
    return {"ok": True}
