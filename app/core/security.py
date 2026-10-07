"""API-key authentication for the public API.

A partner ed-tech company authenticates each request with a static API
key in the `X-API-Key` header, checked against the configured set of
valid keys (see app.core.config.Settings.api_keys). This is intentionally
simple -- per-partner scoping, rotation, and rate limiting are real
concerns a production deployment would need but this scaffold does not
attempt.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(_api_key_header)) -> str:
    if api_key is None or api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
        )
    return api_key
