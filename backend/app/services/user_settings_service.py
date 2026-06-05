from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.user_preference_repository import UserPreferenceRepository
from backend.app.services.rag.prompts.defaults import get_default_system_prompt


class UserSettingsService:
    """
    Shared (global) settings for the whole app.

    Note: We currently store the shared prompt in `user_preferences` under a
    fixed synthetic key to avoid a migration.
    """

    GLOBAL_PROMPT_KEY = "__global__"

    def __init__(self, repo: UserPreferenceRepository | None = None):
        self._repo = repo or UserPreferenceRepository()

    def default_system_prompt(self) -> str:
        return get_default_system_prompt()

    async def get_system_prompt(self, session: AsyncSession, clerk_user_id: str) -> dict:
        default = self.default_system_prompt()
        # Shared prompt (same for all users)
        row = await self._repo.get(session, self.GLOBAL_PROMPT_KEY)
        custom = (row.system_prompt.strip() if row and row.system_prompt else None) or None
        is_custom = bool(custom and custom != default.strip())
        effective = custom if is_custom else default
        return {
            "default_prompt": default,
            "custom_prompt": custom if is_custom else None,
            "effective_prompt": effective,
            "is_custom": is_custom,
        }

    async def save_system_prompt(
        self, session: AsyncSession, clerk_user_id: str, system_prompt: str
    ) -> dict:
        default = self.default_system_prompt()
        text = system_prompt.strip()
        to_store = None if not text or text == default.strip() else text
        # Shared prompt (same for all users)
        await self._repo.upsert_system_prompt(session, self.GLOBAL_PROMPT_KEY, to_store)
        return await self.get_system_prompt(session, clerk_user_id)
