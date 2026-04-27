from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class VideoFormat(str, Enum):
    short_9x16 = "short_9x16"
    wide_16x9 = "wide_16x9"


class RenderMode(str, Enum):
    draft = "draft"
    final = "final"


class MotionProfile(str, Enum):
    static_clean = "static_clean"
    documentary_dynamic = "documentary_dynamic"
    kinetic_explainer = "kinetic_explainer"
    tutorial_followcam = "tutorial_followcam"


class MotionIntensity(str, Enum):
    low = "low"
    med = "med"
    high = "high"


class VisualSource(str, Enum):
    generated_card = "generated_card"
    stock_footage = "stock_footage"
    playwright_capture = "playwright_capture"
    user_image = "user_image"
    user_video = "user_video"
    proof_screenshot = "proof_screenshot"
    local_dom_reconstruction = "local_dom_reconstruction"


class ProviderStatus(str, Enum):
    pending = "pending"
    resolved = "resolved"
    fallback_used = "fallback_used"
    failed = "failed"
    blocked = "blocked"


class CaptionSafeZone(BaseModel):
    x: int = 54
    y: int = 1450
    width: int = 972
    height: int = 360


class RegenerationPolicy(BaseModel):
    visual: Literal["never", "if_missing", "always"] = "if_missing"
    narration: Literal["never", "if_unlocked", "always"] = "if_unlocked"
    captions: Literal["from_audio", "manual_only"] = "from_audio"
    fallback_allowed: bool = True


class StoryboardScene(BaseModel):
    scene_id: str
    scene_type: str
    duration: float = Field(gt=0)
    narration_text: str
    caption_text: str | None = None
    visual_source: VisualSource
    asset_path: str | None = None
    fallback_asset_path: str | None = None
    lock_visual: bool = False
    lock_narration: bool = False
    allow_caption_edit: bool = True
    allow_narration_regen: bool = True
    caption_safe_zone: CaptionSafeZone = Field(default_factory=CaptionSafeZone)
    proof_label: str | None = None
    privacy_reviewed: bool = False
    provider_used: str | None = None
    provider_status: ProviderStatus = ProviderStatus.pending
    regeneration_policy: RegenerationPolicy = Field(default_factory=RegenerationPolicy)
    motion_profile: MotionProfile = MotionProfile.static_clean
    motion_intensity: MotionIntensity = MotionIntensity.low
    micro_beats: list[str] = Field(default_factory=list)
    supporting_cutaways: list[str] = Field(default_factory=list)
    style: dict[str, Any] = Field(default_factory=dict)

    @field_validator("caption_text")
    @classmethod
    def default_caption(cls, value: str | None) -> str | None:
        return value


class Storyboard(BaseModel):
    project_id: str
    title: str
    niche: str
    template_id: str
    format: VideoFormat = VideoFormat.short_9x16
    render_mode: RenderMode = RenderMode.draft
    style: dict[str, Any] = Field(default_factory=dict)
    variables: dict[str, Any] = Field(default_factory=dict)
    scenes: list[StoryboardScene]

    @field_validator("scenes")
    @classmethod
    def require_scenes(cls, value: list[StoryboardScene]) -> list[StoryboardScene]:
        if not value:
            raise ValueError("storyboard must contain at least one scene")
        return value


def load_storyboard(path: str | Path) -> Storyboard:
    return Storyboard.model_validate_json(Path(path).read_text(encoding="utf-8"))


def save_storyboard(storyboard: Storyboard, path: str | Path) -> None:
    Path(path).write_text(json.dumps(storyboard.model_dump(mode="json"), indent=2), encoding="utf-8")
