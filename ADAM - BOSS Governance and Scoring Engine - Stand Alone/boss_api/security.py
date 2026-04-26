"""Minimal token-based authentication layer.

The default is permissive (auth disabled) to keep local development
friction-free. When ``BOSS_AUTH_ENABLED=true`` the API requires a
bearer token that is present in ``BOSS_ADMIN_TOKENS``. Production
deployments should layer a proper OIDC or mTLS gateway in front.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from boss_api.config import Settings, get_settings


async def require_token(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    settings: Settings = Depends(get_settings),
) -> str:
    """Validate a bearer token and return the caller identity."""
    if not settings.auth_enabled:
        return "anonymous"

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token or token not in settings.admin_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token is not authorized for the BOSS Engine.",
        )
    return token
