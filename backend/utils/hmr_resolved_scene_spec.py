"""Normalized resolved scene asset helpers for HMR.

This module is the first small boundary between scene asset planning and the
renderer loop. It keeps the public report fields compatible with existing HMR
reports while giving source-specific adapters a normalized asset shape.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

try:
    from .hmr_playwright_capture import resolve_hmr_playwright_capture
except ImportError:  # pragma: no cover - direct script execution fallback
    from hmr_playwright_capture import resolve_hmr_playwright_capture


@dataclass
class ResolvedSceneAsset:
    """JSON-serializable normalized asset resolution result."""

    resolved_asset_type: str | None = None
    resolved_asset_path: str | None = None
    resolved_asset_paths: list[str] = field(default_factory=list)
    resolved_asset_provider: str | None = None
    asset_resolution_status: str = "not_attempted"
    fallback_used: bool = True
    query_used: str | None = None
    queries_attempted: list[str] = field(default_factory=list)
    provider_available: bool | None = None
    missing_config: list[str] = field(default_factory=list)
    html_fallback_path: str | None = None
    html_fallback_paths: list[str] = field(default_factory=list)
    playwright_motion_mode: str | None = None
    capture_steps: list[str] = field(default_factory=list)
    visible_interaction: bool | None = None
    saved_chrome_profile_used: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_report_fields(cls, fields: dict[str, Any]) -> "ResolvedSceneAsset":
        """Build a normalized asset from legacy flat report fields."""
        return cls(
            resolved_asset_type=fields.get("resolved_asset_type"),
            resolved_asset_path=fields.get("resolved_asset_path"),
            resolved_asset_paths=list(fields.get("resolved_asset_paths") or []),
            resolved_asset_provider=fields.get("resolved_asset_provider"),
            asset_resolution_status=str(fields.get("asset_resolution_status") or "not_attempted"),
            fallback_used=bool(fields.get("fallback_used", True)),
            query_used=fields.get("query_used"),
            queries_attempted=list(fields.get("queries_attempted") or []),
            provider_available=fields.get("provider_available"),
            missing_config=list(fields.get("missing_config") or []),
            html_fallback_path=fields.get("html_fallback_path"),
            html_fallback_paths=list(fields.get("html_fallback_paths") or []),
            playwright_motion_mode=fields.get("playwright_motion_mode"),
            capture_steps=list(fields.get("capture_steps") or []),
            visible_interaction=fields.get("visible_interaction"),
            saved_chrome_profile_used=fields.get("saved_chrome_profile_used"),
            metadata=dict(fields.get("metadata") or {}),
        )

    def to_report_fields(self) -> dict[str, Any]:
        """Return the existing flat HMR report contract."""
        return asdict(self)


@dataclass
class ResolvedSceneSpec:
    """Optional normalized scene spec for future slices."""

    scene_id: str
    template: str
    duration: float
    scene: dict[str, Any]
    asset_strategy: dict[str, Any]
    resolved_asset: ResolvedSceneAsset
    render_config: dict[str, Any] = field(default_factory=dict)
    report: dict[str, Any] = field(default_factory=dict)

    def to_report_fields(self) -> dict[str, Any]:
        data = asdict(self)
        data["resolved_asset"] = self.resolved_asset.to_report_fields()
        return data


PlaywrightResolver = Callable[[dict[str, Any], str, str | Path, int, int], dict[str, Any]]


def resolve_playwright_scene_asset(
    scene: dict[str, Any],
    asset_strategy: dict[str, Any],
    output_dir: str | Path,
    width: int,
    height: int,
    *,
    capture_resolver: PlaywrightResolver = resolve_hmr_playwright_capture,
) -> dict[str, Any]:
    """Resolve a Playwright scene asset and preserve the existing report shape."""
    capture_hint = str(asset_strategy.get("capture_hint") or "")
    raw_result = capture_resolver(scene, capture_hint, output_dir, width, height)
    asset = ResolvedSceneAsset.from_report_fields(raw_result)
    if asset.resolved_asset_type == "playwright_capture" and asset.asset_resolution_status != "resolved":
        asset.resolved_asset_type = None
        asset.fallback_used = True
    return asset.to_report_fields()
