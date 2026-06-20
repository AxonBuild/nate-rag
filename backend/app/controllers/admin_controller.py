from typing import Any, Optional

from backend.app.schemas.admin import InviteRequestSchema, InviteResponseSchema
from backend.app.services.admin_service import AdminService


class AdminController:
    def __init__(self, service: AdminService):
        self._service = service

    async def create_invitation(self, body: InviteRequestSchema) -> InviteResponseSchema:
        data = await self._service.create_invitation(body.email, body.role)
        return InviteResponseSchema(**data)

    async def resend_invitation(
        self, invitation_id: str, body: InviteRequestSchema
    ) -> InviteResponseSchema:
        data = await self._service.resend_invitation(invitation_id, body.email, body.role)
        return InviteResponseSchema(**data)

    async def list_invitations(self, status: Optional[str] = "pending") -> dict[str, Any]:
        return await self._service.list_invitations(status=status)

    async def list_users(self) -> dict[str, Any]:
        return await self._service.list_users()

    async def delete_user(self, user_id: str) -> dict[str, str]:
        return await self._service.delete_user(user_id)
