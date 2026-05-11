from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional


GENERATED_ROOT = Path(__file__).resolve().parents[1] / "generated_videos"
VOICE_CACHE_ROOT = Path(__file__).resolve().parents[1] / "assets" / "voice_cache"


@dataclass
class CleanupReport:
    files_deleted: list[str] = field(default_factory=list)
    dirs_deleted: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def deleted_count(self) -> int:
        return len(self.files_deleted) + len(self.dirs_deleted)


def generated_root() -> Path:
    return GENERATED_ROOT


def voice_cache_root() -> Path:
    return VOICE_CACHE_ROOT


def _resolve_under(root: Path, path_value: Optional[str | Path]) -> Optional[Path]:
    if not path_value:
        return None
    root_resolved = root.resolve()
    candidate = Path(str(path_value))
    try:
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    except Exception:
        return None
    if resolved == root_resolved or root_resolved in resolved.parents:
        return resolved
    return None


def relative_generated_path(path_value: Optional[str | Path]) -> Optional[str]:
    if not path_value:
        return None
    root = generated_root().resolve()
    candidate = Path(str(path_value))
    try:
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    except Exception:
        return candidate.name
    if root in resolved.parents:
        return str(resolved.relative_to(root)).replace("\\", "/")
    return candidate.name


def _delete_path(path: Path, report: CleanupReport) -> None:
    try:
        if path.is_file():
            path.unlink(missing_ok=True)
            report.files_deleted.append(str(path))
        elif path.is_dir():
            shutil.rmtree(path)
            report.dirs_deleted.append(str(path))
    except FileNotFoundError:
        return
    except Exception as exc:
        report.skipped.append(f"{path}: {exc}")


def safe_delete_generated_path(path_value: Optional[str | Path], report: Optional[CleanupReport] = None) -> CleanupReport:
    report = report or CleanupReport()
    resolved = _resolve_under(generated_root(), path_value)
    if not resolved:
        if path_value:
            report.skipped.append(f"{path_value}: outside generated_videos")
        return report
    if resolved.exists() and resolved != generated_root().resolve():
        _delete_path(resolved, report)
    return report


def safe_move_into_run_dir(path_value: Optional[str | Path], run_dir: Path, subdir: str) -> Optional[str]:
    if not path_value:
        return None

    candidate = Path(str(path_value))
    try:
        resolved = candidate.resolve()
    except Exception:
        return None
    if not resolved.exists() or not resolved.is_file():
        return None

    generated = generated_root().resolve()
    voice_cache = voice_cache_root().resolve()
    if generated not in resolved.parents and voice_cache not in resolved.parents:
        return None

    target_dir = run_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / resolved.name
    if target.resolve() == resolved:
        return str(target.relative_to(generated_root())).replace("\\", "/")

    try:
        resolved.replace(target)
    except Exception:
        try:
            shutil.copy2(resolved, target)
            resolved.unlink(missing_ok=True)
        except Exception:
            return None
    return str(target.relative_to(generated_root())).replace("\\", "/")


def delete_generation_assets(
    *,
    video_file: Optional[str],
    video_thumbnail: Optional[str],
    video_run_id: Optional[str],
) -> CleanupReport:
    report = CleanupReport()
    root = generated_root()

    candidates: set[Path] = set()
    for value in (video_file, video_thumbnail):
        resolved = _resolve_under(root, value)
        if resolved:
            candidates.add(resolved)
            if resolved.parent != root.resolve():
                candidates.add(resolved.parent)
        if value:
            by_name = _resolve_under(root, Path(str(value)).name)
            if by_name:
                candidates.add(by_name)

    run_id = (video_run_id or "").strip()
    if run_id and root.exists():
        for folder in (root, root / "raw", root / "temp", root / "cache"):
            if folder.exists():
                candidates.update(folder.glob(f"*{run_id}*"))

    for path in sorted(candidates, key=lambda p: len(p.parts), reverse=True):
        resolved = _resolve_under(root, path)
        if not resolved or resolved == root.resolve() or not resolved.exists():
            continue
        _delete_path(resolved, report)

    return report


def _older_than(path: Path, cutoff: datetime) -> bool:
    try:
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return False
    return modified < cutoff


def _iter_cleanup_candidates(completed_hours: int, failed_temp_hours: int) -> Iterable[tuple[Path, str]]:
    root = generated_root()
    if not root.exists():
        return []

    now = datetime.now(timezone.utc)
    completed_cutoff = now - timedelta(hours=max(1, completed_hours))
    temp_cutoff = now - timedelta(hours=max(1, failed_temp_hours))

    candidates: list[tuple[Path, str]] = []
    for child in root.iterdir():
        if child.name in {"raw", "temp", "cache"}:
            continue
        if _older_than(child, completed_cutoff):
            candidates.append((child, "completed"))

    for subdir_name in ("raw", "temp", "cache"):
        subdir = root / subdir_name
        if not subdir.exists():
            continue
        for child in subdir.iterdir():
            if _older_than(child, temp_cutoff):
                candidates.append((child, subdir_name))

    return candidates


def cleanup_old_video_artifacts(
    *,
    completed_hours: Optional[int] = None,
    failed_temp_hours: Optional[int] = None,
    dry_run: bool = False,
) -> CleanupReport:
    completed = completed_hours or int(os.getenv("VIDEO_COMPLETED_ARTIFACT_EXPIRY_HOURS", "72"))
    failed_temp = failed_temp_hours or int(os.getenv("VIDEO_TEMP_ARTIFACT_EXPIRY_HOURS", "24"))
    report = CleanupReport()
    root = generated_root().resolve()

    for candidate, label in _iter_cleanup_candidates(completed, failed_temp):
        resolved = _resolve_under(root, candidate)
        if not resolved or resolved == root:
            report.skipped.append(f"{candidate}: outside generated_videos")
            continue
        if dry_run:
            report.skipped.append(f"dry-run {label}: {resolved}")
            continue
        _delete_path(resolved, report)

    return report
