from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, HTTPException, status

from auth import BETA_WAITLIST_MESSAGE, get_current_user, user_has_beta_full_access
from models import User


DEFAULT_ALLOWED_EMAIL = "krishna.dhakal03@gmail.com"

_active_renders = 0
_active_lock = asyncio.Lock()


def _truthy_env(name: str, default: str = "0") -> bool:
    return str(os.getenv(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", "development").strip().lower() == "production"


def server_video_rendering_enabled() -> bool:
    return _truthy_env("ENABLE_SERVER_VIDEO_RENDERING", "0")


def allowed_video_render_email() -> str:
    return os.getenv("VIDEO_RENDER_ALLOWED_USER_EMAIL", DEFAULT_ALLOWED_EMAIL).strip().lower()


def max_concurrent_video_renders() -> int:
    try:
        return max(1, int(os.getenv("MAX_CONCURRENT_VIDEO_RENDERS", "1")))
    except ValueError:
        return 1


def max_video_duration_seconds() -> int:
    try:
        return max(1, int(os.getenv("MAX_VIDEO_DURATION_SECONDS", "20")))
    except ValueError:
        return 20


def max_video_render_seconds() -> int:
    try:
        return max(1, int(os.getenv("MAX_VIDEO_RENDER_SECONDS", "900")))
    except ValueError:
        return 900


def default_render_resolution() -> str:
    return os.getenv("DEFAULT_RENDER_RESOLUTION", "720x1280").strip() or "720x1280"


def assert_video_duration_allowed(duration_seconds: float | int | None) -> None:
    if duration_seconds is None:
        return
    try:
        duration = float(duration_seconds)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid render duration.")
    if duration > max_video_duration_seconds():
        raise HTTPException(
            status_code=400,
            detail=f"Video duration exceeds {max_video_duration_seconds()} seconds.",
        )


async def require_video_render_access(
    current_user: User = Depends(get_current_user),
) -> User:
    if not server_video_rendering_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server-side video rendering is disabled.",
        )

    user_email = str(getattr(current_user, "email", "") or "").strip().lower()
    if not user_has_beta_full_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=BETA_WAITLIST_MESSAGE,
        )

    if not user_email or user_email != allowed_video_render_email():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server-side video rendering is restricted.",
        )

    return current_user


async def acquire_render_slot() -> object:
    global _active_renders
    async with _active_lock:
        if _active_renders >= max_concurrent_video_renders():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Another video render is already active.",
            )
        _active_renders += 1
    return object()


async def release_render_slot(token: object | None) -> None:
    global _active_renders
    if token is None:
        return
    async with _active_lock:
        _active_renders = max(0, _active_renders - 1)


@asynccontextmanager
async def render_slot():
    token = await acquire_render_slot()
    try:
        yield token
    finally:
        await release_render_slot(token)


async def run_with_render_timeout(coro: Any):
    return await asyncio.wait_for(coro, timeout=max_video_render_seconds())


def reset_render_guard_for_tests() -> None:
    global _active_renders
    _active_renders = 0
