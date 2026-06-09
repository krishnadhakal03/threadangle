"""
build_wc.py — Full pipeline: cards → footage → MP4.

Usage:
  python worldcup/build_wc.py France
  python worldcup/build_wc.py France --no-voice
  python worldcup/build_wc.py France --format long --no-voice
  python worldcup/build_wc.py France --skip-cards

Environment:
  WC_VOICE=false     same as --no-voice (default)
  WC_VOICE=true      generate narration via ElevenLabs/gTTS
  BGM_TRACK=hype     football_hype.mp3 (default)
  BGM_TRACK=dramatic dramatic.mp3

Output (short): worldcup/output/final/{team}_wc2026_short_{timestamp}.mp4
Output (long):  worldcup/output/final/{team}_wc2026_long_{timestamp}.mp4
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from worldcup.capcut_builder import SEGMENTS, SEGMENTS_LONG
from worldcup.config import OUTPUT_DIR
from worldcup.data.footage import fetch_footage
from worldcup.data.wc2026_data import get_full_team_data
from worldcup.assembler.captions import build_segment_captions, generate_srt
from worldcup.assembler.mp4_assembler import assemble_mp4
from worldcup.audio.narration import generate_narration


def _fmt(seconds: float) -> str:
    return f"{seconds:.1f}s"


def _step(n: int, label: str) -> float:
    print(f"\n── Step {n}: {label}")
    return time.perf_counter()


def _done(t0: float) -> None:
    print(f"   ✓ done in {_fmt(time.perf_counter() - t0)}")


# ── Step 1: render cards ────────────────────────────────────────────────────────

def render_cards(team: str, skip: bool, fmt: str = "short") -> dict[str, Path]:
    slug      = team.lower().replace(" ", "_")
    subdir    = f"{slug}_long" if fmt == "long" else slug
    cards_dir = OUTPUT_DIR / "cards" / subdir
    existing  = {p.stem: p for p in cards_dir.glob("*.png")} if cards_dir.exists() else {}
    required  = {"hook", "history", "player_0", "player_1", "player_2", "group", "cta"}
    missing   = required - existing.keys()

    if missing and not skip:
        print(f"   Rendering {len(missing)} card(s) [{fmt}]: {sorted(missing)}")
        from worldcup.renderer.html_cards import render_team_cards
        rendered = render_team_cards(team, fmt=fmt)
        existing = {p.stem: p for p in rendered}
        print(f"   {len(existing)} cards saved → {cards_dir}")
    elif existing:
        print(f"   {len(existing)} cached cards from {cards_dir}")
    else:
        print("   WARNING: no cards found and --skip-cards set")
    return existing


# ── Step 2: fetch footage ───────────────────────────────────────────────────────

def fetch_all_footage(
    team: str,
    segs: list = None,
    resolution: tuple[int, int] = (1080, 1920),
) -> tuple[list[Path], list[str], list[float]]:
    """Return (footage_paths, segment_names, segment_durations) in segment order."""
    if segs is None:
        segs = SEGMENTS
    paths:     list[Path]  = []
    names:     list[str]   = []
    durations: list[float] = []
    player_idx = 0
    for seg_name, seg_dur in segs:
        label = f"player_{player_idx}" if seg_name == "player" else seg_name
        if seg_name == "player":
            player_idx += 1
        t0 = time.perf_counter()
        p  = fetch_footage(team, label, seg_dur, resolution=resolution)
        elapsed = time.perf_counter() - t0
        size_kb = p.stat().st_size // 1024 if p.exists() else 0
        print(f"   [{label:10s}] {_fmt(elapsed):>5}  {size_kb} KB  {p.name}")
        paths.append(p)
        names.append(label)
        durations.append(seg_dur)
    return paths, names, durations


# ── Step 3: assemble ────────────────────────────────────────────────────────────

def build_mp4(
    team: str,
    footage_paths: list[Path],
    card_by_name: dict[str, Path],
    seg_names: list[str],
    narration_path: Path | None,
    srt_path: Path | None = None,
    fmt: str = "short",
) -> Path:
    ordered_cards: list[Path] = []
    for label in seg_names:
        card = card_by_name.get(label)
        if card is None or not card.exists():
            fallback = next(iter(card_by_name.values()), None)
            print(f"   WARNING: card '{label}' missing — using fallback")
            card = fallback
        ordered_cards.append(card)

    return assemble_mp4(
        team=team,
        footage_paths=footage_paths,
        card_pngs=ordered_cards,
        narration_path=narration_path,
        srt_path=srt_path,
        fmt=fmt,
    )


# ── Main ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="World Cup pipeline — short or long-form")
    parser.add_argument("team", help="Team name, e.g. France")
    parser.add_argument(
        "--format", choices=["short", "long"], default="short",
        help="Output format: short (37s, 1080×1920) or long (~117s, 1920×1080)",
    )
    parser.add_argument(
        "--no-voice", action="store_true",
        help="Skip narration (default; also set by WC_VOICE=false)",
    )
    parser.add_argument(
        "--skip-cards", action="store_true",
        help="Reuse cached card PNGs; skip Playwright render",
    )
    args = parser.parse_args()

    team     = args.team
    fmt      = args.format
    no_voice = args.no_voice or os.getenv("WC_VOICE", "false").lower() != "true"
    segs     = SEGMENTS_LONG if fmt == "long" else SEGMENTS
    res      = (1920, 1080) if fmt == "long" else (1080, 1920)

    wall_start = time.perf_counter()
    print(f"{'='*52}")
    print(f"  World Cup {'Long-form' if fmt=='long' else 'Short'} — {team}")
    print(f"  Format: {fmt}  Resolution: {res[0]}×{res[1]}")
    print(f"  Voice: {'off' if no_voice else 'on'}")
    print(f"{'='*52}")

    # ── 1. Cards ────────────────────────────────────────────────────────────────
    t0 = _step(1, f"render_team_cards() [{fmt}]")
    card_by_name = render_cards(team, skip=args.skip_cards, fmt=fmt)
    _done(t0)

    # ── 2. Footage ──────────────────────────────────────────────────────────────
    t0 = _step(2, f"fetch_footage() — {len(segs)} segments @ {res[0]}×{res[1]}")
    footage_paths, seg_names, seg_durations = fetch_all_footage(team, segs=segs, resolution=res)
    _done(t0)

    # ── 3. Captions ──────────────────────────────────────────────────────────────
    t0 = _step(3, "generate_srt()")
    team_data    = get_full_team_data(team)
    caption_segs = build_segment_captions(team, seg_names, seg_durations, team_data)
    srt_path     = generate_srt(team, caption_segs)
    _done(t0)

    # ── 4. Narration ─────────────────────────────────────────────────────────────
    t0 = _step(4, "generate_narration()")
    narration_path: Path | None = None
    if not no_voice:
        narration_path = generate_narration(team, team_data)
        if narration_path:
            size_kb = narration_path.stat().st_size // 1024
            print(f"   → {narration_path} ({size_kb} KB)")
    else:
        print("   WC_VOICE=false — skipped")
    _done(t0)

    # ── 5. Assemble ──────────────────────────────────────────────────────────────
    t0 = _step(5, "assemble_mp4()")
    out = build_mp4(team, footage_paths, card_by_name, seg_names,
                    narration_path, srt_path, fmt=fmt)
    _done(t0)

    # ── Summary ──────────────────────────────────────────────────────────────────
    total = time.perf_counter() - wall_start
    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"\n{'='*52}")
    print(f"  DONE in {_fmt(total)}")
    print(f"  {size_mb:.1f} MB  →  {out}")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()
