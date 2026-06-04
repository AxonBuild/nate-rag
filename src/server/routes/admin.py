"""Admin routes — Clerk invitations (admins only)."""
import logging
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from src.ingestion.config import settings
from src.server.clerk_auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

CLERK_API = "https://api.clerk.com/v1"


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="client", pattern="^(admin|client)$")


class InviteResponse(BaseModel):
    id: str
    email_address: str
    status: str
    role: str


def _clerk_headers() -> dict[str, str]:
    if not settings.clerk_secret_key:
        raise HTTPException(status_code=503, detail="CLERK_SECRET_KEY is not configured")
    return {"Authorization": f"Bearer {settings.clerk_secret_key}"}


def _redirect_url() -> str:
    return settings.clerk_invite_redirect_url or "http://localhost:5173"


@router.post("/invitations", response_model=InviteResponse)
async def create_invitation(
    body: InviteRequest,
    _admin: dict[str, Any] = Depends(require_admin),
):
    payload = {
        "email_address": body.email,
        "redirect_url": _redirect_url(),
        "public_metadata": {"role": body.role},
        "notify": True,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.post(
            f"{CLERK_API}/invitations",
            headers=_clerk_headers(),
            json=payload,
        )
    if res.status_code == 422:
        detail = res.json().get("errors", [{}])[0]
        msg = detail.get("long_message") or detail.get("message") or "Invalid invitation"
        raise HTTPException(status_code=422, detail=msg)
    if res.status_code >= 400:
        logger.error("Clerk invite failed: %s %s", res.status_code, res.text)
        raise HTTPException(status_code=502, detail="Clerk could not send invitation")
    data = res.json()
    return InviteResponse(
        id=data["id"],
        email_address=data.get("email_address") or body.email,
        status=data.get("status", "pending"),
        role=body.role,
    )


@router.get("/invitations")
async def list_invitations(
    status: Optional[str] = "pending",
    _admin: dict[str, Any] = Depends(require_admin),
):
    params = {}
    if status:
        params["status"] = status
    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.get(
            f"{CLERK_API}/invitations",
            headers=_clerk_headers(),
            params=params,
        )
    if res.status_code >= 400:
        logger.error("Clerk list invitations failed: %s %s", res.status_code, res.text)
        raise HTTPException(status_code=502, detail="Could not load invitations")
    data = res.json()
    items = data if isinstance(data, list) else data.get("data", [])
    return {
        "invitations": [
            {
                "id": inv.get("id"),
                "email_address": inv.get("email_address"),
                "status": inv.get("status"),
                "role": (inv.get("public_metadata") or {}).get("role", "client"),
                "created_at": inv.get("created_at"),
            }
            for inv in items
        ]
    }
