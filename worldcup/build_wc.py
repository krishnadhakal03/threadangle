"""
build_wc.py — Full France pipeline: cards → footage → MP4.

Usage:
  python worldcup/build_wc.py France
  python worldcup/build_wc.py France --no-voice
  python worldcup/build_wc.py France --skip-cards

Environment:
  WC_VOICE=false   same as --no-voice (default)
  WC_VOICE=true    attempt narration from cached .wav

Output: worldcup/output/final/{team}_wc2026_{timestamp}.mp4
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from worldcup.capcut_builder import SEGMENTS
from worldcup.config import OUTPUT_DIR
from worldcup.data.footage import fetch_footage
from worldcup.assembler.mp4_assembler import assemble_mp4


def _fmt(seconds: float) -> str:
    return f"{seconds:.1f}s"


def _step(n: int, label: str) -> float:
    print(f"\n── Step {n}: {label}")
    return time.perf_counter()


def _done(t0: float) -> None:
    print(f"   ✓ done in {_fmt(time.perf_counter() - t0)}")


# ── Step 1: render cards ────────────────────────────────────────────────────────

def render_cards(team: str, skip: bool) -> dict[str, Path]:
    cards_dir = OUTPUT_DIR / "cards" / team.lower()
    existing  = {p.stem: p for p in cards_dir.glob("*.png")} if cards_dir.exists() else {}
    required  = {"hook", "history", "player_0", "player_1", "player_2", "group", "cta"}
    missing   = required - existing.keys()

    if missing and not skip:
        print(f"   Rendering {len(missing)} card(s): {sorted(missing)}")
        from worldcup.renderer.html_cards import render_team_cards
        rendered = render_team_cards(team)
        existing = {p.stem: p for p in rendered}
        print(f"   {len(existing)} cards saved → {cards_dir}")
    elif existing:
        print(f"   {len(existing)} cached cards from {cards_dir}")
    else:
        print("   WARNING: no cards found and --skip-cards set")
    return existing


# ── Step 2: fetch footage ───────────────────────────────────────────────────────

def fetch_all_footage(team: str) -> tuple[list[Path], list[str]]:
    """Return (footage_paths, segment_names) in SEGMENTS order."""
    paths: list[Path] = []
    names: list[str]  = []
    player_idx = 0
    for seg_name, seg_dur in SEGMENTS:
        label = f"player_{player_idx}" if seg_name == "player" else seg_name
        if seg_name == "player":
            player_idx += 1
        t0 = time.perf_counter()
        p  = fetch_footage(team, seg_name, seg_dur)
        elapsed = time.perf_counter() - t0
        size_kb = p.stat().st_size // 1024 if p.exists() else 0
        print(f"   [{label:10s}] {_fmt(elapsed):>5}  {size_kb} KB  {p.name}")
        paths.append(p)
        names.append(label)
    return paths, names


# ── Step 3: assemble ────────────────────────────────────────────────────────────

def build_mp4(
    team: str,
    footage_paths: list[Path],
    card_by_name: dict[str, Path],
    seg_names: list[str],
    narration_path: Path | None,
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
    )


# ── Main ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="World Cup Short — full pipeline")
    parser.add_argument("team", help="Team name, e.g. France")
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
    no_voice = args.no_voice or os.getenv("WC_VOICE", "false").lower() != "true"

    wall_start = time.perf_counter()
    print(f"{'='*52}")
    print(f"  World Cup Short — {team}")
    print(f"  Voice: {'off' if no_voice else 'on'}")
    print(f"{'='*52}")

    # ── 1. Cards ────────────────────────────────────────────────────────────────
    t0 = _step(1, "render_team_cards()")
    card_by_name = render_cards(team, skip=args.skip_cards)
    _done(t0)

    # ── 2. Footage ──────────────────────────────────────────────────────────────
    t0 = _step(2, f"fetch_footage() — {len(SEGMENTS)} segments")
    footage_paths, seg_names = fetch_all_footage(team)
    _done(t0)

    # ── 3. Narration ─────────────────────────────────────────────────────────────
    narration_path: Path | None = None
    if not no_voice:
        slug    = team.lower().replace(" ", "_")
        wav     = OUTPUT_DIR / f"{slug}_vo.wav"
        if wav.exists():
            narration_path = wav
            print(f"\n── Narration: {wav}")
        else:
            print("\n── Narration: no .wav found — silent")

    # ── 4. Assemble ──────────────────────────────────────────────────────────────
    t0 = _step(3, "assemble_mp4()")
    out = build_mp4(team, footage_paths, card_by_name, seg_names, narration_path)
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
