"""Conversation / message data access."""
import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.orm import Conversation, Message


def _title_from_question(question: str, max_len: int = 80) -> str:
    t = " ".join(question.split())
    if len(t) <= max_len:
        return t or "New conversation"
    return t[: max_len - 1] + "…"


class ConversationRepository:
    async def list_for_user(self, session: AsyncSession, clerk_user_id: str) -> list[Conversation]:
        has_message = exists().where(Message.conversation_id == Conversation.id)
        result = await session.execute(
            select(Conversation)
            .where(Conversation.clerk_user_id == clerk_user_id)
            .where(has_message)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_messages(self, session: AsyncSession, conversation_id: str) -> list[Message]:
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def get(
        self, session: AsyncSession, conversation_id: str, clerk_user_id: str
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

    async def create(
        self, session: AsyncSession, clerk_user_id: str, title: str = "New conversation"
    ) -> Conversation:
        conv = Conversation(clerk_user_id=clerk_user_id, title=title)
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
        return conv

    async def delete(
        self, session: AsyncSession, conversation_id: str, clerk_user_id: str
    ) -> bool:
        conv = await self.get(session, conversation_id, clerk_user_id)
        if not conv:
            return False
        await session.delete(conv)
        await session.commit()
        return True

    async def add_message(
        self,
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

    @staticmethod
    def messages_to_chat_history(messages: list[Message], limit: int = 10) -> list[dict[str, str]]:
        history: list[dict[str, str]] = []
        for m in messages[-limit:]:
            if m.role == "user":
                history.append({"role": "user", "content": m.content})
            elif m.role == "assistant":
                history.append({"role": "assistant", "content": m.content})
        return history

    @staticmethod
    def conversation_to_dict(conv: Conversation) -> dict[str, Any]:
        return {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }

    async def conversation_detail_dict(
        self, session: AsyncSession, conv: Conversation
    ) -> dict[str, Any]:
        data = self.conversation_to_dict(conv)
        msgs = await self.list_messages(session, conv.id)
        data["messages"] = [self.message_to_dict(m) for m in msgs]
        return data

    @staticmethod
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
