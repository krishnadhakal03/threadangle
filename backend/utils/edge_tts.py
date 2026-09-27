"""
Free high-quality TTS via Microsoft Edge's read-aloud service (edge-tts).

No API key, no credits, near-human neural voices. Used as the FIRST free
option in the voice fallback chain — ahead of gTTS (robotic) and pyttsx3
(requires espeak on the server).
"""
from __future__ import annotations

import asyncio
import os

# Override with EDGE_TTS_VOICE. Good narrators:
#   en-US-GuyNeural / en-US-AriaNeural / en-GB-RyanNeural / en-AU-NatashaNeural
DEFAULT_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-GuyNeural")


def generate_edge_tts_sync(text: str, out_path: str, voice: str | None = None) -> str:
    """Synchronous wrapper — safe to call from sync FastAPI handlers."""
    return asyncio.run(_generate(text, out_path, voice or DEFAULT_VOICE))


async def _generate(text: str, out_path: str, voice: str) -> str:
    try:
        from edge_tts import Communicate
    except ImportError as exc:
        raise RuntimeError(
            "edge-tts is not installed (pip install edge-tts)"
        ) from exc
    communicate = Communicate(text, voice)
    await communicate.save(out_path)
    size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    if size < 1000:
        raise RuntimeError(f"edge-tts produced an empty file ({size} bytes)")
    return out_path
