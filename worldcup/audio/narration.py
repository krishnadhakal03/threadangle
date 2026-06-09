"""
worldcup/audio/narration.py

ElevenLabs voice narration with gTTS fallback.

WC_VOICE=false (default) → generate_narration() returns None immediately.
WC_VOICE=true            → generates per-segment MP3, concatenates, returns Path.

Fallback chain:
  1. ElevenLabs API  (if ELEVENLABS_API_KEY set)
  2. gTTS            (free, offline-capable)
  3. Silence clip    (never crashes the pipeline)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# ── Config ─────────────────────────────────────────────────────────────────────
WC_VOICE = os.getenv("WC_VOICE", "false").lower() == "true"

ELEVENLABS_VOICE_ID  = "pNInz6obpgDQGcFmaJgB"   # Adam — energetic male sports
ELEVENLABS_MODEL     = "eleven_monolingual_v1"
ELEVENLABS_STABILITY = 0.4
ELEVENLABS_SIMILARITY= 0.8

NARRATION_SCRIPTS: dict[str, str] = {
    "hook":     "{team}. FIFA World Cup 2026. One team. One dream.",
    "history":  "{team} have appeared at {appearances} World Cups, "
                "winning it {titles} times. Their best finish — {best}.",
    "player_0": "{name}. {position} for {club}. "
                "{goals} international goals. A danger at every World Cup.",
    "player_1": "{name} brings {caps} caps of experience. "
                "The engine of {team}'s midfield.",
    "player_2": "{name}. Pace, skill, and {goals} goals for {team}. "
                "One to watch in 2026.",
    "group":    "{team} drawn in Group {group_id} alongside "
                "{opponents}. A tough path ahead.",
    "cta":      "Can {team} win the World Cup? "
                "Comment your prediction below.",
}

_POS_LABELS = {
    "FW": "forward", "MF": "midfielder",
    "DF": "defender", "GK": "goalkeeper",
}

from worldcup.config import OUTPUT_DIR
from worldcup.capcut_builder import SEGMENTS

AUDIO_DIR = OUTPUT_DIR / "audio"
FFMPEG    = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"


# ── Script builder ──────────────────────────────────────────────────────────────

def _build_script(seg_key: str, team: str, team_data: dict, player_idx: int = 0) -> str:
    """Fill narration template for *seg_key*, substituting live team/player data."""
    template = NARRATION_SCRIPTS.get(seg_key)
    if not template:
        return team.title()

    key_players = team_data.get("key_players", [])
    group_info  = team_data.get("group_info", {})
    group_id    = group_info.get("group", "?")
    group_teams = group_info.get("teams", [])
    opponents   = ", ".join(t for t in group_teams if t.lower() != team.lower())

    p   = key_players[player_idx] if player_idx < len(key_players) else {}
    pos = _POS_LABELS.get(p.get("position", "").upper(), "player")

    return template.format(
        team        = team.title(),
        appearances = team_data.get("appearances", "?"),
        titles      = team_data.get("titles", 0),
        best        = team_data.get("best_finish", "?"),
        name        = p.get("name", ""),
        position    = pos,
        club        = p.get("club", ""),
        goals       = p.get("country_goals") or p.get("goals", 0),
        caps        = p.get("caps", 0),
        group_id    = group_id,
        opponents   = opponents,
    )


# ── TTS backends ────────────────────────────────────────────────────────────────

def _elevenlabs_tts(text: str, dest: Path, api_key: str) -> bool:
    """Generate MP3 via ElevenLabs. Returns False on 429 or any error."""
    try:
        import httpx
        r = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": ELEVENLABS_MODEL,
                "voice_settings": {
                    "stability":        ELEVENLABS_STABILITY,
                    "similarity_boost": ELEVENLABS_SIMILARITY,
                },
            },
            timeout=30.0,
        )
        if r.status_code == 429:
            print("[narration] ElevenLabs quota exceeded — falling back to gTTS")
            return False
        r.raise_for_status()
        dest.write_bytes(r.content)
        return dest.exists() and dest.stat().st_size > 1_000
    except Exception as exc:
        print(f"[narration] ElevenLabs error: {exc}")
        return False


def _gtts_tts(text: str, dest: Path) -> bool:
    """Generate MP3 via gTTS (free, no key required)."""
    try:
        from gtts import gTTS
        gTTS(text=text, lang="en", slow=False).save(str(dest))
        return dest.exists() and dest.stat().st_size > 1_000
    except Exception as exc:
        print(f"[narration] gTTS error: {exc}")
        return False


def _make_silence(dest: Path, duration: float) -> None:
    """Create a silent MP3 of *duration* seconds as last-resort fallback."""
    subprocess.run(
        [FFMPEG, "-y", "-f", "lavfi",
         "-i", f"anullsrc=r=44100:cl=stereo",
         "-t", f"{duration:.3f}",
         "-c:a", "mp3", "-b:a", "64k", str(dest)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


# ── ffmpeg audio helpers ────────────────────────────────────────────────────────

def _pad_trim(src: Path, dest: Path, duration: float) -> bool:
    """Pad with silence or trim to exactly *duration* seconds."""
    try:
        r = subprocess.run(
            [FFMPEG, "-y",
             "-i", str(src),
             "-af", f"apad=whole_dur={duration:.3f}",
             "-t",  f"{duration:.3f}",
             "-c:a", "mp3", "-b:a", "128k",
             str(dest)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60,
        )
        return r.returncode == 0 and dest.exists()
    except Exception as exc:
        print(f"[narration] pad/trim error: {exc}")
        return False


def _concat_mp3s(mp3s: list[Path], dest: Path) -> bool:
    """Concatenate MP3 files via ffmpeg concat demuxer."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        list_path = Path(f.name)
        for p in mp3s:
            f.write(f"file '{p.as_posix()}'\n")
    try:
        r = subprocess.run(
            [FFMPEG, "-y",
             "-f", "concat", "-safe", "0",
             "-i", str(list_path),
             "-c:a", "mp3", "-b:a", "128k",
             str(dest)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120,
        )
        return r.returncode == 0 and dest.exists()
    except Exception as exc:
        print(f"[narration] concat error: {exc}")
        return False
    finally:
        list_path.unlink(missing_ok=True)


# ── Public API ──────────────────────────────────────────────────────────────────

def generate_narration(team: str, team_data: dict) -> Optional[Path]:
    """
    Generate per-segment narration and return path to concatenated MP3.

    Returns None immediately if WC_VOICE=false — no API calls made.
    Fallback chain: ElevenLabs → gTTS → silence (never crashes pipeline).
    Output: worldcup/output/audio/{team}_narration.mp3
    """
    if not WC_VOICE:
        print("[narration] WC_VOICE=false — skipping (dev mode)")
        return None

    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / "backend" / ".env")
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        print("[narration] ELEVENLABS_API_KEY not set — using gTTS fallback")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    slug = team.lower().replace(" ", "_")

    seg_mp3s: list[Path] = []
    player_idx = 0

    for seg_name, seg_dur in SEGMENTS:
        label = f"player_{player_idx}" if seg_name == "player" else seg_name
        if seg_name == "player":
            player_idx += 1

        p_idx  = int(label.split("_")[1]) if label.startswith("player_") else 0
        script = _build_script(label, team, team_data, p_idx)
        raw    = AUDIO_DIR / f"{slug}_{label}_raw.mp3"
        trimmed = AUDIO_DIR / f"{slug}_{label}.mp3"

        print(f"[narration] [{label:10s}] {script[:60]}...")

        ok = False
        if api_key:
            ok = _elevenlabs_tts(script, raw, api_key)
        if not ok:
            print(f"[narration] [{label}] → gTTS")
            ok = _gtts_tts(script, raw)
        if not ok:
            print(f"[narration] [{label}] → silence fallback")
            _make_silence(raw, seg_dur)

        if not _pad_trim(raw, trimmed, seg_dur):
            shutil.copy(str(raw), str(trimmed))
        seg_mp3s.append(trimmed)

    final = AUDIO_DIR / f"{slug}_narration.mp3"
    if _concat_mp3s(seg_mp3s, final):
        size_kb = final.stat().st_size // 1024
        print(f"[narration] Done → {final} ({size_kb} KB)")
        return final

    print("[narration] Concat failed — returning None")
    return None
