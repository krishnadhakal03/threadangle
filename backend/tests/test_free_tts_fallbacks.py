from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def no_postprocess(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VOICE_POSTPROCESS", "0")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)


def test_force_free_gtts_success_does_not_call_elevenlabs(monkeypatch):
    from routes.voice_gen import VoiceGenRequest, generate_voice

    class FakeGTTS:
        def __init__(self, text: str, lang: str = "en"):
            self.text = text
            self.lang = lang

        def save(self, path: str):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"mp3")

    fake_gtts = ModuleType("gtts")
    fake_gtts.gTTS = FakeGTTS
    monkeypatch.setitem(sys.modules, "gtts", fake_gtts)

    def fake_run(cmd, **_kwargs):
        Path(cmd[-1]).write_bytes(b"0" * 4096)
        return MagicMock(returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)
    paid_call = MagicMock()
    monkeypatch.setattr("routes.voice_gen.requests.post", paid_call)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "dummy-paid-key-that-must-not-be-used")

    result = generate_voice(VoiceGenRequest(text="Free local narration", force_free=True))

    assert result.provider == "gtts"
    assert Path(result.audio_file).exists()
    paid_call.assert_not_called()


def test_missing_free_tts_dependencies_report_explicit_reason(monkeypatch):
    from routes.voice_gen import VoiceGenRequest, generate_voice

    monkeypatch.setitem(sys.modules, "gtts", None)
    monkeypatch.setitem(sys.modules, "pyttsx3", None)

    with pytest.raises(HTTPException) as exc:
        generate_voice(VoiceGenRequest(text="Free local narration", force_free=True))

    assert exc.value.status_code == 500
    assert "Voice generation failed" in str(exc.value.detail)
    assert "gTTS" in str(exc.value.detail)
    assert "pyttsx3" in str(exc.value.detail)


def test_silent_fallback_is_explicit_when_free_tts_fails(monkeypatch):
    from routes.voice_gen import VoiceGenRequest, generate_voice

    monkeypatch.setitem(sys.modules, "gtts", None)
    monkeypatch.setitem(sys.modules, "pyttsx3", None)

    result = generate_voice(
        VoiceGenRequest(text="Free local narration", force_free=True, allow_silent=True)
    )

    assert result.provider == "silent"
    assert result.audio_file == ""
    assert "silent fallback selected" in (result.warning or "")
