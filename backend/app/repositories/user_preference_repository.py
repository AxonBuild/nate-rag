from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.orm import UserPreference


class UserPreferenceRepository:
    async def get(self, session: AsyncSession, clerk_user_id: str) -> Optional[UserPreference]:
        result = await session.execute(
            select(UserPreference).where(UserPreference.clerk_user_id == clerk_user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_system_prompt(
        self, session: AsyncSession, clerk_user_id: str, system_prompt: Optional[str]
    ) -> UserPreference:
        row = await self.get(session, clerk_user_id)
        if row is None:
            row = UserPreference(clerk_user_id=clerk_user_id, system_prompt=system_prompt)
            session.add(row)
        else:
            row.system_prompt = system_prompt
            row.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(row)
        return row
