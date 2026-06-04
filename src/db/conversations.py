"""Conversation / message persistence helpers."""
import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Conversation, Message


def _title_from_question(question: str, max_len: int = 80) -> str:
    t = " ".join(question.split())
    if len(t) <= max_len:
        return t or "New conversation"
    return t[: max_len - 1] + "…"


async def list_conversations(session: AsyncSession, clerk_user_id: str) -> list[Conversation]:
    """Only conversations that have at least one saved message."""
    has_message = exists().where(
        Message.conversation_id == Conversation.id,
    )
    result = await session.execute(
        select(Conversation)
        .where(Conversation.clerk_user_id == clerk_user_id)
        .where(has_message)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def list_messages(session: AsyncSession, conversation_id: str) -> list[Message]:
    """Load messages in-session (avoids async lazy-load on conv.messages)."""
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


async def get_conversation(
    session: AsyncSession, conversation_id: str, clerk_user_id: str
) -> Optional[Conversation]:
    result = await session.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.clerk_user_id == clerk_user_id,
        )
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one_or_none()


async def create_conversation(
    session: AsyncSession, clerk_user_id: str, title: str = "New conversation"
) -> Conversation:
    conv = Conversation(clerk_user_id=clerk_user_id, title=title)
    session.add(conv)
    await session.commit()
    await session.refresh(conv)
    return conv


async def delete_conversation(
    session: AsyncSession, conversation_id: str, clerk_user_id: str
) -> bool:
    conv = await get_conversation(session, conversation_id, clerk_user_id)
    if not conv:
        return False
    await session.delete(conv)
    await session.commit()
    return True


async def add_message(
    session: AsyncSession,
    conversation: Conversation,
    role: str,
    content: str,
    metadata: Optional[dict[str, Any]] = None,
) -> Message:
    msg = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    session.add(msg)
    conversation.updated_at = datetime.now(timezone.utc)
    if role == "user" and conversation.title == "New conversation":
        conversation.title = _title_from_question(content)
    await session.commit()
    await session.refresh(msg)
    return msg


def messages_to_chat_history(messages: list[Message], limit: int = 10) -> list[dict[str, str]]:
    """Map stored messages to API chat_history (excludes in-flight)."""
    history: list[dict[str, str]] = []
    for m in messages[-limit:]:
        if m.role == "user":
            history.append({"role": "user", "content": m.content})
        elif m.role == "assistant":
            history.append({"role": "assistant", "content": m.content})
    return history


def conversation_to_dict(conv: Conversation) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
    }
    return data


async def conversation_detail_dict(
    session: AsyncSession, conv: Conversation
) -> dict[str, Any]:
    data = conversation_to_dict(conv)
    msgs = await list_messages(session, conv.id)
    data["messages"] = [message_to_dict(m) for m in msgs]
    return data


def message_to_dict(m: Message) -> dict[str, Any]:
    meta = None
    if m.metadata_json:
        try:
            meta = json.loads(m.metadata_json)
        except json.JSONDecodeError:
            meta = None
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "created_at": m.created_at.isoformat(),
        "metadata": meta,
    }
