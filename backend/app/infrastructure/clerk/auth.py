"""Clerk JWT verification and admin checks."""
import base64
import logging
from typing import Any, Optional

import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)
_jwks_client: Optional[PyJWKClient] = None

CLERK_API = "https://api.clerk.com/v1"


def _issuer_from_publishable_key(pk: str) -> Optional[str]:
    try:
        encoded = pk.split("_", 2)[2].rstrip("$")
        pad = "=" * (-len(encoded) % 4)
        slug = base64.b64decode(encoded + pad).decode().rstrip("$")
        return f"https://{slug}"
    except Exception:
        return None


def get_clerk_issuer() -> str:
    if settings.clerk_issuer:
        return settings.clerk_issuer.rstrip("/")
    if settings.clerk_publishable_key:
        derived = _issuer_from_publishable_key(settings.clerk_publishable_key)
        if derived:
            return derived
    raise HTTPException(
        status_code=503,
        detail="Clerk issuer not configured. Set CLERK_ISSUER or CLERK_PUBLISHABLE_KEY in .env",
    )


def _jwks() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        issuer = get_clerk_issuer()
        _jwks_client = PyJWKClient(f"{issuer}/.well-known/jwks.json")
    return _jwks_client


def decode_session_token(token: str) -> dict[str, Any]:
    issuer = get_clerk_issuer()
    try:
        key = _jwks().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            issuer=issuer,
            # Allow small clock skew (common during rapid account switching / Windows time drift).
            # Without this, we can intermittently see "The token is not yet valid (iat)" for a
            # newly-issued Clerk session token.
            leeway=60,
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as e:
        logger.warning("JWT verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired session") from e


async def fetch_clerk_user(user_id: str) -> dict[str, Any]:
    if not settings.clerk_secret_key:
        raise HTTPException(status_code=503, detail="CLERK_SECRET_KEY is not configured")
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{CLERK_API}/users/{user_id}",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
        )
    if res.status_code == 404:
        raise HTTPException(status_code=401, detail="User not found")
    if res.status_code >= 400:
        logger.error("Clerk user fetch failed: %s %s", res.status_code, res.text)
        raise HTTPException(status_code=502, detail="Could not verify user with Clerk")
    return res.json()


def user_is_admin(clerk_user: dict[str, Any]) -> bool:
    role = (clerk_user.get("public_metadata") or {}).get("role")
    return role == "admin"


async def require_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict[str, str]:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authorization required")
    payload = decode_session_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")
    return {"clerk_user_id": user_id}


async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authorization required")
    payload = decode_session_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")
    clerk_user = await fetch_clerk_user(user_id)
    if not user_is_admin(clerk_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return clerk_user
