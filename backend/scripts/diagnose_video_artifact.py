"""Diagnose generated video artifact linkage for a Generation row.

Usage from repo root:
    python backend/scripts/diagnose_video_artifact.py 67

This script is intentionally read-only. It prints:
- generation.video_file / thumbnail / status
- latest hmr_render_jobs result/artifact JSON
- whether referenced local files exist
- most recent MP4 files under backend/generated_videos
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"


def _find_db() -> Path:
    candidates = list(REPO_ROOT.rglob("*.db"))
    if not candidates:
        raise SystemExit("No .db files found under repo root. Adjust script for your DB setup.")
    # Prefer backend-local DBs if present.
    for candidate in candidates:
        if "backend" in candidate.parts:
            return candidate
    return candidates[0]


def _resolve(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    raw = str(path_value).strip().split("?", 1)[0].split("#", 1)[0]
    if not raw or raw.startswith(("http://", "https://", "data:")):
        return None
    p = Path(raw)
    candidates = [p] if p.is_absolute() else [
        REPO_ROOT / p,
        BACKEND_ROOT / p,
        BACKEND_ROOT / "generated_videos" / p,
        BACKEND_ROOT / "generated_videos" / p.name,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return candidates[0] if candidates else None


def _json_load(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _print_path(label: str, value: str | None) -> None:
    resolved = _resolve(value)
    print(f"{label}: {value}")
    if resolved:
        print(f"  resolved: {resolved}")
        print(f"  exists: {resolved.exists()} size={resolved.stat().st_size if resolved.exists() else 'missing'}")


def main() -> None:
    generation_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    db = _find_db()
    print(f"DB: {db}")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    if generation_id is None:
        row = conn.execute("SELECT id FROM generations ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            raise SystemExit("No generations found.")
        generation_id = int(row["id"])

    print(f"\n=== Generation {generation_id} ===")
    gen = conn.execute(
        """
        SELECT id, status, video_run_id, video_file, video_thumbnail,
               video_duration_seconds, runway_credits_used,
               elevenlabs_credits_used, total_cost_usd, error_message,
               created_at
        FROM generations
        WHERE id = ?
        """,
        (generation_id,),
    ).fetchone()
    if not gen:
        raise SystemExit(f"Generation {generation_id} not found.")
    gd = dict(gen)
    for k, v in gd.items():
        if k not in {"video_file", "video_thumbnail"}:
            print(f"{k}: {v}")
    _print_path("video_file", gd.get("video_file"))
    _print_path("video_thumbnail", gd.get("video_thumbnail"))

    print(f"\n=== Latest HMR job for generation {generation_id} ===")
    job = conn.execute(
        """
        SELECT id, generation_id, run_id, status, percent, step, message,
               error_message, artifact_paths_json, result_json,
               render_invoked, worker_active, completed_at
        FROM hmr_render_jobs
        WHERE generation_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (generation_id,),
    ).fetchone()
    if not job:
        print("No HMR job found.")
    else:
        jd = dict(job)
        for k in ("artifact_paths_json", "result_json"):
            jd[k] = _json_load(jd.get(k))
        for k, v in jd.items():
            if k in {"artifact_paths_json", "result_json"}:
                print(f"{k}: {json.dumps(v, indent=2, default=str)[:5000]}")
            else:
                print(f"{k}: {v}")

    print("\n=== Recent MP4 files ===")
    root = BACKEND_ROOT / "generated_videos"
    if not root.exists():
        print(f"No generated_videos folder found at {root}")
        return
    files = sorted(root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    for p in files:
        print(f"{p} size={p.stat().st_size} mtime={p.stat().st_mtime}")


if __name__ == "__main__":
    main()
