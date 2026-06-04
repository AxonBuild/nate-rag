from typing import Any, Optional

from fastapi import APIRouter, Depends

from backend.app.controllers.admin_controller import AdminController
from backend.app.dependencies.container import get_admin_service
from backend.app.infrastructure.clerk.auth import require_admin
from backend.app.schemas.admin import InviteRequestSchema, InviteResponseSchema
from backend.app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_controller(
    service: AdminService = Depends(get_admin_service),
) -> AdminController:
    return AdminController(service)


@router.post("/invitations", response_model=InviteResponseSchema)
async def create_invitation(
    body: InviteRequestSchema,
    _admin: dict[str, Any] = Depends(require_admin),
    controller: AdminController = Depends(get_admin_controller),
):
    return await controller.create_invitation(body)


@router.get("/invitations")
async def list_invitations(
    status: Optional[str] = "pending",
    _admin: dict[str, Any] = Depends(require_admin),
    controller: AdminController = Depends(get_admin_controller),
):
    return await controller.list_invitations(status=status)
