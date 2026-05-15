from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse


BACKEND_DIR = Path(__file__).resolve().parents[1]
GENERATED_ROOT = BACKEND_DIR / "generated_videos"


def _database_path() -> Path:
    raw_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./threadangle.db")
    parsed = urlparse(raw_url)
    if not raw_url.startswith("sqlite"):
        raise SystemExit("Only sqlite DATABASE_URL values are supported by this local repair script.")
    if parsed.path and parsed.path != "/:memory:":
        db_path = Path(parsed.path)
        if os.name == "nt" and str(db_path).startswith("\\"):
            db_path = Path(str(db_path).lstrip("\\"))
    else:
        db_path = Path(raw_url.rsplit("///", 1)[-1])
    if not db_path.is_absolute():
        db_path = BACKEND_DIR / db_path
    return db_path.resolve()


def _json_paths(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except Exception:
        return []
    found: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            for key, item in node.items():
                if str(key).lower() in {"video", "video_path", "final_mp4", "final_video", "path"} and isinstance(item, str):
                    found.append(item)
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str) and node.lower().endswith(".mp4"):
            found.append(node)

    walk(parsed)
    return found


def _candidate_paths(generation: sqlite3.Row, hmr_rows: list[sqlite3.Row]) -> list[Path]:
    values: list[str] = []
    if generation["video_file"]:
        values.extend(_json_paths(generation["video_file"]) or [generation["video_file"]])
    for row in hmr_rows:
        for column in ("artifact_paths_json", "result_json"):
            if column in row.keys():
                values.extend(_json_paths(row[column]))

    candidates: list[Path] = []
    seen: set[Path] = set()
    for value in values:
        raw = Path(str(value))
        path = raw if raw.is_absolute() else GENERATED_ROOT / raw
        resolved = path.resolve()
        if resolved not in seen:
            candidates.append(resolved)
            seen.add(resolved)
    return candidates


def _relative_generated_path(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(GENERATED_ROOT.resolve()).as_posix()
    except ValueError:
        return None


def _hmr_rows(conn: sqlite3.Connection, generation_id: int) -> list[sqlite3.Row]:
    tables = [row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    if "hmr_render_jobs" not in tables:
        return []
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(hmr_render_jobs)")]
    where_parts = []
    params: list[object] = []
    for column in ("generation_id", "generationId"):
        if column in columns:
            where_parts.append(f"{column} = ?")
            params.append(generation_id)
    if not where_parts:
        return []
    return list(conn.execute(f"SELECT * FROM hmr_render_jobs WHERE {' OR '.join(where_parts)}", params))


def inspect_generation(generation_id: int, apply: bool, show_files: bool) -> int:
    db_path = _database_path()
    print(f"[repair] database={db_path}")
    print(f"[repair] generated_root={GENERATED_ROOT.resolve()}")
    if not db_path.exists():
        print("[repair] database file not found")
        return 2

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        generation = conn.execute("SELECT * FROM generations WHERE id = ?", (generation_id,)).fetchone()
        if not generation:
            print(f"[repair] generation {generation_id} not found")
            return 1

        print(f"[repair] generation_id={generation['id']} status={generation['status']} video_file={generation['video_file']}")
        hmr_rows = _hmr_rows(conn, generation_id)
        print(f"[repair] hmr_jobs={len(hmr_rows)}")
        candidates = _candidate_paths(generation, hmr_rows)
        existing = [path for path in candidates if path.exists() and path.is_file() and path.suffix.lower() == ".mp4"]
        if show_files:
            for path in candidates:
                print(f"[repair] candidate exists={path.exists()} path={path}")

        safe_existing = [(path, _relative_generated_path(path)) for path in existing]
        safe_existing = [(path, rel) for path, rel in safe_existing if rel]
        if safe_existing:
            path, rel = safe_existing[0]
            print(f"[repair] found_mp4={path}")
            print(f"[repair] relative_video_file={rel}")
            if apply:
                conn.execute(
                    "UPDATE generations SET video_file = ?, status = 'success', error_message = NULL WHERE id = ?",
                    (rel, generation_id),
                )
                conn.commit()
                print("[repair] applied backfill and marked generation success")
            else:
                print("[repair] dry_run no database changes")
            return 0

        print("[repair] no valid local MP4 artifact found")
        if apply:
            conn.execute(
                "UPDATE generations SET status = 'failed', error_message = ? WHERE id = ?",
                ("Render completed metadata but no final MP4 artifact was found.", generation_id),
            )
            conn.commit()
            print("[repair] applied failed status because release contract is not satisfied")
        else:
            print("[repair] dry_run no database changes")
        return 3
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or repair a video generation's local MP4 artifact contract.")
    parser.add_argument("--generation-id", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--show-files", action="store_true")
    args = parser.parse_args()
    return inspect_generation(args.generation_id, apply=args.apply, show_files=args.show_files)


if __name__ == "__main__":
    sys.exit(main())
