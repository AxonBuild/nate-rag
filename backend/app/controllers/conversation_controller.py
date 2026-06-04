from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.conversation import (
    ConversationCreateSchema,
    ConversationDetailSchema,
    ConversationSummarySchema,
)
from backend.app.services.conversation_service import ConversationService


class ConversationController:
    def __init__(self, service: ConversationService):
        self._service = service

    async def list(
        self, session: AsyncSession, clerk_user_id: str
    ) -> list[ConversationSummarySchema]:
        rows = await self._service.list(session, clerk_user_id)
        return [ConversationSummarySchema(**r) for r in rows]

    async def create(
        self, session: AsyncSession, clerk_user_id: str, body: ConversationCreateSchema
    ) -> ConversationSummarySchema:
        row = await self._service.create(session, clerk_user_id, body.title)
        return ConversationSummarySchema(**row)

    async def get(
        self, session: AsyncSession, conversation_id: str, clerk_user_id: str
    ) -> ConversationDetailSchema | None:
        row = await self._service.get_detail(session, conversation_id, clerk_user_id)
        if not row:
            return None
        return ConversationDetailSchema(**row)

    async def delete(
        self, session: AsyncSession, conversation_id: str, clerk_user_id: str
    ) -> bool:
        return await self._service.delete(session, conversation_id, clerk_user_id)
