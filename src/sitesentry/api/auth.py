"""API key authentication with constant-time comparison."""

from __future__ import annotations

import hmac

from fastapi import HTTPException, Request, status


def verify_api_key(expected_key: str | None, request: Request) -> None:
    """Verify the Bearer token in the Authorization header.

    Uses hmac.compare_digest to prevent timing attacks.
    Raises HTTP 401 if the key is missing or incorrect.
    If expected_key is None (not configured), auth is skipped.
    """
    if expected_key is None:
        return  # No API key configured – skip auth

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://sitesentry.invalid/errors/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Missing or malformed Authorization header. "
                "Use: Authorization: Bearer <api-key>",
            },
        )

    provided = auth_header[len("Bearer ") :]
    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(provided.encode(), expected_key.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://sitesentry.invalid/errors/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Invalid API key.",
            },
        )
