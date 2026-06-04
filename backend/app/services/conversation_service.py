import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, repo: Optional[ConversationRepository] = None):
        self._repo = repo or ConversationRepository()

    async def list(self, session: AsyncSession, clerk_user_id: str) -> list[dict[str, Any]]:
        rows = await self._repo.list_for_user(session, clerk_user_id)
        return [self._repo.conversation_to_dict(c) for c in rows]

    async def create(
        self, session: AsyncSession, clerk_user_id: str, title: str
    ) -> dict[str, Any]:
        conv = await self._repo.create(
            session, clerk_user_id, title=title.strip() or "New conversation"
        )
        logger.info("[chat] created conversation id=%s user=%s", conv.id, clerk_user_id)
        return self._repo.conversation_to_dict(conv)

    async def get_detail(
        self, session: AsyncSession, conversation_id: str, clerk_user_id: str
    ) -> Optional[dict[str, Any]]:
        conv = await self._repo.get(session, conversation_id, clerk_user_id)
        if not conv:
            return None
        return await self._repo.conversation_detail_dict(session, conv)

    async def delete(
        self, session: AsyncSession, conversation_id: str, clerk_user_id: str
    ) -> bool:
        ok = await self._repo.delete(session, conversation_id, clerk_user_id)
        if ok:
            logger.info("[chat] deleted conversation id=%s", conversation_id)
        return ok
