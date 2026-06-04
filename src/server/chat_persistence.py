"""Persist chat turns to SQLite around the streaming pipeline."""
import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.db import conversations as conv_db
from src.db.database import AsyncSessionLocal
from src.db.models import Conversation

logger = logging.getLogger(__name__)


async def begin_turn(
    clerk_user_id: str,
    question: str,
    conversation_id: Optional[str],
) -> tuple[str, list[dict[str, str]]]:
    """
    Ensure conversation exists, save user message, return (conversation_id, chat_history).
    """
    async with AsyncSessionLocal() as session:
        if conversation_id:
            conv = await conv_db.get_conversation(session, conversation_id, clerk_user_id)
            if not conv:
                raise ValueError("Conversation not found")
        else:
            conv = await conv_db.create_conversation(session, clerk_user_id)

        msgs = await conv_db.list_messages(session, conv.id)
        history = conv_db.messages_to_chat_history(msgs)
        await conv_db.add_message(session, conv, "user", question)
        cid = conv.id
        logger.info(
            "[chat] persisted user message conversation_id=%s history_turns=%d",
            cid,
            len(history),
        )
        return cid, history


async def finish_turn(
    clerk_user_id: str,
    conversation_id: str,
    answer: str,
    *,
    search: Optional[dict[str, Any]] = None,
    timing: Optional[dict[str, Any]] = None,
    verification: Optional[dict[str, Any]] = None,
) -> None:
    """Save assistant message after stream completes."""
    meta: dict[str, Any] = {}
    if search is not None:
        meta["search"] = search
    if timing is not None:
        meta["timing"] = timing
    if verification is not None:
        meta["verification"] = verification

    async with AsyncSessionLocal() as session:
        conv = await conv_db.get_conversation(session, conversation_id, clerk_user_id)
        if not conv:
            logger.warning("[chat] finish_turn: conversation %s not found", conversation_id)
            return
        await conv_db.add_message(
            session,
            conv,
            "assistant",
            answer,
            metadata=meta or None,
        )
        logger.info(
            "[chat] persisted assistant message conversation_id=%s chars=%d",
            conversation_id,
            len(answer),
        )
