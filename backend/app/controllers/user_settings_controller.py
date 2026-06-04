from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.user_settings import (
    SystemPromptResponseSchema,
    SystemPromptUpdateSchema,
)
from backend.app.services.user_settings_service import UserSettingsService


class UserSettingsController:
    def __init__(self, service: UserSettingsService):
        self._service = service

    async def get_system_prompt(
        self, session: AsyncSession, clerk_user_id: str
    ) -> SystemPromptResponseSchema:
        data = await self._service.get_system_prompt(session, clerk_user_id)
        return SystemPromptResponseSchema(**data)

    async def save_system_prompt(
        self,
        session: AsyncSession,
        clerk_user_id: str,
        body: SystemPromptUpdateSchema,
    ) -> SystemPromptResponseSchema:
        data = await self._service.save_system_prompt(
            session, clerk_user_id, body.system_prompt
        )
        return SystemPromptResponseSchema(**data)
