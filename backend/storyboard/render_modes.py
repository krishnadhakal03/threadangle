from __future__ import annotations

import os

from .schema import RenderMode, Storyboard


PAID_PROVIDERS = {"elevenlabs", "runway", "runwayml", "openai", "google-genai", "anthropic"}


def assert_provider_allowed(storyboard: Storyboard, provider: str, purpose: str) -> None:
    normalized = provider.lower()
    if storyboard.render_mode == RenderMode.draft and normalized in PAID_PROVIDERS:
        raise RuntimeError(f"Draft mode blocks paid provider '{provider}' for {purpose}")
    if normalized == "elevenlabs" and os.getenv("ALLOW_PREMIUM_AUDIO") != "1":
        raise RuntimeError("ElevenLabs blocked: set ALLOW_PREMIUM_AUDIO=1 in final mode")
    if normalized in {"runway", "runwayml"} and os.getenv("ALLOW_RUNWAY") != "1":
        raise RuntimeError("Runway blocked: set ALLOW_RUNWAY=1 in final mode")


def assert_draft_mode_safe(storyboard: Storyboard) -> list[str]:
    warnings: list[str] = []
    for scene in storyboard.scenes:
        provider = (scene.provider_used or "").lower()
        if storyboard.render_mode == RenderMode.draft and provider in PAID_PROVIDERS:
            warnings.append(f"{scene.scene_id}: paid provider '{provider}' blocked in draft mode")
    return warnings
