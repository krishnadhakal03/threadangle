"""Hybrid Motion Renderer v1.

Frame-level OpenCV/PIL compositor for fast 9:16 short-form videos. This module
is deliberately independent from MoviePy TextClip and paid generation APIs.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import cv2
import httpx
import numpy as np

try:
    from .hybrid_scene_templates import draw_caption_band, get_template
    from .hmr_scene_asset_strategy import detect_hmr_asset_domain_from_text, local_asset_domain_folders, plan_hmr_scene_assets
    from .hmr_sfx import build_sfx_plan
    from .hmr_audio_timeline import attach_audio_timeline_to_report, build_audio_binding_timeline, execute_audio_mix_plan
    from .hmr_caption_style import attach_caption_style_to_report, build_caption_style_plan, caption_animation_state, get_caption_style_profile
    from .hmr_editing_rhythm import attach_quick_cut_schedule_to_report, build_quick_cut_schedule
    from .hmr_montage import attach_montage_plan_to_report, build_montage_execution_report, build_montage_plan
    from .hmr_proof_assets import build_proof_asset_plan, proof_asset_for_scene, proof_asset_resolution_fields
    from .hmr_scene_iteration import apply_scene_locks_and_overrides
    from .hmr_agency_templates import select_agency_template_for_scenes
    from .hmr_agency_presets import select_agency_preset_for_scenes
    from .hmr_resolved_scene_spec import build_resolved_scene_spec, resolve_playwright_scene_asset, resolve_stock_or_local_scene_asset
except ImportError:  # pragma: no cover - direct script execution fallback
    from hybrid_scene_templates import draw_caption_band, get_template
    from hmr_scene_asset_strategy import detect_hmr_asset_domain_from_text, local_asset_domain_folders, plan_hmr_scene_assets
    from hmr_sfx import build_sfx_plan
    from hmr_audio_timeline import attach_audio_timeline_to_report, build_audio_binding_timeline, execute_audio_mix_plan
    from hmr_caption_style import attach_caption_style_to_report, build_caption_style_plan, caption_animation_state, get_caption_style_profile
    from hmr_editing_rhythm import attach_quick_cut_schedule_to_report, build_quick_cut_schedule
    from hmr_montage import attach_montage_plan_to_report, build_montage_execution_report, build_montage_plan
    from hmr_proof_assets import build_proof_asset_plan, proof_asset_for_scene, proof_asset_resolution_fields
    from hmr_scene_iteration import apply_scene_locks_and_overrides
    from hmr_agency_templates import select_agency_template_for_scenes
    from hmr_agency_presets import select_agency_preset_for_scenes
    from hmr_resolved_scene_spec import build_resolved_scene_spec, resolve_playwright_scene_asset, resolve_stock_or_local_scene_asset


BASE_DIR = Path(__file__).resolve().parents[1]
GENERATED_DIR = BASE_DIR / "generated_videos"
CACHE_DIR = GENERATED_DIR / "cache" / "hybrid_motion"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPO_ROOT = BASE_DIR.parent
LOCAL_HMR_ASSET_DIR = REPO_ROOT / "assets" / "hmr_local"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

HYBRID_METHOD_TO_TEMPLATE = {
    "stock_plus_motion_overlay": "hook_footage_overlay",
    "local_ai_prompt_capture": "ai_prompt_mock",
    "hybrid_motion_scene": "money_shock_math",
    "comparison_motion_scene": "comparison_split",
    "payoff_motion_scene": "payoff_number_reveal",
    "cta_motion_scene": "cta_callback",
}


def _strip_story_labels(text: str) -> str:
    return re.sub(r"(?i)\b(?:hook|body|cta)\s*:\s*", "", str(text or "")).strip()


def _semantic_caption_chunks(script_text: str, max_words: int = 4) -> list[str]:
    script_text = _strip_story_labels(script_text)
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", script_text or "")
        if sentence.strip()
    ]
    chunks: list[str] = []
    number_words = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "fifteen", "twenty", "thirty", "forty", "fifty", "hundred", "thousand", "million"}
    weak_end_words = {"a", "an", "the", "and", "or", "to", "of", "at", "on", "with", "for", "from", "in"}
    for sentence in sentences:
        words = re.findall(r"\$?\d[\d,]*(?:/\w+)?|[A-Za-z']+", sentence)
        if not words:
            continue
        start = 0
        while start < len(words):
            remaining = len(words) - start
            size = min(max_words, remaining)
            if size > 1 and start + size < len(words):
                last = words[start + size - 1].lower()
                nxt = words[start + size].lower()
                if (last in number_words and nxt in number_words) or last in weak_end_words:
                    size -= 1
            chunk_words = words[start:start + size]
            if chunks and len(chunk_words) == 1 and len(chunks[-1].split()) < max_words:
                chunks[-1] = f"{chunks[-1]} {chunk_words[0]}"
            else:
                chunks.append(" ".join(chunk_words))
            start += size
    return chunks


def split_caption_events(script_text: str, duration: float, max_words: int = 4) -> list[dict[str, Any]]:
    chunks = _semantic_caption_chunks(script_text, max_words=max_words)
    if not chunks:
        return []
    weights = [max(1.0, len(chunk.split()) + (0.35 if re.search(r"[$0-9]", chunk) else 0.0)) for chunk in chunks]
    total_weight = sum(weights) or float(len(chunks))
    events = []
    t = 0.0
    for idx, (chunk, weight) in enumerate(zip(chunks, weights)):
        if idx == len(chunks) - 1:
            end = float(duration)
        else:
            slot = max(0.45, float(duration) * (weight / total_weight))
            end = min(float(duration), t + slot)
        events.append({"start": round(t, 3), "end": round(end, 3), "text": chunk})
        t = end
    return events


def _scene_value(scene: Any, key: str, default: Any = None) -> Any:
    if isinstance(scene, dict):
        return scene.get(key, default)
    return getattr(scene, key, default)


def _scene_blob(scene: Any) -> str:
    return " ".join(
        str(_scene_value(scene, key, "") or "")
        for key in (
            "id",
            "part",
            "scene_type",
            "template",
            "headline",
            "caption_text",
            "source_text",
            "subtitle",
            "visual_description",
            "description",
            "prompt",
            "response",
            "subline",
        )
    ).lower()


def _is_coffee_savings_story(scenes: list[Any], script_text: str) -> bool:
    blob = f"{script_text or ''} {' '.join(_scene_blob(scene) for scene in scenes or [])}".lower()
    return "coffee" in blob and any(token in blob for token in ("cost", "costs", "saving", "savings", "dollar", "$", "month", "year", "workday"))


def _clean_scene_text(value: Any) -> str:
    return _strip_story_labels(str(value or "")).strip()


def _enrich_coffee_savings_scene(scene: Any, idx: int, total: int) -> Any:
    base = dict(scene) if isinstance(scene, dict) else {
        "scene": _scene_value(scene, "scene", idx + 1),
        "start": _scene_value(scene, "start", None),
        "end": _scene_value(scene, "end", None),
        "part": _scene_value(scene, "part", ""),
        "source_text": _scene_value(scene, "source_text", ""),
        "subtitle": _scene_value(scene, "subtitle", ""),
        "visual_description": _scene_value(scene, "visual_description", ""),
        "on_screen_text": _scene_value(scene, "on_screen_text", ""),
    }
    for key in ("caption_text", "source_text", "subtitle", "on_screen_text", "headline"):
        if key in base:
            base[key] = _clean_scene_text(base.get(key))
    text = _clean_scene_text(base.get("caption_text") or base.get("subtitle") or base.get("source_text") or base.get("on_screen_text"))
    part = str(base.get("part") or base.get("scene_type") or "").lower()
    is_cta = idx == total - 1 or part == "cta" or "skip" in text.lower() or "try" in text.lower()

    if idx == 0:
        base.update({
            "template": "grocery_receipt_hook",
            "headline": "Coffee habit",
            "daily_number": "$5/DAY",
            "yearly_number": "$1,200/YEAR",
            "price_text": "$1,200/YEAR",
            "hook_number": "$1,200/YEAR",
            "receipt_price_text": "$5.00",
            "store_name": "COFFEE HABIT",
            "subline": "before tips + snacks",
            "receipt_rows": [("workday coffee", "$5.00"), ("monthly total", "$100"), ("yearly total", "$1,200")],
            "visual_description": "clean bold finance hook card five dollars a day twelve hundred a year",
            "caption_text": "Tiny habits add up",
            "force_template_background": True,
        })
    elif is_cta:
        base.update({
            "template": "cta_callback",
            "eyebrow": "7-DAY CHALLENGE",
            "headline": "Skip 2 coffees/week",
            "visual_description": "savings challenge card coffee cup progress bar",
            "caption_text": "Skip two this week",
            "force_template_background": True,
        })
    elif idx == 1:
        base.update({
            "template": "money_shock_math",
            "label": "MONTHLY MATH",
            "number": "$100/MONTH",
            "monthly_number": "$100/MONTH",
            "formula": "$5 x 20 WORKDAYS",
            "subline": "every workday coffee run",
            "headline": "Workday coffee becomes a bill",
            "visual_description": "monthly coffee total calculator card",
            "caption_text": "That is $100/month",
            "force_template_background": True,
        })
    elif idx == 2:
        base.update({
            "template": "comparison_split",
            "comparison_title": "COFFEE SHOP vs HOME BREW",
            "shop_label": "COFFEE SHOP",
            "shop_number": "$100/mo",
            "home_label": "HOME BREW",
            "home_number": "$20/mo",
            "savings_number": "SAVE $80/mo",
            "subline": "same habit, cheaper route",
            "headline": "Same habit, cheaper route",
            "visual_description": "coffee shop versus home brew monthly cost comparison save eighty dollars",
            "caption_text": "Same habit. Cheaper route.",
            "force_template_background": True,
        })
    else:
        base.update({
            "template": "grocery_savings_payoff",
            "number": "$1,200/year",
            "payoff_number": "$1,200/year",
            "label": "12 MONTHS LATER",
            "subline": "gone before tips + snacks",
            "headline": "That small habit became a yearly number",
            "visual_description": "yearly savings reveal phone dashboard coffee receipt",
            "caption_text": "Almost $1,000 saved",
            "force_template_background": True,
        })
    return base


def _enrich_no_spend_explainer_scenes(scenes: list[Any], script_text: str) -> list[Any]:
    if not _is_coffee_savings_story(scenes, script_text):
        return scenes
    total = len(scenes or [])
    return [_enrich_coffee_savings_scene(scene, idx, total) for idx, scene in enumerate(scenes or [])]


def _scene_duration(scene: Any, fallback: float = 2.6) -> float:
    if isinstance(scene, dict) and scene.get("duration") is not None:
        try:
            return max(1.0, float(scene.get("duration")))
        except Exception:
            return fallback
    try:
        start = float(_scene_value(scene, "start", 0) or 0)
        end = float(_scene_value(scene, "end", 0) or 0)
        if end > start:
            return max(1.0, end - start)
    except Exception:
        pass
    return fallback


def _scene_template(scene: Any, idx: int) -> str:
    explicit = str(_scene_value(scene, "template", "") or _scene_value(scene, "hybrid_template", "") or "").strip()
    if explicit:
        return explicit
    method = str(_scene_value(scene, "method", "") or _scene_value(scene, "medium", "") or "").strip()
    if method in HYBRID_METHOD_TO_TEMPLATE:
        return HYBRID_METHOD_TO_TEMPLATE[method]
    part = str(_scene_value(scene, "part", "") or _scene_value(scene, "scene_type", "") or "").lower()
    if idx == 0 or part == "hook":
        return "hook_footage_overlay"
    if "prompt" in part or "ai" in part:
        return "ai_prompt_mock"
    if "comparison" in part or "split" in part:
        return "comparison_split"
    if "payoff" in part or "reveal" in part:
        return "payoff_number_reveal"
    if part == "cta":
        return "cta_callback"
    return "money_shock_math"


def _scene_query(scene: Any, template: str) -> str:
    text = " ".join(
        str(_scene_value(scene, key, "") or "")
        for key in ("visual_description", "description", "caption_text", "source_text", "subtitle")
    ).lower()
    if "coffee" in text:
        return "coffee cup cafe vertical"
    if "receipt" in text or "$" in text or "payment" in text:
        return "receipt payment coffee vertical"
    if template == "comparison_split":
        return "home coffee kitchen vertical"
    if template == "hook_footage_overlay":
        return "person holding coffee vertical"
    return "creator desk laptop vertical"


def _provider_available() -> bool:
    return bool(os.getenv("PEXELS_API_KEY") or os.getenv("PIXABAY_API_KEY"))


def _provider_config_status() -> dict[str, Any]:
    pexels = bool(os.getenv("PEXELS_API_KEY", "").strip())
    pixabay = bool(os.getenv("PIXABAY_API_KEY", "").strip())
    missing = []
    if not pexels:
        missing.append("PEXELS_API_KEY")
    if not pixabay:
        missing.append("PIXABAY_API_KEY")
    return {
        "provider_available": pexels or pixabay,
        "pexels_configured": pexels,
        "pixabay_configured": pixabay,
        "missing_config": missing,
    }


def _stock_cache_path(url: str, suffix: str = ".mp4") -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return CACHE_DIR / f"stock_{digest}{clean_suffix}"


def _fetch_pexels_candidates(query: str) -> list[dict[str, Any]]:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        return []
    try:
        with httpx.Client(timeout=12.0, follow_redirects=True) as client:
            res = client.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": key},
                params={"query": query, "per_page": 5, "orientation": "portrait"},
            )
            if res.status_code != 200:
                return []
            out = []
            for video in res.json().get("videos", [])[:5]:
                files = video.get("video_files") or []
                ranked = sorted(files, key=lambda f: (f.get("height", 0) < f.get("width", 0), -int(f.get("height", 0) or 0)))
                if ranked:
                    chosen = ranked[0]
                    out.append({
                        "provider": "pexels",
                        "media_type": "stock_footage",
                        "url": chosen.get("link"),
                        "width": chosen.get("width"),
                        "height": chosen.get("height"),
                        "duration": video.get("duration"),
                        "id": f"pexels:{video.get('id')}",
                    })
            return [c for c in out if c.get("url")]
    except Exception:
        return []


def _fetch_pixabay_candidates(query: str) -> list[dict[str, Any]]:
    key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not key:
        return []
    try:
        with httpx.Client(timeout=12.0, follow_redirects=True) as client:
            res = client.get(
                "https://pixabay.com/api/videos/",
                params={"key": key, "q": query, "per_page": 5, "video_type": "film"},
            )
            if res.status_code != 200:
                return []
            out = []
            for video in res.json().get("hits", [])[:5]:
                videos = video.get("videos") or {}
                chosen = videos.get("large") or videos.get("medium") or videos.get("small") or {}
                if chosen.get("url"):
                    out.append({
                        "provider": "pixabay",
                        "media_type": "stock_footage",
                        "url": chosen.get("url"),
                        "width": chosen.get("width"),
                        "height": chosen.get("height"),
                        "duration": video.get("duration"),
                        "id": f"pixabay:{video.get('id')}",
                    })
            return out
    except Exception:
        return []


def _fetch_pexels_image_candidates(query: str) -> list[dict[str, Any]]:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        return []
    try:
        with httpx.Client(timeout=12.0, follow_redirects=True) as client:
            res = client.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": key},
                params={"query": query, "per_page": 5, "orientation": "portrait"},
            )
            if res.status_code != 200:
                return []
            out = []
            for photo in res.json().get("photos", [])[:5]:
                src = photo.get("src") or {}
                url = src.get("portrait") or src.get("large2x") or src.get("large") or src.get("original")
                if url:
                    out.append({
                        "provider": "pexels",
                        "media_type": "stock_image",
                        "url": url,
                        "width": photo.get("width"),
                        "height": photo.get("height"),
                        "duration": 0,
                        "id": f"pexels_photo:{photo.get('id')}",
                    })
            return out
    except Exception:
        return []


def _fetch_pixabay_image_candidates(query: str) -> list[dict[str, Any]]:
    key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not key:
        return []
    try:
        with httpx.Client(timeout=12.0, follow_redirects=True) as client:
            res = client.get(
                "https://pixabay.com/api/",
                params={"key": key, "q": query, "per_page": 5, "image_type": "photo", "orientation": "vertical"},
            )
            if res.status_code != 200:
                return []
            out = []
            for photo in res.json().get("hits", [])[:5]:
                url = photo.get("largeImageURL") or photo.get("webformatURL")
                if url:
                    out.append({
                        "provider": "pixabay",
                        "media_type": "stock_image",
                        "url": url,
                        "width": photo.get("imageWidth") or photo.get("webformatWidth"),
                        "height": photo.get("imageHeight") or photo.get("webformatHeight"),
                        "duration": 0,
                        "id": f"pixabay_photo:{photo.get('id')}",
                    })
            return out
    except Exception:
        return []


def _score_stock_candidate(candidate: dict[str, Any], used_ids: set[str]) -> float:
    score = 0.0
    if candidate.get("id") in used_ids:
        score -= 1000.0
    width = int(candidate.get("width") or 0)
    height = int(candidate.get("height") or 0)
    duration = float(candidate.get("duration") or 0)
    if height >= width:
        score += 80
    score += min(height, 1920) / 50.0
    if candidate.get("media_type") == "stock_image":
        score += 10
    elif 2 <= duration <= 20:
        score += 20
    return score


def _download_stock_candidate(candidate: dict[str, Any], warnings: list[str]) -> Path | None:
    url = candidate.get("url")
    if not url:
        return None
    suffix = ".jpg" if candidate.get("media_type") == "stock_image" else ".mp4"
    out = _stock_cache_path(url, suffix=suffix)
    if out.exists() and out.stat().st_size > 1000:
        return out
    try:
        with httpx.Client(timeout=45.0, follow_redirects=True) as client:
            res = client.get(url)
            if res.status_code != 200:
                warnings.append(f"stock_download_failed:{candidate.get('provider')}:HTTP_{res.status_code}")
                return None
            out.write_bytes(res.content)
            return out if out.stat().st_size > 1000 else None
    except Exception as exc:
        warnings.append(f"stock_download_failed:{candidate.get('provider')}:{str(exc)[:80]}")
        return None


def _stock_candidates_for_query(query: str, media_type: str) -> list[dict[str, Any]]:
    if media_type == "stock_image":
        return _fetch_pexels_image_candidates(query) + _fetch_pixabay_image_candidates(query)
    return _fetch_pexels_candidates(query) + _fetch_pixabay_candidates(query)


def _select_stock_asset(
    query_candidates: list[str],
    media_order: list[str],
    used_ids: set[str],
    warnings: list[str],
) -> tuple[Path | None, dict[str, Any]]:
    provider_status = _provider_config_status()
    queries = [str(query).strip() for query in query_candidates if str(query).strip()]
    queries_attempted = queries[:]
    if not provider_status["provider_available"]:
        return None, {
            **provider_status,
            "queries_attempted": queries_attempted,
            "query_used": None,
            "candidates": 0,
            "reason": "stock_provider_keys_not_configured",
        }

    total_candidates = 0
    for media_type in media_order:
        if media_type not in {"stock_footage", "stock_image"}:
            continue
        for query in queries:
            candidates = _stock_candidates_for_query(query, media_type)
            total_candidates += len(candidates)
            ranked = sorted(candidates, key=lambda c: _score_stock_candidate(c, used_ids), reverse=True)
            for candidate in ranked[:5]:
                path = _download_stock_candidate(candidate, warnings)
                if path:
                    used_ids.add(str(candidate.get("id")))
                    return path, {
                        **provider_status,
                        "queries_attempted": queries_attempted,
                        "query_used": query,
                        "candidates": total_candidates,
                        "chosen": candidate,
                        "reason": "resolved",
                    }
    return None, {
        **provider_status,
        "queries_attempted": queries_attempted,
        "query_used": None,
        "candidates": total_candidates,
        "reason": "no_stock_asset_resolved",
    }


def _select_stock_background(scene: Any, template: str, used_ids: set[str], warnings: list[str]) -> tuple[Path | None, dict[str, Any]]:
    return _select_stock_asset([_scene_query(scene, template)], ["stock_footage"], used_ids, warnings)


def _local_asset_domain(asset_strategy: dict[str, Any]) -> str:
    explicit = str(
        asset_strategy.get("local_asset_domain")
        or asset_strategy.get("domain")
        or asset_strategy.get("topic")
        or ""
    ).strip()
    if explicit:
        return explicit
    text = " ".join(
        str(part or "")
        for part in [
            asset_strategy.get("reason"),
            asset_strategy.get("template_hint"),
            asset_strategy.get("asset_role"),
            " ".join(str(query) for query in (asset_strategy.get("query_candidates") or [])),
        ]
    )
    return detect_hmr_asset_domain_from_text(text)


def _local_asset_roots(asset_strategy: dict[str, Any]) -> list[Path]:
    roots = [LOCAL_HMR_ASSET_DIR / folder for folder in local_asset_domain_folders(_local_asset_domain(asset_strategy))]
    roots.append(LOCAL_HMR_ASSET_DIR)
    deduped: list[Path] = []
    for root in roots:
        if root not in deduped:
            deduped.append(root)
    return deduped


def _local_asset_names(scene_id: Any, asset_strategy: dict[str, Any]) -> list[str]:
    scene_key = str(scene_id or "").lower().strip()
    role = str(asset_strategy.get("asset_role") or "").lower().strip()
    names = [scene_key]
    if "hook" in scene_key or "hook" in role:
        names.extend(["hook", "grocery_hook", "receipt_hook"])
    if "reveal" in scene_key or "context" in role:
        names.extend(["reveal", "context", "grocery_reveal", "receipt_reveal"])
    if "payoff" in scene_key or "result" in role:
        names.extend(["payoff", "result"])
    if "cta" in scene_key or "comment" in role:
        names.append("cta")
    return [name for idx, name in enumerate(names) if name and name not in names[:idx]]


def _local_asset_candidate_paths(scene_id: Any, asset_strategy: dict[str, Any]) -> list[Path]:
    roots = _local_asset_roots(asset_strategy)
    names = _local_asset_names(scene_id, asset_strategy)
    out: list[Path] = []
    for root in roots:
        for name in names:
            for ext in [*VIDEO_EXTENSIONS, *IMAGE_EXTENSIONS]:
                out.append(root / f"{name}{ext}")
            out.extend(sorted((root / name).glob("*")) if (root / name).exists() else [])
    return out


def _local_asset_candidates(scene_id: Any, asset_strategy: dict[str, Any]) -> list[Path]:
    return [path for path in _local_asset_candidate_paths(scene_id, asset_strategy) if path.exists() and path.is_file()]


def _display_local_asset_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _resolve_local_asset(scene_id: Any, asset_strategy: dict[str, Any]) -> tuple[Path | None, dict[str, Any]]:
    candidates = _local_asset_candidates(scene_id, asset_strategy)
    for path in candidates:
        suffix = path.suffix.lower()
        if suffix in VIDEO_EXTENSIONS:
            asset_type = "stock_footage"
        elif suffix in IMAGE_EXTENSIONS:
            asset_type = "stock_image"
        else:
            continue
        return path, {
            "resolved_asset_type": asset_type,
            "resolved_asset_path": str(path),
            "resolved_asset_provider": "local_asset",
            "asset_resolution_status": "resolved",
            "fallback_used": False,
            "query_used": None,
            "queries_attempted": [],
            "provider_available": True,
            "missing_config": [],
        }
    return None, {
        "resolved_asset_type": None,
        "resolved_asset_path": None,
        "resolved_asset_provider": None,
        "asset_resolution_status": "local_asset_missing",
        "fallback_used": True,
        "query_used": None,
        "queries_attempted": [],
        "provider_available": False,
        "missing_config": [
            "Add local HMR assets such as "
            + " or ".join(
                _display_local_asset_path(path) for path in _local_asset_candidate_paths(scene_id, asset_strategy)[:4]
            ),
        ],
    }


def _visual_realism_human_gate(asset_strategy: list[dict[str, Any]], scene_reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not asset_strategy:
        return {
            "visual_realism_score": "pending_human_review",
            "object_credibility": "pending_human_review",
            "scene_asset_strategy_used": False,
            "planned_real_sources": 0,
            "resolved_real_assets": 0,
            "drawn_placeholder_risk": "unknown",
            "post_no_post_recommendation": "pending_human_review",
        }
    planned_real_sources = sum(
        1
        for row in asset_strategy
        if row.get("visual_medium") in {"stock_footage", "stock_image", "playwright_capture", "local_asset"}
    )
    motion_only = sum(1 for row in asset_strategy if row.get("visual_medium") == "motion_template")
    resolved_real_sources = sum(
        1
        for row in scene_reports
        if row.get("resolved_asset_type") in {"playwright_capture", "stock_image", "stock_footage", "local_asset"}
    )
    if resolved_real_sources < planned_real_sources:
        risk = "high_until_asset_resolution"
    elif motion_only >= max(2, len(asset_strategy) // 2):
        risk = "high"
    elif motion_only:
        risk = "medium"
    else:
        risk = "low"
    return {
        "visual_realism_score": "pending_human_review",
        "object_credibility": "pending_human_review",
        "scene_asset_strategy_used": planned_real_sources > 0,
        "planned_real_sources": planned_real_sources,
        "resolved_real_assets": resolved_real_sources,
        "drawn_placeholder_risk": risk,
        "post_no_post_recommendation": "pending_human_review",
    }


def _fit_background_frame(frame: np.ndarray, width: int, height: int, progress: float) -> np.ndarray:
    fh, fw = frame.shape[:2]
    scale = max(width / max(1, fw), height / max(1, fh)) * (1.0 + 0.025 * math.sin(progress * math.pi))
    resized = cv2.resize(frame, (int(fw * scale), int(fh * scale)), interpolation=cv2.INTER_LINEAR)
    y = max(0, (resized.shape[0] - height) // 2)
    x = max(0, (resized.shape[1] - width) // 2)
    cropped = resized[y:y + height, x:x + width]
    if cropped.shape[0] != height or cropped.shape[1] != width:
        cropped = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)
    return cropped


def _zoom_canvas(canvas: np.ndarray, scale: float) -> np.ndarray:
    if scale <= 1.001:
        return canvas
    h, w = canvas.shape[:2]
    crop_w = max(1, int(w / scale))
    crop_h = max(1, int(h / scale))
    x = max(0, (w - crop_w) // 2)
    y = max(0, (h - crop_h) // 2)
    cropped = canvas[y:y + crop_h, x:x + crop_w]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)


def _scene_quick_cuts(editing_rhythm_plan: dict[str, Any], scene_id: str, scene_start: float, scene_end: float) -> list[dict[str, Any]]:
    cuts = [
        cut
        for cut in editing_rhythm_plan.get("cut_schedule", []) or []
        if str(cut.get("scene_id")) == str(scene_id)
    ]
    return cuts or [{"scene_id": scene_id, "start": scene_start, "end": scene_end, "cue": "scene_hold", "transition": "hard_cut"}]


def _active_quick_cut(cuts: list[dict[str, Any]], timestamp: float) -> dict[str, Any]:
    for cut in cuts:
        start = float(cut.get("start", 0.0) or 0.0)
        end = float(cut.get("end", start) or start)
        if start <= timestamp < end or abs(timestamp - end) < 0.001:
            return cut
    return cuts[-1] if cuts else {"start": timestamp, "end": timestamp, "cue": "scene_hold"}


def _transition_for_quick_cut(cut: dict[str, Any]) -> str:
    return "zoom_blend" if cut.get("cue") == "payoff_hit" else "hard_cut"


def _read_bg_frame(capture: cv2.VideoCapture | None, width: int, height: int, progress: float) -> np.ndarray | None:
    if capture is None:
        return None
    ok, frame = capture.read()
    if not ok:
        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = capture.read()
    if not ok:
        return None
    return _fit_background_frame(frame, width, height, progress)


def _make_silent_audio(path: Path, duration: float) -> str | None:
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", f"{duration:.3f}", str(path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        return str(path)
    except Exception:
        return None


def _probe_media_duration(path: str | Path | None) -> float | None:
    if not path:
        return None
    media_path = Path(path)
    if not media_path.exists():
        return None
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(media_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        duration = float((proc.stdout or "").strip())
        return duration if duration > 0 else None
    except Exception:
        return None


def _mux_audio(video_path: Path, audio_path: str | None, duration: float, warnings: list[str]) -> None:
    audio = audio_path if audio_path and Path(audio_path).exists() else None
    if audio is None:
        silent = video_path.with_suffix(".silent.wav")
        audio = _make_silent_audio(silent, duration)
        if audio is None:
            warnings.append("audio_mux_skipped:no_audio_and_silent_generation_failed")
            return
        warnings.append("rendered_with_silent_audio")
    muxed = video_path.with_name(video_path.stem + "_muxed.mp4")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-i", audio, "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(muxed)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
        muxed.replace(video_path)
    except Exception as exc:
        warnings.append(f"audio_mux_failed:{str(exc)[:90]}")


def render_hybrid_video(
    scenes: list[Any],
    script_text: str,
    output_path: str | Path,
    audio_path: str | None = None,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
    use_stock_backgrounds: bool = True,
    use_free_tts: bool = True,
    style_preset: str = "documentary_money_short",
    proof_assets: list[dict[str, Any]] | None = None,
    scene_locks: list[dict[str, Any]] | None = None,
    scene_overrides: list[dict[str, Any]] | None = None,
    agency_preset_id: str | None = None,
    music_bed_path: str | Path | None = None,
    execute_audio_mix: bool = False,
) -> dict[str, Any]:
    start_time = time.time()
    profile_start = time.perf_counter()
    scenes, scene_iteration_report = apply_scene_locks_and_overrides(
        scenes,
        scene_locks=scene_locks,
        scene_overrides=scene_overrides,
    )
    scenes = _enrich_no_spend_explainer_scenes(scenes, script_text)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    scene_reports: list[dict[str, Any]] = []
    profile_scene_reports: list[dict[str, Any]] = []
    profile_template_totals: dict[str, dict[str, Any]] = {}
    used_stock_ids: set[str] = set()
    media_mix: dict[str, int] = {}
    stock_status = {
        "provider_available": _provider_available(),
        "used": False,
        "reason": "",
        "provider_config": _provider_config_status(),
    }
    scene_asset_strategy = plan_hmr_scene_assets(scenes)
    strategy_by_scene_id = {str(row.get("scene_id")): row for row in scene_asset_strategy}
    agency_template = select_agency_template_for_scenes(scenes, script_text)
    agency_preset = select_agency_preset_for_scenes(
        scenes,
        script_text,
        agency_template=agency_template,
        preset_id=agency_preset_id,
    )
    proof_asset_plan = build_proof_asset_plan(scenes, proof_assets)
    for row in scene_iteration_report.get("rejected_overrides", []):
        warnings.append(f"scene_override_rejected:{row.get('scene_id')}")
    for row in scene_iteration_report.get("missing_override_targets", []):
        warnings.append(f"scene_override_target_missing:{row.get('scene_id')}")
    for row in proof_asset_plan.get("missing_assets", []):
        proof_asset = row.get("proof_asset") or {}
        warnings.append(f"proof_asset_missing:{row.get('scene_id')}:{proof_asset.get('candidate_path')}")
    for row in proof_asset_plan.get("unresolved_targets", []):
        warnings.append(f"proof_asset_target_missing:{row.get('scene_id') or row.get('scene_role')}")

    prepared = []
    asset_lookup_sec = 0.0
    for idx, scene in enumerate(scenes):
        template_name = _scene_template(scene, idx)
        duration = _scene_duration(scene, 2.6)
        bg_path = None
        stock_meta: dict[str, Any] = {}
        asset_resolution: dict[str, Any] = {
            "resolved_asset_type": None,
            "resolved_asset_path": None,
            "resolved_asset_provider": None,
            "asset_resolution_status": "not_attempted",
            "fallback_used": True,
            "query_used": None,
            "queries_attempted": [],
            "provider_available": None,
            "missing_config": [],
        }
        scene_id = _scene_value(scene, "id", None) or _scene_value(scene, "scene_id", None) or _scene_value(scene, "scene", None) or _scene_value(scene, "scene_index", idx + 1)
        asset_strategy = strategy_by_scene_id.get(str(scene_id), {})
        lookup_start = time.perf_counter()
        proof_row = proof_asset_for_scene(proof_asset_plan, scene_id)
        if proof_row:
            proof_asset = proof_row.get("proof_asset") or {}
            bg_path = Path(str(proof_asset.get("resolved_path")))
            asset_resolution = proof_asset_resolution_fields(proof_row)
            stock_meta = {
                "provider": "user_proof_asset",
                "reason": "proof_asset_override",
                "proof_asset": proof_asset,
            }
        elif asset_strategy.get("visual_medium") == "playwright_capture":
            asset_resolution = resolve_playwright_scene_asset(
                scene if isinstance(scene, dict) else {},
                asset_strategy,
                CACHE_DIR / "captures",
                width,
                height,
            )
            if asset_resolution.get("fallback_used"):
                warnings.append(f"asset_resolution_fallback:{scene_id}:{asset_resolution.get('asset_resolution_status')}")
        elif asset_strategy.get("visual_medium") in {"stock_footage", "stock_image"}:
            bg_path, asset_resolution = resolve_stock_or_local_scene_asset(
                scene_id,
                asset_strategy,
                used_stock_ids,
                warnings,
                use_stock_backgrounds,
                stock_selector=_select_stock_asset,
                local_resolver=_resolve_local_asset,
                provider_status_getter=_provider_config_status,
            )
            stock_meta = {
                "provider_available": asset_resolution.get("provider_available"),
                "queries_attempted": asset_resolution.get("queries_attempted") or [],
                "query_used": asset_resolution.get("query_used"),
                "reason": asset_resolution.get("asset_resolution_status"),
                "missing_config": asset_resolution.get("missing_config") or [],
            }
            if bg_path and asset_resolution.get("resolved_asset_provider") != "local_asset":
                stock_status["used"] = True
            elif not stock_status["reason"]:
                stock_status["reason"] = asset_resolution.get("asset_resolution_status") or "asset_unresolved_for_scene"
            if asset_resolution.get("fallback_used"):
                warnings.append(f"asset_resolution_fallback:{scene_id}:{asset_resolution.get('asset_resolution_status')}")
        asset_lookup_sec += time.perf_counter() - lookup_start
        spec = build_resolved_scene_spec(
            scene_id=scene_id,
            template=template_name,
            duration=duration,
            scene=scene if isinstance(scene, dict) else {},
            asset_strategy=asset_strategy,
            asset_resolution=asset_resolution,
            bg_path=bg_path,
            stock_meta=stock_meta,
        )
        prepared.append((scene, template_name, duration, bg_path, stock_meta, asset_resolution, spec))

    source_total_duration = sum(item[2] for item in prepared)
    probe_start = time.perf_counter()
    audio_duration = _probe_media_duration(audio_path)
    audio_probe_sec = time.perf_counter() - probe_start
    duration_strategy = "scene_durations"
    if audio_duration and source_total_duration > 0 and abs(audio_duration - source_total_duration) > 0.35:
        if audio_duration > source_total_duration and len(prepared) > 1:
            first = prepared[0]
            first_duration = first[2]
            remaining_source_duration = max(0.1, source_total_duration - first_duration)
            remaining_target_duration = max(0.1, audio_duration - first_duration)
            scale = remaining_target_duration / remaining_source_duration
            prepared = [
                first,
                *[
                    (
                        scene,
                        template_name,
                        duration * scale,
                        bg_path,
                        stock_meta,
                        asset_resolution,
                        build_resolved_scene_spec(
                            scene_id=spec.scene_id,
                            template=template_name,
                            duration=duration * scale,
                            scene=scene if isinstance(scene, dict) else {},
                            asset_strategy=spec.asset_strategy,
                            asset_resolution=asset_resolution,
                            bg_path=bg_path,
                            stock_meta=stock_meta,
                        ),
                    )
                    for scene, template_name, duration, bg_path, stock_meta, asset_resolution, spec in prepared[1:]
                ],
            ]
            duration_strategy = "scaled_to_audio_duration_preserve_hook"
        else:
            scale = audio_duration / source_total_duration
            prepared = [
                (
                    scene,
                    template_name,
                    duration * scale,
                    bg_path,
                    stock_meta,
                    asset_resolution,
                    build_resolved_scene_spec(
                        scene_id=spec.scene_id,
                        template=template_name,
                        duration=duration * scale,
                        scene=scene if isinstance(scene, dict) else {},
                        asset_strategy=spec.asset_strategy,
                        asset_resolution=asset_resolution,
                        bg_path=bg_path,
                        stock_meta=stock_meta,
                    ),
                )
                for scene, template_name, duration, bg_path, stock_meta, asset_resolution, spec in prepared
            ]
            duration_strategy = "scaled_to_audio_duration"
    total_duration = sum(item[2] for item in prepared)
    scene_timings = []
    timing_cursor = 0.0
    for idx, (scene, _template_name, duration, _bg_path, _stock_meta, _asset_resolution, _spec) in enumerate(prepared):
        scene_id = _scene_value(scene, "id", None) or _scene_value(scene, "scene_id", None) or _scene_value(scene, "scene", None) or _scene_value(scene, "scene_index", idx + 1)
        scene_timings.append({
            "scene_id": str(scene_id),
            "start": round(timing_cursor, 3),
            "end": round(timing_cursor + duration, 3),
            "duration": round(duration, 3),
        })
        timing_cursor += duration
    sfx_plan = build_sfx_plan([item[0] for item in prepared], scene_timings=scene_timings)
    for role in sfx_plan.get("missing_roles", []):
        warnings.append(f"sfx_missing:{role}")
    sfx_by_scene_id: dict[str, list[dict[str, Any]]] = {}
    for cue in sfx_plan.get("cues", []):
        sfx_by_scene_id.setdefault(str(cue.get("scene_id")), []).append(cue)
    caption_style_profile = get_caption_style_profile("modern_bounce")
    caption_events = split_caption_events(script_text, total_duration, max_words=caption_style_profile.max_words_per_chunk)
    caption_style_plan = build_caption_style_plan(
        caption_events=caption_events,
        profile_id=caption_style_profile.id,
    )
    editing_rhythm_plan = build_quick_cut_schedule(
        script_text=script_text,
        scene_timings=scene_timings,
        caption_events=caption_events,
        profile_id="quick_cut_shorts",
    )
    audio_binding_timeline = build_audio_binding_timeline(
        script_text=script_text,
        scene_timings=scene_timings,
        caption_events=caption_events,
        sfx_plan=sfx_plan,
        editing_rhythm_plan=editing_rhythm_plan,
        voice_audio_path=audio_path,
        music_bed_path=music_bed_path,
        music_enabled=music_bed_path is not None,
    )

    writer_open_start = time.perf_counter()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output), fourcc, float(fps), (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Unable to open VideoWriter for {output}")
    writer_open_sec = time.perf_counter() - writer_open_start

    global_frame = 0
    elapsed = 0.0
    total_bg_read_sec = 0.0
    total_template_sec = 0.0
    total_caption_sec = 0.0
    total_writer_write_sec = 0.0
    executed_montage_transition_types: set[str] = set()
    executed_montage_clip_count = 0
    scene_montage_execution: dict[str, dict[str, Any]] = {}
    for scene_idx, (scene, template_name, duration, bg_path, stock_meta, asset_resolution, spec) in enumerate(prepared):
        scene_profile_start = time.perf_counter()
        template = get_template(template_name)
        force_template_background = bool(_scene_value(scene, "force_template_background", False))
        if force_template_background:
            bg_path = None
        frame_count = max(1, int(round(duration * fps)))
        scene_id = _scene_value(scene, "id", None) or _scene_value(scene, "scene", None) or _scene_value(scene, "scene_index", scene_idx + 1)
        scene_start_time = elapsed
        scene_end_time = elapsed + duration
        quick_cuts = _scene_quick_cuts(editing_rhythm_plan, str(scene_id), scene_start_time, scene_end_time)
        scene_executed_clip_ids: set[str] = set()
        asset_fields = spec.resolved_asset.to_report_fields()
        resolved_type = str(asset_fields.get("resolved_asset_type") or "")
        bg_suffix = bg_path.suffix.lower() if bg_path else ""
        image_background = None
        if bg_path and (resolved_type == "stock_image" or bg_suffix in IMAGE_EXTENSIONS):
            raw_image = cv2.imread(str(bg_path))
            if raw_image is not None:
                image_background = _fit_background_frame(raw_image, width, height, 0.0)
        capture = cv2.VideoCapture(str(bg_path)) if bg_path and image_background is None else None
        media_class = "REAL_STOCK" if bg_path else "ANIMATED_FALLBACK"
        if asset_fields.get("resolved_asset_type") == "playwright_capture":
            media_class = "LOCAL_CAPTURE"
        elif bg_path:
            media_class = "REAL_STOCK"
        elif template_name == "ai_prompt_mock":
            media_class = "LOCAL_CAPTURE"
        elif template_name == "cta_callback":
            media_class = "ANIMATED_FALLBACK"
        elif template_name == "comparison_split":
            media_class = "MOTION_SCENE"
        elif template_name in {"money_shock_math", "payoff_number_reveal", "grocery_receipt_hook", "grocery_reveal_scene", "grocery_ai_comparison", "grocery_savings_payoff"}:
            media_class = "MOTION_CARD"
        media_mix[media_class] = media_mix.get(media_class, 0) + 1

        scene_caption_reports = []
        text_cropped = False
        key_boxes: list[tuple[int, int, int, int]] = []
        motion_scores = []
        postability_signals: dict[str, Any] = {}
        template_cache: dict[str, Any] = {}
        scene_bg_read_sec = 0.0
        scene_template_sec = 0.0
        scene_caption_sec = 0.0
        scene_writer_write_sec = 0.0
        for local_frame in range(frame_count):
            current_t = elapsed + local_frame / float(fps)
            active_cut = _active_quick_cut(quick_cuts, current_t)
            cut_start = float(active_cut.get("start", scene_start_time) or scene_start_time)
            cut_end = float(active_cut.get("end", scene_end_time) or scene_end_time)
            cut_duration = max(0.001, cut_end - cut_start)
            cut_local = max(0.0, min(cut_duration, current_t - cut_start))
            progress = cut_local / max(0.001, cut_duration)
            cut_transition = _transition_for_quick_cut(active_cut)
            executed_montage_transition_types.add(cut_transition)
            scene_executed_clip_ids.add(f"{scene_id}:{round(cut_start, 3)}")
            bg_start = time.perf_counter()
            if image_background is not None:
                canvas = image_background.copy()
            else:
                canvas = _read_bg_frame(capture, width, height, progress)
            if canvas is None:
                canvas = np.zeros((height, width, 3), dtype=np.uint8)
            bg_elapsed = time.perf_counter() - bg_start
            scene_bg_read_sec += bg_elapsed
            total_bg_read_sec += bg_elapsed
            scene_config = {
                **(scene if isinstance(scene, dict) else {}),
                "has_real_background": bg_path is not None and not bool(_scene_value(scene, "force_template_background", False)),
                "style_preset": style_preset,
                **{
                    key: value
                    for key, value in asset_fields.items()
                    if key.startswith("resolved_asset_")
                    or key in {
                        "asset_resolution_status",
                        "fallback_used",
                        "query_used",
                        "queries_attempted",
                        "provider_available",
                        "missing_config",
                        "playwright_motion_mode",
                        "capture_steps",
                        "visible_interaction",
                        "saved_chrome_profile_used",
                    }
                },
                "_template_cache": template_cache,
            }
            template_start = time.perf_counter()
            template_report = template(local_frame, progress, canvas, scene_config)
            template_elapsed = time.perf_counter() - template_start
            scene_template_sec += template_elapsed
            total_template_sec += template_elapsed
            text_cropped = text_cropped or bool(template_report.get("cropped"))
            key_boxes = [tuple(b) for b in template_report.get("key_number_boxes", [])]
            motion_scores.append(float(template_report.get("motion_score") or 0.5))
            for key, value in (template_report.get("postability_signals") or {}).items():
                if key not in postability_signals:
                    postability_signals[key] = value

            if force_template_background:
                active_caption_event = {
                    "start": scene_start_time,
                    "end": scene_end_time,
                    "text": str(_scene_value(scene, "caption_text", "") or ""),
                }
            else:
                active_caption_event = next((ev for ev in caption_events if ev["start"] <= current_t < ev["end"]), None)
            active_caption = active_caption_event["text"] if active_caption_event else ""
            caption_start = time.perf_counter()
            animation = (
                caption_animation_state(
                    event_start=active_caption_event["start"],
                    event_end=active_caption_event["end"],
                    current_time=current_t,
                    profile=caption_style_profile,
                )
                if active_caption_event
                else None
            )
            cap_report = draw_caption_band(
                canvas,
                active_caption,
                reserved_boxes=key_boxes,
                caption_style=caption_style_profile.to_dict(),
                animation_state=animation,
            )
            if cut_transition == "zoom_blend":
                pulse = max(0.0, 1.0 - min(1.0, cut_local / 0.22))
                if pulse > 0:
                    canvas[:] = _zoom_canvas(canvas, 1.0 + 0.085 * pulse)
            caption_elapsed = time.perf_counter() - caption_start
            scene_caption_sec += caption_elapsed
            total_caption_sec += caption_elapsed
            if local_frame == 0 and cap_report.get("caption"):
                scene_caption_reports.append(cap_report)
            writer_start = time.perf_counter()
            writer.write(canvas)
            writer_elapsed = time.perf_counter() - writer_start
            scene_writer_write_sec += writer_elapsed
            total_writer_write_sec += writer_elapsed
            global_frame += 1

        if capture is not None:
            capture.release()
        executed_montage_clip_count += len(scene_executed_clip_ids)
        scene_montage_execution[str(scene_id)] = {
            "executed_clip_count": len(scene_executed_clip_ids),
            "executed_transition_types": sorted(executed_montage_transition_types),
            "quick_cut_boundaries_consumed": [
                {
                    "start": round(float(cut.get("start", scene_start_time) or scene_start_time), 3),
                    "end": round(float(cut.get("end", scene_end_time) or scene_end_time), 3),
                    "transition": _transition_for_quick_cut(cut),
                    "cue": cut.get("cue"),
                }
                for cut in quick_cuts
            ],
        }
        scene_total_sec = time.perf_counter() - scene_profile_start
        profile_scene_reports.append({
            "scene_id": _scene_value(scene, "id", None) or _scene_value(scene, "scene", None) or _scene_value(scene, "scene_index", scene_idx + 1),
            "template": template_name,
            "frame_count": frame_count,
            "total_sec": round(scene_total_sec, 4),
            "asset_loading_resizing_sec": round(scene_bg_read_sec, 4),
            "template_composition_sec": round(scene_template_sec, 4),
            "caption_composition_sec": round(scene_caption_sec, 4),
            "writer_write_sec": round(scene_writer_write_sec, 4),
            "sec_per_frame": round(scene_total_sec / max(1, frame_count), 5),
        })
        template_profile = profile_template_totals.setdefault(
            template_name,
            {
                "template": template_name,
                "scene_count": 0,
                "frame_count": 0,
                "total_sec": 0.0,
                "asset_loading_resizing_sec": 0.0,
                "template_composition_sec": 0.0,
                "caption_composition_sec": 0.0,
                "writer_write_sec": 0.0,
            },
        )
        template_profile["scene_count"] += 1
        template_profile["frame_count"] += frame_count
        template_profile["total_sec"] += scene_total_sec
        template_profile["asset_loading_resizing_sec"] += scene_bg_read_sec
        template_profile["template_composition_sec"] += scene_template_sec
        template_profile["caption_composition_sec"] += scene_caption_sec
        template_profile["writer_write_sec"] += scene_writer_write_sec
        scene_id = _scene_value(scene, "id", None) or _scene_value(scene, "scene", None) or _scene_value(scene, "scene_index", scene_idx + 1)
        asset_strategy = strategy_by_scene_id.get(str(scene_id), {})
        scene_reports.append({
            "scene_id": scene_id,
            "template": template_name,
            "duration": round(duration, 3),
            "media_classification": media_class,
            "scene_asset_strategy": asset_strategy,
            "resolved_asset_type": asset_fields.get("resolved_asset_type"),
            "resolved_asset_path": asset_fields.get("resolved_asset_path"),
            "resolved_asset_paths": asset_fields.get("resolved_asset_paths") or [],
            "resolved_asset_provider": asset_fields.get("resolved_asset_provider"),
            "asset_resolution_status": asset_fields.get("asset_resolution_status"),
            "fallback_used": asset_fields.get("fallback_used"),
            "playwright_motion_mode": asset_fields.get("playwright_motion_mode"),
            "capture_steps": asset_fields.get("capture_steps") or [],
            "visible_interaction": asset_fields.get("visible_interaction"),
            "saved_chrome_profile_used": asset_fields.get("saved_chrome_profile_used"),
            "query_used": asset_fields.get("query_used"),
            "queries_attempted": asset_fields.get("queries_attempted") or [],
            "provider_available": asset_fields.get("provider_available"),
            "missing_config": asset_fields.get("missing_config") or [],
            "provider_usage": (
                stock_meta
                if bg_path
                else {
                    "provider": asset_fields.get("resolved_asset_provider"),
                    "reason": asset_fields.get("asset_resolution_status") or stock_status.get("reason") or "animated_or_motion_template",
                }
            ),
            "background_id": str(bg_path) if bg_path else f"{media_class}:{template_name}",
            "caption_report": scene_caption_reports[0] if scene_caption_reports else {"caption": "", "word_count": 0},
            "text_cropped": text_cropped,
            "motion_score": round(sum(motion_scores) / max(1, len(motion_scores)), 3),
            "number_reveal": template_name in {"payoff_number_reveal", "grocery_savings_payoff", "money_shock_math", "grocery_receipt_hook"},
            "postability_signals": postability_signals,
            "montage_execution": scene_montage_execution.get(str(scene_id), {}),
            "sfx_cues": sfx_by_scene_id.get(str(scene_id), []),
            "proof_asset": (spec.resolved_asset.metadata or {}).get("proof_asset"),
            "proof_asset_used": asset_fields.get("resolved_asset_provider") == "user_proof_asset",
        })
        elapsed += duration

    writer_release_start = time.perf_counter()
    writer.release()
    writer_release_sec = time.perf_counter() - writer_release_start
    mux_audio_sec = 0.0
    audio_mix_execution = execute_audio_mix_plan(
        voice_audio_path=audio_path,
        output_audio_path=output.with_name(output.stem + "_audio_bound.m4a"),
        audio_timeline=audio_binding_timeline,
        enabled=execute_audio_mix,
    )
    audio_for_mux = audio_mix_execution.get("mixed_audio_path") or audio_path
    if audio_for_mux or use_free_tts:
        mux_start = time.perf_counter()
        _mux_audio(output, audio_for_mux, total_duration, warnings)
        mux_audio_sec = time.perf_counter() - mux_start
    final_probe_start = time.perf_counter()
    final_video_duration = _probe_media_duration(output)
    final_probe_sec = time.perf_counter() - final_probe_start
    sync_target_duration = audio_duration or total_duration
    sync_delta = abs((final_video_duration or total_duration) - sync_target_duration) if sync_target_duration else None
    template_totals = []
    for row in profile_template_totals.values():
        frame_count = int(row["frame_count"] or 0)
        out = {
            "template": row["template"],
            "scene_count": row["scene_count"],
            "frame_count": frame_count,
            "total_sec": round(float(row["total_sec"]), 4),
            "asset_loading_resizing_sec": round(float(row["asset_loading_resizing_sec"]), 4),
            "template_composition_sec": round(float(row["template_composition_sec"]), 4),
            "caption_composition_sec": round(float(row["caption_composition_sec"]), 4),
            "writer_write_sec": round(float(row["writer_write_sec"]), 4),
            "sec_per_frame": round(float(row["total_sec"]) / max(1, frame_count), 5),
        }
        template_totals.append(out)
    total_profile_sec = time.perf_counter() - profile_start

    report = {
        "video_path": str(output),
        "duration": round(total_duration, 3),
        "audio_sync_report": {
            "audio_path": str(audio_path) if audio_path else None,
            "source_audio_duration_sec": round(audio_duration, 3) if audio_duration else None,
            "source_scene_duration_sec": round(source_total_duration, 3),
            "planned_video_duration_sec": round(total_duration, 3),
            "final_video_duration_sec": round(final_video_duration, 3) if final_video_duration else None,
            "duration_delta_sec": round(sync_delta, 3) if sync_delta is not None else None,
            "duration_strategy": duration_strategy,
        },
        "scene_reports": scene_reports,
        "agency_template": agency_template,
        "agency_preset": agency_preset,
        "scene_iteration": scene_iteration_report,
        "proof_asset_plan": proof_asset_plan,
        "sfx_plan": sfx_plan,
        "audio_mix_execution": audio_mix_execution,
        "audio_mix_execution_status": audio_mix_execution["audio_mix_execution_status"],
        "mixed_event_count": audio_mix_execution["mixed_event_count"],
        "skipped_event_count": audio_mix_execution["skipped_event_count"],
        "local_assets_only": audio_mix_execution["local_assets_only"],
        "scene_asset_strategy": scene_asset_strategy,
        "visual_realism_human_gate": _visual_realism_human_gate(scene_asset_strategy, scene_reports),
        "render_profile": {
            "total_wall_sec": round(total_profile_sec, 4),
            "frame_count": global_frame,
            "fps": fps,
            "width": width,
            "height": height,
            "asset_lookup_sec": round(asset_lookup_sec, 4),
            "audio_probe_sec": round(audio_probe_sec, 4),
            "final_video_probe_sec": round(final_probe_sec, 4),
            "writer_open_sec": round(writer_open_sec, 4),
            "writer_write_sec": round(total_writer_write_sec, 4),
            "writer_release_sec": round(writer_release_sec, 4),
            "mux_audio_sec": round(mux_audio_sec, 4),
            "asset_loading_resizing_sec": round(total_bg_read_sec, 4),
            "frame_template_composition_sec": round(total_template_sec, 4),
            "caption_composition_sec": round(total_caption_sec, 4),
            "per_scene": profile_scene_reports,
            "per_template": sorted(template_totals, key=lambda row: row["total_sec"], reverse=True),
        },
        "media_mix": media_mix,
        "warnings": warnings,
        "render_time_sec": round(time.time() - start_time, 3),
        "caption_events": caption_events,
        "caption_report": {
            "max_words": caption_style_profile.max_words_per_chunk,
            "event_count": len(caption_events),
            "violations": [
                ev
                for ev in caption_events
                if len(str(ev.get("text", "")).split()) > caption_style_profile.max_words_per_chunk
            ],
        },
        "stock_status": stock_status,
    }
    report = attach_quick_cut_schedule_to_report(report, schedule=editing_rhythm_plan)
    report = attach_audio_timeline_to_report(report, audio_binding_timeline)
    report = attach_caption_style_to_report(report, caption_style_plan)
    montage_plan = build_montage_plan(
        scene_reports=scene_reports,
        scene_timings=scene_timings,
        editing_rhythm_plan=editing_rhythm_plan,
        audio_timeline=audio_binding_timeline,
        profile_id="smooth_high_energy_shorts",
    )
    report.update(build_montage_execution_report(montage_plan))
    report["montage_renderer_execution"] = {
        "execution_approach": "in_renderer_quick_cut_progress_reset",
        "consumed_quick_cut_clip_count": executed_montage_clip_count,
        "executed_transition_types": sorted(executed_montage_transition_types),
        "scene_execution": scene_montage_execution,
        "unsupported_transition_policy": "left_as_planned_only_metadata",
    }
    return attach_montage_plan_to_report(report, montage_plan)


def save_render_report(result: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
