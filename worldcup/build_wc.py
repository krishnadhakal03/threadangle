"""
build_wc.py — CLI entry point for the WC Short assembler (Issue #124).

Usage:
  python worldcup/build_wc.py France --no-voice
  python worldcup/build_wc.py Brazil
  python worldcup/build_wc.py England --no-voice --skip-cards
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as: python worldcup/build_wc.py ... from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from worldcup.capcut_builder import SEGMENTS
from worldcup.config import OUTPUT_DIR
from worldcup.data.footage import fetch_footage
from worldcup.assembler.mp4_assembler import assemble_mp4


def _load_cards(team: str, skip_render: bool) -> dict[str, Path]:
    """
    Return a {stem: Path} dict of card PNGs for *team*.
    Renders via Playwright if cards are missing and skip_render is False.
    """
    cards_dir = OUTPUT_DIR / "cards" / team.lower()
    existing = {p.stem: p for p in cards_dir.glob("*.png")} if cards_dir.exists() else {}

    required = {"hook", "history", "player_0", "player_1", "player_2", "group", "cta"}
    missing = required - existing.keys()

    if missing and not skip_render:
        print(f"[build_wc] Rendering {len(missing)} missing card(s): {sorted(missing)}")
        from worldcup.renderer.html_cards import render_team_cards
        rendered = render_team_cards(team)
        existing = {p.stem: p for p in rendered}
    elif existing:
        print(f"[build_wc] Using {len(existing)} cached card(s) from {cards_dir}")
    else:
        print("[build_wc] WARNING: no cards found and --skip-cards set — overlays will be skipped")

    return existing


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble a World Cup Short MP4 via ffmpeg."
    )
    parser.add_argument("team", help="Team name, e.g. France")
    parser.add_argument(
        "--no-voice", action="store_true",
        help="Skip narration — produce a silent video (fast dev mode)"
    )
    parser.add_argument(
        "--skip-cards", action="store_true",
        help="Use cached card PNGs; skip Playwright re-render"
    )
    args = parser.parse_args()

    team: str = args.team

    # ── 1. Cards ───────────────────────────────────────────────────────────────
    card_by_name = _load_cards(team, skip_render=args.skip_cards)

    # ── 2. Footage + ordered card list ────────────────────────────────────────
    footage_paths: list[Path] = []
    ordered_cards: list[Path] = []
    player_idx = 0

    for seg_name, seg_dur in SEGMENTS:
        card_key = f"player_{player_idx}" if seg_name == "player" else seg_name
        if seg_name == "player":
            player_idx += 1

        footage_path = fetch_footage(team, seg_name, seg_dur)
        footage_paths.append(footage_path)

        card = card_by_name.get(card_key)
        if card is None or not card.exists():
            # Fall back to first available card so assemble_mp4 receives valid paths
            fallback = next(iter(card_by_name.values()), None)
            print(f"[build_wc] WARNING: card '{card_key}' missing — using fallback")
            card = fallback
        ordered_cards.append(card)

    # ── 3. Narration (optional) ───────────────────────────────────────────────
    narration_path: Path | None = None
    if not args.no_voice:
        slug = team.lower().replace(" ", "_")
        wav_path = OUTPUT_DIR / f"{slug}_vo.wav"
        if wav_path.exists():
            print(f"[build_wc] Using existing voiceover: {wav_path}")
            narration_path = wav_path
        else:
            print("[build_wc] No voiceover found — rendering silent (run worldcup/run.py for voice)")

    # ── 4. Assemble ───────────────────────────────────────────────────────────
    print(f"\n[build_wc] Assembling {len(footage_paths)}-segment Short for {team}...")
    out = assemble_mp4(
        team=team,
        footage_paths=footage_paths,
        card_pngs=ordered_cards,
        narration_path=narration_path,
    )
    print(f"\n[build_wc] SUCCESS → {out}")


if __name__ == "__main__":
    main()
