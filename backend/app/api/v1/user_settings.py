from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.controllers.user_settings_controller import UserSettingsController
from backend.app.dependencies.container import get_user_settings_service
from backend.app.infrastructure.clerk.auth import require_admin, require_user
from backend.app.infrastructure.database.session import get_db_session
from backend.app.schemas.user_settings import (
    SystemPromptResponseSchema,
    SystemPromptUpdateSchema,
)
from backend.app.services.user_settings_service import UserSettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


def get_user_settings_controller(
    service: UserSettingsService = Depends(get_user_settings_service),
) -> UserSettingsController:
    return UserSettingsController(service)


@router.get("/system-prompt", response_model=SystemPromptResponseSchema)
async def get_system_prompt(
    user: dict[str, str] = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    controller: UserSettingsController = Depends(get_user_settings_controller),
):
    return await controller.get_system_prompt(session, user["clerk_user_id"])


@router.put("/system-prompt", response_model=SystemPromptResponseSchema)
async def save_system_prompt(
    body: SystemPromptUpdateSchema,
    admin: dict = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
    controller: UserSettingsController = Depends(get_user_settings_controller),
):
    return await controller.save_system_prompt(session, admin["id"], body)
