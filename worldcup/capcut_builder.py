"""
CapCut Draft Builder for World Cup 2026 pipeline (Issue #123, step 16C).

Public API
----------
build_draft(team) -> str

Orchestrates a complete World Cup Short into a CapCut project:
  1. Renders HTML card PNGs via render_team_cards()
  2. Fetches portrait footage via fetch_footage() per segment
  3. Runs the existing CapcutPipeline (subclassed to inject WC assets)
  4. Copies card PNGs into Resources/media/ for manual use in CapCut
  5. Returns the draft folder path (already registered in root_meta_info.json)

Segment timeline (~37 s total):
  hook    3.0 s  — football fans footage
  history 8.0 s  — trophy/stadium footage
  player  5.0 s  — action footage  (×3)
  group   6.0 s  — stadium crowd footage
  cta     5.0 s  — crowd celebration footage

The draft has ONE video track (7 footage clips in sequence).
Card PNGs land in Resources/media/ so the user can drag them onto the
timeline manually in CapCut.
"""
from __future__ import annotations

import os
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

# Force UTF-8 stdout so emoji in capcut_pipeline.py print statements don't
# crash on Windows consoles that default to cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Bootstrap: add backend/ to sys.path so capcut_pipeline is importable ───────
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import capcut_pipeline as _cp      # module-level constants (CAPCUT_ASSETS_DIR, etc.)
from capcut_pipeline import CapcutPipeline

from worldcup.data.footage import fetch_footage
from worldcup.renderer.html_cards import render_team_cards

# ── Timeline ────────────────────────────────────────────────────────────────────

SEGMENTS: list[tuple[str, float]] = [
    ("hook",    3.0),
    ("history", 8.0),
    ("player",  5.0),   # player_0
    ("player",  5.0),   # player_1
    ("player",  5.0),   # player_2
    ("group",   6.0),
    ("cta",     5.0),
]  # total 37s — 1080×1920 portrait (Shorts)

SEGMENTS_LONG: list[tuple[str, float]] = [
    ("hook",     10.0),
    ("history",  25.0),
    ("player",   18.0),  # player_0
    ("player",   18.0),  # player_1
    ("player",   18.0),  # player_2
    ("group",    18.0),
    ("cta",      10.0),
]  # total 117s ≈ 2 min — 1920×1080 landscape (long-form)

_CAPCUT_SYSTEM_DRAFTS = Path(
    os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft")
)


# ── Plan builder ────────────────────────────────────────────────────────────────

def _make_plan(team: str) -> dict:
    """Build a CapcutPipeline-compatible plan dict from the WC segment list."""
    _narrations = {
        "hook":    f"{team.title()}. FIFA World Cup 2026.",
        "history": f"The record books of {team.title()} at the World Cup.",
        "player":  f"Key player to watch for {team.title()} at WC 2026.",
        "group":   f"{team.title()} group stage draw — FIFA World Cup 2026.",
        "cta":     f"Can {team.title()} win the World Cup? Comment below.",
    }
    scenes = []
    for i, (seg, dur) in enumerate(SEGMENTS):
        scenes.append({
            "scene_number":     i + 1,
            "duration_seconds": int(dur),
            "mood":             "Hype",
            "pexels_search":    f"{team} football",
            "caption":          f"{team.title()} · {seg.upper()} · WC 2026",
            "narration":        _narrations.get(seg, f"{team} {seg}"),
            "text_overlay":     "",
            "instruction":      "",
        })
    return {
        "title":            f"{team.lower().replace(' ', '_')}_wc2026",
        "script_text":      f"{team} World Cup 2026 Short",
        "scenes":           scenes,
        "voiceover_text":   f"{team} World Cup 2026",
        "thumbnail_prompt": f"{team} football stadium",
        "thumbnail_title":  [team.title(), "WC 2026"],
        "thumbnail_scheme": "Dark",
    }


# ── Pipeline subclass ────────────────────────────────────────────────────────────

class _WCPipeline(CapcutPipeline):
    """
    CapcutPipeline subclass for the World Cup pipeline.

    Overrides:
      _fetch_footage       — no-op; copying is done in _build_capcut_project
      _generate_voiceover  — no-op (voice added manually in CapCut)
      _generate_thumbnail  — converts hook.png to JPEG draft cover
      _build_capcut_project — copies footage DIRECTLY from self._footage_paths
                              into draft_dir/Resources/media/ so the two-step
                              CAPCUT_ASSETS_DIR intermediary is bypassed entirely
    """

    def __init__(
        self,
        job_id: str,
        plan: dict,
        footage_paths: list[Path],      # one per SEGMENTS entry, in order
        thumb_png: Optional[Path],       # hook.png used as draft cover
    ) -> None:
        super().__init__(job_id, plan, update_job_fn=None)
        self._footage_paths = footage_paths
        self._thumb_png     = thumb_png

    # -- Overrides ---------------------------------------------------------------

    def _fetch_footage(self) -> None:
        """No-op — footage is copied directly in _build_capcut_project."""
        if "footage_fetched" not in self.steps_completed:
            self.steps_completed.append("footage_fetched")
        self._persist()

    def _generate_voiceover(self) -> None:
        """Skip — voiceover is added manually in CapCut."""
        if "voiceover_done" not in self.steps_completed:
            self.steps_completed.append("voiceover_done")
        self._persist()

    def _generate_thumbnail(self) -> None:
        """Convert hook.png to JPEG and stage it as the CapCut draft cover."""
        if self._thumb_png and self._thumb_png.exists():
            try:
                from PIL import Image
                thumb_dir = self.output_dir / "thumbnail"
                thumb_dir.mkdir(parents=True, exist_ok=True)
                img = Image.open(self._thumb_png).convert("RGB")
                img.save(str(thumb_dir / "thumbnail_final.jpg"),
                         format="JPEG", quality=88)
            except Exception as exc:
                print(f"[build_draft] Thumbnail conversion failed: {exc}")
        if "thumbnail_done" not in self.steps_completed:
            self.steps_completed.append("thumbnail_done")
        self._persist()

    def _build_capcut_project(self) -> None:
        """
        Copy WC footage directly from self._footage_paths into
        draft_dir/Resources/media/ and build draft_content.json.

        Bypasses CAPCUT_ASSETS_DIR so files are guaranteed to be present
        at the path referenced in draft_content.json.
        """
        self.current_step = "Building CapCut timeline..."
        self._persist()

        try:
            _cp._ensure_capcut_server()
        except Exception as exc:
            print(f"[build_draft] CapCutAPI server warn: {exc}")

        draft_id = self._compute_draft_id()

        # Resolve draft directory (mirrors base class logic)
        if _CAPCUT_SYSTEM_DRAFTS.exists():
            draft_dir = _CAPCUT_SYSTEM_DRAFTS / self.project_name
        else:
            draft_dir = Path(str(_cp.CAPCUT_DRAFTS_DIR)) / self.project_name

        draft_dir.mkdir(parents=True, exist_ok=True)
        media_dir = draft_dir / "Resources" / "media"
        media_dir.mkdir(parents=True, exist_ok=True)

        # ── Copy footage directly into Resources/media/ ───────────────────
        scene_clips: list[Path] = []
        scene_durations = [int(dur) for _, dur in SEGMENTS]

        for i, src in enumerate(self._footage_paths):
            dest = media_dir / f"scene_{i + 1}_trimmed.mp4"
            if src.exists() and src.stat().st_size > 0:
                shutil.copy2(src, dest)
                print(f"[build_draft]   scene_{i + 1}_trimmed.mp4  "
                      f"({src.stat().st_size // 1024} KB)")
            else:
                # Create a black placeholder so the slot is never empty
                print(f"[build_draft]   scene_{i + 1}: footage missing, "
                      f"creating placeholder")
                self._create_placeholder_video(dest, scene_durations[i])

            if dest.exists() and dest.stat().st_size > 0:
                scene_clips.append(dest)

        # ── Copy thumbnail (staged by _generate_thumbnail) ───────────────
        thumb_src = self.output_dir / "thumbnail" / "thumbnail_final.jpg"
        if thumb_src.exists():
            shutil.copy2(thumb_src, draft_dir / "draft_cover.jpg")

        # ── Calculate total duration ──────────────────────────────────────
        duration_ms = self._get_project_duration_ms(media_dir)
        if duration_ms == 0:
            duration_ms = int(sum(scene_durations) * 1000)
        duration_us = duration_ms * 1000

        # ── Write CapCut metadata files ───────────────────────────────────
        self._write_capcut_project_files(draft_dir, draft_id, duration_us)

        # ── Build draft_content.json ──────────────────────────────────────
        captions = [
            scene.get("caption_text", "") or scene.get("narration", "")
            for scene in self.plan.get("scenes", [])
        ]
        self._generate_draft_content(
            draft_dir, draft_id, duration_us,
            scene_clips, None, scene_durations, captions,
        )

        print(f"[build_draft] Draft written: {draft_dir}")

        # ── Register in CapCut's root_meta_info.json ──────────────────────
        if _CAPCUT_SYSTEM_DRAFTS.exists():
            try:
                draft_norm  = os.path.normpath(str(draft_dir))
                capcut_norm = os.path.normpath(str(_CAPCUT_SYSTEM_DRAFTS))
                if draft_norm.startswith(capcut_norm):
                    self._register_draft_in_root_meta(draft_dir, draft_id, duration_us)
            except Exception as exc:
                print(f"[build_draft] root_meta registration failed: {exc}")

        if "capcut_built" not in self.steps_completed:
            self.steps_completed.append("capcut_built")
        if draft_dir.exists() and "draft_saved" not in self.steps_completed:
            self.steps_completed.append("draft_saved")
        self._persist()


# ── Public API ───────────────────────────────────────────────────────────────────

def build_draft(team: str) -> str:
    """
    Build a CapCut draft for *team* and return the draft folder path.

    The draft is written directly into CapCut's system projects folder
    (if it exists) and registered in root_meta_info.json, so it appears
    in CapCut Desktop immediately without any manual import.

    Parameters
    ----------
    team : str
        Team name matching wc2026_data.py (e.g. "Brazil").

    Returns
    -------
    str
        Absolute path to the CapCut draft folder.
    """
    print(f"\n[build_draft] == World Cup draft: {team} ==")

    # Step 1 — render HTML card PNGs ------------------------------------------
    print("[build_draft] Step 1: rendering card PNGs...")
    card_pngs = render_team_cards(team, players=3)
    # Order guaranteed: hook, history, player_0, player_1, player_2, group, cta
    print(f"[build_draft]   {len(card_pngs)} PNGs rendered")

    # Step 2 — fetch footage per segment --------------------------------------
    print("[build_draft] Step 2: fetching footage clips...")
    footage_paths: list[Path] = []
    for seg_key, dur in SEGMENTS:
        clip = fetch_footage(team, seg_key, dur)
        footage_paths.append(clip)
    print(f"[build_draft]   {len(footage_paths)} clips ready")

    # Step 3 — build the CapCut draft -----------------------------------------
    print("[build_draft] Step 3: building CapCut draft...")
    job_id   = str(uuid.uuid4())
    plan     = _make_plan(team)
    thumb    = card_pngs[0] if card_pngs else None

    pipeline = _WCPipeline(job_id, plan, footage_paths, thumb)
    # Override to millisecond timestamp so rapid successive runs never collide
    pipeline.project_name = (
        f"{team.lower().replace(' ', '_')}_wc2026_{int(time.time() * 1000)}"
    )
    print(f"[build_draft]   project_name = {pipeline.project_name}")

    pipeline.run()

    if pipeline.status != "done":
        detail = getattr(pipeline, "error_detail", "") or ""
        raise RuntimeError(
            f"CapcutPipeline failed for {team}: {pipeline.error}\n{detail}"
        )

    # Resolve draft folder location (mirrors _build_capcut_project logic)
    if _CAPCUT_SYSTEM_DRAFTS.exists():
        draft_dir = _CAPCUT_SYSTEM_DRAFTS / pipeline.project_name
    else:
        draft_dir = Path(str(_cp.CAPCUT_DRAFTS_DIR)) / pipeline.project_name

    # Step 4 — copy card PNGs into Resources/media/ for manual use in CapCut ---
    print("[build_draft] Step 4: copying card PNGs to Resources/media/...")
    media_dir = draft_dir / "Resources" / "media"
    copied = 0
    for png in card_pngs:
        if png and png.exists() and png.stat().st_size > 0:
            shutil.copy2(png, media_dir / png.name)
            print(f"[build_draft]   {png.name}  ({png.stat().st_size // 1024} KB)")
            copied += 1
    print(f"[build_draft]   {copied}/{len(card_pngs)} card PNGs copied")

    # Step 5 — verify draft folder size ----------------------------------------
    total_bytes = sum(
        f.stat().st_size for f in draft_dir.rglob("*") if f.is_file()
    )
    total_mb = total_bytes / (1024 * 1024)
    print(f"\n[build_draft] Draft folder size: {total_mb:.1f} MB")
    if total_bytes < 10_000_000:
        print(f"[build_draft] WARNING: draft is only {total_bytes // 1024} KB — "
              f"media files may not have copied correctly")
        media_files = list((draft_dir / "Resources" / "media").glob("*"))
        print(f"[build_draft] Resources/media contains {len(media_files)} files:")
        for f in sorted(media_files):
            print(f"[build_draft]   {f.name}  ({f.stat().st_size // 1024} KB)")

    print(f"\n[build_draft] Draft ready:")
    print(f"  {draft_dir}")
    return str(draft_dir)
