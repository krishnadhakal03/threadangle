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
except ImportError:  # pragma: no cover - direct script execution fallback
    from hybrid_scene_templates import draw_caption_band, get_template


BASE_DIR = Path(__file__).resolve().parents[1]
GENERATED_DIR = BASE_DIR / "generated_videos"
CACHE_DIR = GENERATED_DIR / "cache" / "hybrid_motion"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HYBRID_METHOD_TO_TEMPLATE = {
    "stock_plus_motion_overlay": "hook_footage_overlay",
    "local_ai_prompt_capture": "ai_prompt_mock",
    "hybrid_motion_scene": "money_shock_math",
    "comparison_motion_scene": "comparison_split",
    "payoff_motion_scene": "payoff_number_reveal",
    "cta_motion_scene": "cta_callback",
}


def split_caption_events(script_text: str, duration: float, max_words: int = 4) -> list[dict[str, Any]]:
    words = re.findall(r"[A-Za-z0-9$']+", script_text or "")
    if not words:
        return []
    chunks = [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]
    slot = max(0.45, float(duration) / max(1, len(chunks)))
    events = []
    t = 0.0
    for chunk in chunks:
        events.append({"start": round(t, 3), "end": round(min(duration, t + slot), 3), "text": chunk})
        t += slot
    return events


def _scene_value(scene: Any, key: str, default: Any = None) -> Any:
    if isinstance(scene, dict):
        return scene.get(key, default)
    return getattr(scene, key, default)


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


def _stock_cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"stock_{digest}.mp4"


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
                        "url": chosen.get("url"),
                        "width": chosen.get("width"),
                        "height": chosen.get("height"),
                        "duration": video.get("duration"),
                        "id": f"pixabay:{video.get('id')}",
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
    if 2 <= duration <= 20:
        score += 20
    return score


def _download_stock_candidate(candidate: dict[str, Any], warnings: list[str]) -> Path | None:
    url = candidate.get("url")
    if not url:
        return None
    out = _stock_cache_path(url)
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


def _select_stock_background(scene: Any, template: str, used_ids: set[str], warnings: list[str]) -> tuple[Path | None, dict[str, Any]]:
    query = _scene_query(scene, template)
    candidates = _fetch_pexels_candidates(query) + _fetch_pixabay_candidates(query)
    if not candidates:
        return None, {"query": query, "candidates": 0, "provider_available": _provider_available(), "reason": "no_candidates"}
    ranked = sorted(candidates, key=lambda c: _score_stock_candidate(c, used_ids), reverse=True)
    for candidate in ranked[:5]:
        path = _download_stock_candidate(candidate, warnings)
        if path:
            used_ids.add(str(candidate.get("id")))
            return path, {"query": query, "candidates": len(candidates), "chosen": candidate, "provider_available": True}
    return None, {"query": query, "candidates": len(candidates), "provider_available": True, "reason": "download_or_validation_failed"}


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
) -> dict[str, Any]:
    start_time = time.time()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    scene_reports: list[dict[str, Any]] = []
    used_stock_ids: set[str] = set()
    media_mix: dict[str, int] = {}
    stock_status = {
        "provider_available": _provider_available(),
        "used": False,
        "reason": "",
    }

    prepared = []
    for idx, scene in enumerate(scenes):
        template_name = _scene_template(scene, idx)
        duration = _scene_duration(scene, 2.6)
        bg_path = None
        stock_meta: dict[str, Any] = {}
        if use_stock_backgrounds and template_name == "hook_footage_overlay" and _provider_available():
            bg_path, stock_meta = _select_stock_background(scene, template_name, used_stock_ids, warnings)
            if bg_path:
                stock_status["used"] = True
            elif not stock_status["reason"]:
                stock_status["reason"] = stock_meta.get("reason") or "stock_unavailable_for_scene"
        elif use_stock_backgrounds and template_name == "hook_footage_overlay" and not _provider_available():
            stock_status["reason"] = "pexels_pixabay_keys_not_configured"
        prepared.append((scene, template_name, duration, bg_path, stock_meta))

    source_total_duration = sum(item[2] for item in prepared)
    audio_duration = _probe_media_duration(audio_path)
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
                    (scene, template_name, duration * scale, bg_path, stock_meta)
                    for scene, template_name, duration, bg_path, stock_meta in prepared[1:]
                ],
            ]
            duration_strategy = "scaled_to_audio_duration_preserve_hook"
        else:
            scale = audio_duration / source_total_duration
            prepared = [
                (scene, template_name, duration * scale, bg_path, stock_meta)
                for scene, template_name, duration, bg_path, stock_meta in prepared
            ]
            duration_strategy = "scaled_to_audio_duration"
    total_duration = sum(item[2] for item in prepared)
    caption_events = split_caption_events(script_text, total_duration, max_words=4)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output), fourcc, float(fps), (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Unable to open VideoWriter for {output}")

    global_frame = 0
    elapsed = 0.0
    for scene_idx, (scene, template_name, duration, bg_path, stock_meta) in enumerate(prepared):
        template = get_template(template_name)
        frame_count = max(1, int(round(duration * fps)))
        capture = cv2.VideoCapture(str(bg_path)) if bg_path else None
        media_class = "REAL_STOCK" if bg_path else "ANIMATED_FALLBACK"
        if template_name == "ai_prompt_mock":
            media_class = "LOCAL_CAPTURE"
        elif template_name == "cta_callback":
            media_class = "ANIMATED_FALLBACK"
        elif template_name == "comparison_split":
            media_class = "MOTION_SCENE"
        elif template_name in {"money_shock_math", "payoff_number_reveal"}:
            media_class = "MOTION_CARD"
        media_mix[media_class] = media_mix.get(media_class, 0) + 1

        scene_caption_reports = []
        text_cropped = False
        key_boxes: list[tuple[int, int, int, int]] = []
        motion_scores = []
        postability_signals: dict[str, Any] = {}
        for local_frame in range(frame_count):
            progress = local_frame / max(1, frame_count - 1)
            canvas = _read_bg_frame(capture, width, height, progress)
            if canvas is None:
                canvas = np.zeros((height, width, 3), dtype=np.uint8)
            scene_config = {
                **(scene if isinstance(scene, dict) else {}),
                "has_real_background": bg_path is not None,
                "style_preset": style_preset,
            }
            template_report = template(local_frame, progress, canvas, scene_config)
            text_cropped = text_cropped or bool(template_report.get("cropped"))
            key_boxes = [tuple(b) for b in template_report.get("key_number_boxes", [])]
            motion_scores.append(float(template_report.get("motion_score") or 0.5))
            for key, value in (template_report.get("postability_signals") or {}).items():
                if key not in postability_signals:
                    postability_signals[key] = value

            current_t = elapsed + local_frame / float(fps)
            active_caption = next((ev["text"] for ev in caption_events if ev["start"] <= current_t < ev["end"]), "")
            cap_report = draw_caption_band(canvas, active_caption, reserved_boxes=key_boxes)
            if local_frame == 0 and cap_report.get("caption"):
                scene_caption_reports.append(cap_report)
            writer.write(canvas)
            global_frame += 1

        if capture is not None:
            capture.release()
        scene_id = _scene_value(scene, "id", None) or _scene_value(scene, "scene", None) or _scene_value(scene, "scene_index", scene_idx + 1)
        scene_reports.append({
            "scene_id": scene_id,
            "template": template_name,
            "duration": round(duration, 3),
            "media_classification": media_class,
            "provider_usage": stock_meta if bg_path else {"provider": None, "reason": stock_status.get("reason") or "animated_or_motion_template"},
            "background_id": str(bg_path) if bg_path else f"{media_class}:{template_name}",
            "caption_report": scene_caption_reports[0] if scene_caption_reports else {"caption": "", "word_count": 0},
            "text_cropped": text_cropped,
            "motion_score": round(sum(motion_scores) / max(1, len(motion_scores)), 3),
            "number_reveal": template_name == "payoff_number_reveal",
            "postability_signals": postability_signals,
        })
        elapsed += duration

    writer.release()
    if audio_path or use_free_tts:
        _mux_audio(output, audio_path, total_duration, warnings)
    final_video_duration = _probe_media_duration(output)
    sync_target_duration = audio_duration or total_duration
    sync_delta = abs((final_video_duration or total_duration) - sync_target_duration) if sync_target_duration else None

    return {
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
        "media_mix": media_mix,
        "warnings": warnings,
        "render_time_sec": round(time.time() - start_time, 3),
        "caption_events": caption_events,
        "caption_report": {
            "max_words": 4,
            "event_count": len(caption_events),
            "violations": [ev for ev in caption_events if len(str(ev.get("text", "")).split()) > 4],
        },
        "stock_status": stock_status,
    }


def save_render_report(result: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
