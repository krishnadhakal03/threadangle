"""Helpers for converting internal script/planning text into public narration/captions.

The planner may use structural labels such as HOOK, BODY, CTA, STEP ONE, or
PAYOFF 1 to segment a short. Those labels are useful internally, but they must
not leak into voiceover, subtitles, captions, thumbnails, or scene text.
"""

from __future__ import annotations

import re
from typing import Any

_PUBLIC_LABEL_PATTERNS = [
    # Line-leading workflow labels.
    re.compile(r"(?im)^\s*(hook|body|cta)\s*:\s*"),
    # Segment labels that may appear at line start or after sentence breaks.
    re.compile(r"(?im)(^|(?<=[.!?])\s+)(payoff\s*[1-9][0-9]*|step\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|[1-9][0-9]*))\s*:\s*"),
]

_EXTRA_SPACE_RE = re.compile(r"[ \t]{2,}")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.!?;:])")


def sanitize_public_script_text(value: Any) -> str:
    """Strip internal planning labels from user-facing text.

    Examples:
    - ``PAYOFF 1: Writing + research`` -> ``Writing + research``
    - ``Hook: Stop paying for AI`` -> ``Stop paying for AI``
    - ``Step one: Open the app`` -> ``Open the app``
    """
    text = str(value or "")
    if not text.strip():
        return ""

    # Normalize newlines first so line-leading regexes behave consistently.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for pattern in _PUBLIC_LABEL_PATTERNS:
        text = pattern.sub(lambda m: m.group(1) if m.lastindex and m.group(1) and m.group(1).strip() not in {"hook", "body", "cta"} else "", text)

    # A simpler second pass catches labels at comma/dash boundaries without
    # being too aggressive on normal prose.
    text = re.sub(
        r"(?i)(^|[\n\-–—])\s*(payoff\s*[1-9][0-9]*|step\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|[1-9][0-9]*))\s*:\s*",
        lambda m: m.group(1),
        text,
    )

    text = _EXTRA_SPACE_RE.sub(" ", text)
    text = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sanitize_public_scene(scene: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a scene with public text fields sanitized."""
    out = dict(scene or {})
    for key in (
        "script",
        "subtitle",
        "caption_text",
        "narration_text",
        "on_screen_text",
        "headline",
        "description",
        "source_text",
    ):
        if key in out and isinstance(out.get(key), str):
            out[key] = sanitize_public_script_text(out.get(key))
    return out


def sanitize_public_scenes(scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sanitize public text fields for a list of scene dictionaries."""
    return [sanitize_public_scene(scene) if isinstance(scene, dict) else scene for scene in (scenes or [])]
