import logging
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)
CLERK_API = "https://api.clerk.com/v1"


class AdminService:
    def _headers(self) -> dict[str, str]:
        if not settings.clerk_secret_key:
            raise HTTPException(status_code=503, detail="CLERK_SECRET_KEY is not configured")
        return {"Authorization": f"Bearer {settings.clerk_secret_key}"}

    def _redirect_url(self) -> str:
        return settings.clerk_invite_redirect_url or "http://localhost:5173"

    async def create_invitation(self, email: str, role: str) -> dict[str, Any]:
        payload = {
            "email_address": email,
            "redirect_url": self._redirect_url(),
            "public_metadata": {"role": role},
            "notify": True,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                f"{CLERK_API}/invitations",
                headers=self._headers(),
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
        return {
            "id": data["id"],
            "email_address": data.get("email_address") or email,
            "status": data.get("status", "pending"),
            "role": role,
        }

    async def list_invitations(self, status: Optional[str] = "pending") -> dict[str, Any]:
        params = {"status": status} if status else {}
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(
                f"{CLERK_API}/invitations",
                headers=self._headers(),
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
