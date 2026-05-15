# Free TTS Production Notes

Threadangle's no-spend render path uses free TTS fallbacks before it will allow a silent render.

## Dependency Contract

- Python package: `pyttsx3==2.90` in `backend/requirements.txt`
- Network fallback: `gTTS==2.5.4` in `backend/requirements.txt`
- Ubuntu/systemd voice package: install `espeak` or `espeak-ng`

Example Ubuntu setup:

```bash
sudo apt-get update
sudo apt-get install -y espeak espeak-ng
pip install -r backend/requirements.txt
```

## Safe Runtime Modes

- `tts_provider=free`: tries gTTS, then pyttsx3, with no ElevenLabs credits.
- `VIDEO_ALLOW_SILENT_FALLBACK=1`: allows an explicit silent render if all free TTS options fail.
- `VIDEO_ALLOW_SILENT_FALLBACK=0`: stops rendering when audio is required and free TTS fails.

Do not enable ElevenLabs for the free/no-spend render path unless paid providers are explicitly allowed for that run.
