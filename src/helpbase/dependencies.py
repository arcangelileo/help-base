"""Shared FastAPI dependencies."""

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.database import get_db
from helpbase.models.user import User
from helpbase.services.auth import decode_access_token, get_user_by_id


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User:
    """Extract and validate the current user from the JWT cookie.

    Raises HTTPException 401 if token is missing/invalid or user not found.
    """
    if not access_token:
        # For HTML pages, redirect to login instead of returning JSON error
        if "text/html" in request.headers.get("accept", ""):

            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/auth/login"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(access_token)
    if payload is None:
        if "text/html" in request.headers.get("accept", ""):

            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/auth/login"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await get_user_by_id(db, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User | None:
    """Get current user if authenticated, otherwise return None.

    Does not raise errors — useful for pages visible to both guests and users.
    """
    if not access_token:
        return None

    payload = decode_access_token(access_token)
    if payload is None:
        return None

    user = await get_user_by_id(db, payload["sub"])
    if user is None or not user.is_active:
        return None

    return user
