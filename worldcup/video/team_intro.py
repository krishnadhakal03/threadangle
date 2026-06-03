"""
Type 1: Team Intro video — broadcast-quality 55-second Short.

Segment layout (short, 1080x1920):
  Seg 1  HOOK          0-3s    slide_in         → full-bleed flag bg + team name
  Seg 2  HISTORY       3-18s   crossfade+zoom   → 2x2 stat grid + win-rate bar
  Seg 3  KEY PLAYERS  18-38s   crossfade+fade   → 3 × 6.67s player cards
  Seg 4  GROUP STAGE  38-48s   crossfade+slide  → GROUP X + 4 team rows + flags
  Seg 5  CTA          48-55s   crossfade+fade   → prediction prompt + subscribe

Long (1920×1080) version doubles all segment durations.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from worldcup.config import SHORT_RES, LONG_RES, OUTPUT_DIR, FPS
from worldcup.data.wc2026_data import get_full_team_data, get_flag_url, get_group_info
from worldcup.renderer import card as card_mod
from worldcup.renderer import animations as anim
from worldcup.renderer.theme import get_country_theme


# ── Timeline constants ─────────────────────────────────────────────────────────
# Short: total ≈ 55s  |  Long: total ≈ 110s (doubles)

SHORT_SEG = {
    "hook":    3.0,
    "history": 15.0,
    "players": 20.0,   # shared across N player cards
    "group":   10.0,
    "cta":      7.0,
}
TRANSITION_DUR  = 0.30   # crossfade between segments
SLIDE_DUR       = 0.40   # slide-in entrance
FADE_DUR        = 0.30   # fade-up entrance
ZOOM_DUR        = 0.50   # zoom-in on history


# ── Internal helpers ───────────────────────────────────────────────────────────

def _bg_color(team: str) -> tuple:
    ct = get_country_theme(team)
    return ct["gradient_bottom"]


def _collect_clips(team: str, static: dict, key_players: list, fmt: str):
    """
    Build and return a list of MoviePy clips representing the full timeline.
    """
    from moviepy.editor import concatenate_videoclips

    scale = 2.0 if fmt == "long" else 1.0
    segs  = {k: v * scale for k, v in SHORT_SEG.items()}
    res   = SHORT_RES if fmt == "short" else LONG_RES

    group_info = static["group_info"]
    group_id   = group_info["group"]
    group_teams = group_info.get("teams", [])
    flag_url    = get_flag_url(team)
    history = static
    accent = get_country_theme(team)["accent"]

    # ── Build segment PIL Images ───────────────────────────────────────────────
    print("[team_intro] Building segment images...")

    seg1 = card_mod.build_hook_segment(
        team=team, group_id=group_id, flag_url=flag_url, res=res)

    seg2 = card_mod.build_history_segment(
        team=team,
        titles=history["titles"],
        appearances=history["appearances"],
        best_finish=history["best_finish"],
        last_title=history["titles_years"][-1] if history.get("titles_years") else 0,
        res=res,
    )

    # Player cards — fetch photos
    from worldcup.data.photos import get_player_photo
    player_segs = []
    for p in key_players[:3]:
        print(f"  [photo] {p['name']}...")
        photo = get_player_photo(p["name"], size=300, accent=accent)
        player_segs.append(card_mod.build_player_segment(
            player=p, photo=photo, team=team, res=res))

    seg4 = card_mod.build_group_segment(
        team=team, group_id=group_id, group_teams=group_teams, res=res)

    seg5 = card_mod.build_cta_segment(
        team=team, group_id=group_id, res=res)

    bg = _bg_color(team)

    # ── Assemble clips ─────────────────────────────────────────────────────────
    print("[team_intro] Assembling animation clips...")
    clips = []

    # Seg 1 HOOK: slide_in + hold
    clips.append(anim.slide_in_from_right(seg1, FPS, SLIDE_DUR, bg=bg))
    clips.append(anim.hold(seg1, FPS, segs["hook"] - SLIDE_DUR))

    # Seg 2 HISTORY: crossfade + zoom + hold
    cf_dur  = min(TRANSITION_DUR, segs["history"] * 0.05)
    zm_dur  = min(ZOOM_DUR, segs["history"] * 0.10)
    hold_dur = segs["history"] - cf_dur - zm_dur
    clips.append(anim.crossfade(seg1, seg2, FPS, cf_dur))
    clips.append(anim.zoom_in(seg2, FPS, zm_dur))
    clips.append(anim.hold(seg2, FPS, hold_dur))

    # Seg 3 PLAYERS: one crossfade+fade_up per player
    player_dur_each = segs["players"] / max(len(player_segs), 1)
    prev_seg = seg2
    for pseg in player_segs:
        cf_d  = min(TRANSITION_DUR, player_dur_each * 0.05)
        fu_d  = min(FADE_DUR, player_dur_each * 0.05)
        hd    = player_dur_each - cf_d - fu_d
        clips.append(anim.crossfade(prev_seg, pseg, FPS, cf_d))
        clips.append(anim.fade_up(pseg, FPS, fu_d, bg=bg))
        clips.append(anim.hold(pseg, FPS, hd))
        prev_seg = pseg

    # Seg 4 GROUP: crossfade + slide_in + hold
    last_player = player_segs[-1] if player_segs else seg2
    cf_d4  = min(TRANSITION_DUR, segs["group"] * 0.04)
    sl_d4  = min(SLIDE_DUR, segs["group"] * 0.07)
    hd4    = segs["group"] - cf_d4 - sl_d4
    clips.append(anim.crossfade(last_player, seg4, FPS, cf_d4))
    clips.append(anim.slide_in_from_right(seg4, FPS, sl_d4, bg=bg))
    clips.append(anim.hold(seg4, FPS, hd4))

    # Seg 5 CTA: crossfade + fade_up + hold
    cf_d5  = min(TRANSITION_DUR, segs["cta"] * 0.05)
    fu_d5  = min(FADE_DUR, segs["cta"] * 0.05)
    hd5    = segs["cta"] - cf_d5 - fu_d5
    clips.append(anim.crossfade(seg4, seg5, FPS, cf_d5))
    clips.append(anim.fade_up(seg5, FPS, fu_d5, bg=bg))
    clips.append(anim.hold(seg5, FPS, hd5))

    return clips


# ── Public entry point ─────────────────────────────────────────────────────────

def render_team_intro(
    team: str,
    fmt: str = "short",
    output_path: Optional[str] = None,
    voiceover: bool = True,
    captions: bool = True,
    dry_run: bool = False,
):
    """
    Render a broadcast-quality Team Intro Short for *team*.

    Duration: ~55 s (short) or ~110 s (long).
    Uses wc2026_data as primary source; optionally enriches with API-Football.
    """
    from moviepy.editor import concatenate_videoclips

    res = SHORT_RES if fmt == "short" else LONG_RES

    if output_path is None:
        slug = team.lower().replace(" ", "_")
        output_path = str(OUTPUT_DIR / f"{slug}_team_intro_{fmt}.mp4")

    # ── Static data ────────────────────────────────────────────────────────────
    static      = get_full_team_data(team)
    key_players = static["key_players"]

    if not key_players:
        print(f"[team_intro] WARNING: No key player data for {team}")
        key_players = [{"name": team, "position": "TBD", "club": "TBD", "country_goals": 0}]

    # Optionally enrich squad from API
    if not dry_run:
        try:
            from worldcup.data.fetcher import get_team_squad
            live = get_team_squad(team)
            if live.get("players"):
                # Merge: prefer wc2026_data key players for spotlight cards,
                # use API for squad display
                pass   # key_players stays from static for spotlight
        except (EnvironmentError, OSError) as exc:
            print(f"[team_intro] API unavailable — using static data ({exc})")

    if dry_run:
        # Save one PNG per segment for QA
        print(f"[team_intro] Dry run for {team}")
        from worldcup.data.photos import get_player_photo
        from worldcup.renderer.theme import get_country_theme
        group_info = static["group_info"]
        flag_url   = get_flag_url(team)
        accent     = get_country_theme(team)["accent"]

        segs = [
            card_mod.build_hook_segment(team, group_info["group"], flag_url, res),
            card_mod.build_history_segment(
                team, static["titles"], static["appearances"],
                static["best_finish"],
                static["titles_years"][-1] if static.get("titles_years") else 0, res),
            card_mod.build_group_segment(
                team, group_info["group"], group_info.get("teams", []), res),
            card_mod.build_cta_segment(team, group_info["group"], res),
        ]
        for kp in key_players[:1]:
            photo = get_player_photo(kp["name"], 300, accent)
            segs.insert(2, card_mod.build_player_segment(kp, photo, team, res))

        for i, seg_img in enumerate(segs):
            p = OUTPUT_DIR / f"{team.lower().replace(' ','_')}_seg_{i:02d}.png"
            seg_img.save(str(p))
            print(f"  Saved: {p}")
        return

    # ── Build clips ────────────────────────────────────────────────────────────
    clips = _collect_clips(team, static, key_players, fmt)

    print("[team_intro] Concatenating clips...")
    video = concatenate_videoclips(clips, method="compose")

    # ── Voiceover (optional) ────────────────────────────────────────────────────
    if voiceover:
        try:
            from worldcup.audio.voiceover import generate_script, generate_voiceover
            from worldcup.audio.captions  import script_to_segments, generate_srt

            print("[team_intro] Generating voiceover...")
            team_data_script = {
                "team_name":  team,
                "players":    [p["name"] for p in key_players[:3]],
                "history":    static,
                "group":      static["group_info"],
            }
            script    = generate_script(team_data_script, int(video.duration))
            audio_path = str(OUTPUT_DIR / f"{team.lower().replace(' ','_')}_vo.mp3")
            generate_voiceover(script, output_path=audio_path)

            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(audio_path)
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            video = video.set_audio(audio)

            if captions:
                from worldcup.audio.captions import script_to_segments, generate_srt
                segs_data = script_to_segments(script, video.duration)
                srt_path  = OUTPUT_DIR / f"{team.lower().replace(' ','_')}_captions.srt"
                generate_srt(segs_data, srt_path)
                from worldcup.audio.captions import burn_captions
                video = burn_captions(video, segs_data)
        except Exception as exc:
            print(f"[team_intro] Voiceover failed ({exc}) — rendering silent")

    # ── Write ───────────────────────────────────────────────────────────────────
    print(f"[team_intro] Writing video ({video.duration:.1f}s) -> {output_path}")
    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(OUTPUT_DIR / "tmp_audio.m4a"),
        remove_temp=True,
        logger="bar",
    )
    print(f"[team_intro] Done -> {output_path}")
