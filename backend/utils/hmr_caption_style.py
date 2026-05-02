"""Caption style profiles and timing metadata for HMR captions."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CaptionStyleProfile:
    id: str
    bounce_enabled: bool
    pop_scale: float
    emphasis_keywords: tuple[str, ...]
    max_words_per_chunk: int
    safe_area: dict[str, float]
    animation_in: float
    animation_out: float
    highlight_style: str
    font_weight: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["emphasis_keywords"] = list(self.emphasis_keywords)
        return data


CAPTION_STYLE_PROFILES: dict[str, CaptionStyleProfile] = {
    "modern_bounce": CaptionStyleProfile(
        id="modern_bounce",
        bounce_enabled=True,
        pop_scale=1.12,
        emphasis_keywords=(
            "save",
            "saved",
            "found",
            "leak",
            "hidden",
            "stop",
            "compare",
            "before",
            "after",
            "today",
            "money",
        ),
        max_words_per_chunk=4,
        safe_area={"top": 0.12, "bottom": 0.82, "left": 0.08, "right": 0.92},
        animation_in=0.16,
        animation_out=0.1,
        highlight_style="mint_keyword_pop",
        font_weight="heavy",
    ),
    "clean_proof": CaptionStyleProfile(
        id="clean_proof",
        bounce_enabled=False,
        pop_scale=1.0,
        emphasis_keywords=("save", "compare", "proof", "result"),
        max_words_per_chunk=5,
        safe_area={"top": 0.14, "bottom": 0.78, "left": 0.08, "right": 0.92},
        animation_in=0.08,
        animation_out=0.08,
        highlight_style="subtle_mint",
        font_weight="bold",
    ),
    "high_energy": CaptionStyleProfile(
        id="high_energy",
        bounce_enabled=True,
        pop_scale=1.16,
        emphasis_keywords=("stop", "wait", "found", "save", "leak", "secret", "now"),
        max_words_per_chunk=3,
        safe_area={"top": 0.12, "bottom": 0.84, "left": 0.07, "right": 0.93},
        animation_in=0.14,
        animation_out=0.08,
        highlight_style="yellow_pop",
        font_weight="heavy",
    ),
}


def get_caption_style_profile(profile_id: str | None = None) -> CaptionStyleProfile:
    if not profile_id:
        return CAPTION_STYLE_PROFILES["modern_bounce"]
    try:
        return CAPTION_STYLE_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown caption style profile: {profile_id}") from exc


def _round_time(value: float) -> float:
    return round(max(0.0, float(value)), 3)


def emphasized_words(text: str, profile: CaptionStyleProfile) -> list[str]:
    keywords = {word.lower() for word in profile.emphasis_keywords}
    out = []
    for word in re.findall(r"\S+", str(text or "")):
        clean = re.sub(r"[^A-Za-z0-9$]", "", word).lower()
        if re.search(r"[$0-9]", word) or clean in keywords:
            out.append(word)
    return out


def caption_animation_state(
    *,
    event_start: float,
    event_end: float,
    current_time: float,
    profile: CaptionStyleProfile,
) -> dict[str, Any]:
    duration = max(0.001, float(event_end) - float(event_start))
    local = max(0.0, min(duration, float(current_time) - float(event_start)))
    scale = 1.0
    phase = "hold"
    if profile.bounce_enabled and local <= profile.animation_in:
        progress = local / max(0.001, profile.animation_in)
        scale = 1.0 + (profile.pop_scale - 1.0) * (1.0 - abs(1.0 - 2.0 * min(0.5, progress / 2.0)))
        phase = "pop_in"
    elif profile.bounce_enabled and duration - local <= profile.animation_out:
        progress = (duration - local) / max(0.001, profile.animation_out)
        scale = 1.0 + (profile.pop_scale - 1.0) * max(0.0, min(1.0, progress)) * 0.35
        phase = "pop_out"
    return {
        "phase": phase,
        "scale": round(scale, 3),
        "local_time": _round_time(local),
        "event_progress": round(local / duration, 3),
    }


def build_caption_style_plan(
    *,
    caption_events: list[dict[str, Any]],
    profile_id: str | None = None,
) -> dict[str, Any]:
    profile = get_caption_style_profile(profile_id)
    styled_events = []
    for idx, event in enumerate(caption_events):
        text = str(event.get("text") or event.get("caption") or "").strip()
        start = float(event.get("start", 0.0) or 0.0)
        end = float(event.get("end", start) or start)
        styled_events.append(
            {
                "id": f"caption_{idx + 1:02d}",
                "start": _round_time(start),
                "end": _round_time(end),
                "text": text,
                "word_count": len(text.split()),
                "emphasis_words": emphasized_words(text, profile),
                "animation": {
                    "bounce_enabled": profile.bounce_enabled,
                    "animation_in": profile.animation_in,
                    "animation_out": profile.animation_out,
                    "pop_scale": profile.pop_scale,
                },
            }
        )
    return {
        "schema_version": 1,
        "profile": profile.to_dict(),
        "styled_events": styled_events,
        "timing_confidence": "caption_phrase_timing" if caption_events else "fallback_required",
        "debug": {
            "event_count": len(styled_events),
            "max_words_per_chunk": profile.max_words_per_chunk,
            "violations": [
                event
                for event in styled_events
                if int(event["word_count"]) > int(profile.max_words_per_chunk)
            ],
            "render_required": False,
        },
    }


def attach_caption_style_to_report(report: dict[str, Any], caption_style_plan: dict[str, Any]) -> dict[str, Any]:
    report["caption_style_plan"] = caption_style_plan
    report.setdefault("caption_report", {})
    report["caption_report"]["style_profile"] = caption_style_plan.get("profile", {}).get("id")
    report["caption_report"]["bounce_enabled"] = caption_style_plan.get("profile", {}).get("bounce_enabled")
    report["caption_report"]["highlight_style"] = caption_style_plan.get("profile", {}).get("highlight_style")
    return report
