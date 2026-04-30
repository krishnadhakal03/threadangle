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

    def flat_report_fields(self) -> dict[str, Any]:
        """Return existing top-level report fields for compatibility."""
        return {
            "scene_id": self.scene_id,
            "template": self.template,
            "duration": round(self.duration, 3),
            "scene_asset_strategy": self.asset_strategy,
            **self.resolved_asset.to_report_fields(),
            **self.report,
        }


PlaywrightResolver = Callable[[dict[str, Any], str, str | Path, int, int], dict[str, Any]]
StockSelector = Callable[[list[str], list[str], set[str], list[str]], tuple[Path | None, dict[str, Any]]]
LocalResolver = Callable[[Any, dict[str, Any]], tuple[Path | None, dict[str, Any]]]
ProviderStatusGetter = Callable[[], dict[str, Any]]


def build_resolved_scene_spec(
    *,
    scene_id: Any,
    template: str,
    duration: float,
    scene: dict[str, Any],
    asset_strategy: dict[str, Any],
    asset_resolution: dict[str, Any],
    bg_path: str | Path | None = None,
    stock_meta: dict[str, Any] | None = None,
) -> ResolvedSceneSpec:
    """Combine scene, strategy, resolved asset, and render metadata."""
    resolved_asset = ResolvedSceneAsset.from_report_fields(asset_resolution)
    render_config = {
        "background_path": str(bg_path) if bg_path else None,
        "has_real_background": bg_path is not None,
        "resolved_asset_path": resolved_asset.resolved_asset_path,
        "resolved_asset_paths": resolved_asset.resolved_asset_paths,
        "playwright_motion_mode": resolved_asset.playwright_motion_mode,
        "capture_steps": resolved_asset.capture_steps,
        "visible_interaction": resolved_asset.visible_interaction,
        "saved_chrome_profile_used": resolved_asset.saved_chrome_profile_used,
    }
    provider_usage = (
        stock_meta
        if bg_path
        else {
            "provider": resolved_asset.resolved_asset_provider,
            "reason": resolved_asset.asset_resolution_status,
        }
    )
    return ResolvedSceneSpec(
        scene_id=str(scene_id),
        template=template,
        duration=float(duration),
        scene=dict(scene or {}),
        asset_strategy=dict(asset_strategy or {}),
        resolved_asset=resolved_asset,
        render_config=render_config,
        report={
            "provider_usage": provider_usage,
            "background_id": str(bg_path) if bg_path else None,
        },
    )


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


def resolve_stock_or_local_scene_asset(
    scene_id: Any,
    asset_strategy: dict[str, Any],
    used_ids: set[str],
    warnings: list[str],
    use_stock_backgrounds: bool,
    *,
    stock_selector: StockSelector,
    local_resolver: LocalResolver,
    provider_status_getter: ProviderStatusGetter,
) -> tuple[Path | None, dict[str, Any]]:
    """Resolve stock/local assets and preserve the existing report shape."""
    queries = [str(query) for query in asset_strategy.get("query_candidates") or [] if str(query).strip()]
    media_order = ["stock_footage", "stock_image"]
    stock_meta: dict[str, Any] = {}
    if use_stock_backgrounds:
        stock_path, stock_meta = stock_selector(queries, media_order, used_ids, warnings)
        if stock_path:
            chosen = stock_meta.get("chosen") or {}
            asset = ResolvedSceneAsset(
                resolved_asset_type=str(chosen.get("media_type") or "stock_footage"),
                resolved_asset_path=str(stock_path),
                resolved_asset_provider=str(chosen.get("provider") or "stock_provider"),
                asset_resolution_status="resolved",
                fallback_used=False,
                query_used=stock_meta.get("query_used"),
                queries_attempted=list(stock_meta.get("queries_attempted") or queries),
                provider_available=stock_meta.get("provider_available"),
                missing_config=list(stock_meta.get("missing_config") or []),
            )
            return stock_path, asset.to_report_fields()

    local_path, local_meta = local_resolver(scene_id, asset_strategy)
    if local_path:
        local_meta["queries_attempted"] = queries
        local_meta["provider_available"] = stock_meta.get("provider_available", provider_status_getter().get("provider_available"))
        local_meta["missing_config"] = stock_meta.get("missing_config") or []
        return local_path, ResolvedSceneAsset.from_report_fields(local_meta).to_report_fields()

    provider_status = provider_status_getter()
    missing_config = list(provider_status.get("missing_config") or [])
    missing_config.extend(local_meta.get("missing_config") or [])
    status = "stock_provider_keys_not_configured_and_local_asset_missing"
    if provider_status.get("provider_available"):
        status = "stock_unresolved_and_local_asset_missing"
    asset = ResolvedSceneAsset(
        resolved_asset_type=None,
        resolved_asset_path=None,
        resolved_asset_provider=None,
        asset_resolution_status=status,
        fallback_used=True,
        query_used=stock_meta.get("query_used"),
        queries_attempted=list(stock_meta.get("queries_attempted") or queries),
        provider_available=provider_status.get("provider_available"),
        missing_config=missing_config,
    )
    return None, asset.to_report_fields()
