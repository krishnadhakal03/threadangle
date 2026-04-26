from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .schema import ProviderStatus, StoryboardScene, VisualSource


PROVIDER_ORDER = [
    "user_locked_asset",
    "user_proof_insert",
    "playwright_capture",
    "stock_footage",
    "generated_card",
    "local_dom_reconstruction",
]


@dataclass
class ProviderDecision:
    provider: str
    status: ProviderStatus
    asset_path: Path | None
    reason: str | None = None
    is_reconstruction: bool = False


def route_scene_provider(scene: StoryboardScene, repo_root: Path) -> ProviderDecision:
    asset = Path(scene.asset_path) if scene.asset_path else None
    if asset and not asset.is_absolute():
        asset = repo_root / asset
    fallback = Path(scene.fallback_asset_path) if scene.fallback_asset_path else None
    if fallback and not fallback.is_absolute():
        fallback = repo_root / fallback

    if scene.lock_visual:
        if asset and asset.exists():
            return ProviderDecision("user_locked_asset", ProviderStatus.resolved, asset)
        return ProviderDecision("user_locked_asset", ProviderStatus.failed, None, "locked asset missing")

    if scene.visual_source in {VisualSource.user_image, VisualSource.user_video, VisualSource.proof_screenshot}:
        if asset and asset.exists():
            return ProviderDecision("user_proof_insert", ProviderStatus.resolved, asset)
        if fallback and fallback.exists() and scene.regeneration_policy.fallback_allowed:
            return ProviderDecision("fallback_asset", ProviderStatus.fallback_used, fallback, "user asset missing; fallback used")
        return ProviderDecision("user_proof_insert", ProviderStatus.failed, None, "user asset missing")

    if scene.visual_source == VisualSource.generated_card:
        return ProviderDecision("generated_card", ProviderStatus.resolved, asset)

    if scene.visual_source == VisualSource.local_dom_reconstruction:
        return ProviderDecision("local_dom_reconstruction", ProviderStatus.resolved, asset, is_reconstruction=True)

    if fallback and fallback.exists() and scene.regeneration_policy.fallback_allowed:
        return ProviderDecision("fallback_asset", ProviderStatus.fallback_used, fallback, "provider unavailable; fallback used")
    return ProviderDecision(str(scene.visual_source.value), ProviderStatus.failed, None, "provider not implemented in MVP")
