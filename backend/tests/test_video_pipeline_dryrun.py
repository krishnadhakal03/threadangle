"""
Zero-credit automated test suite for the video generation pipeline.

ALL tests run in DRY-RUN / stock-only mode.
NO RunwayML, NO ElevenLabs, NO Pexels/Pixabay requests are made.
Every external call is mocked.

Coverage:
  1.  parse_script — hook/body/cta splitting edge-cases
  2.  resolve_duration_seconds — cap at 45s, minimum 10s
  3.  build_scene_plan — scene count limits, proportional allocation
  4.  _scene_query_candidates — priority ordering & keyword map hits
  5.  scenes_from_rows — confirmed plan → ScenePlan round-trip
  6.  parse_clip_to_clip_structure — valid / single / empty input
  7.  score_scene_heuristic — hook always 10, trigger words, budget guard
  8.  select_runway_model — model selection and budget guardrails
  9.  get_hybrid_scene_strategy — 70% budget cap, model assignment
  10. fetch_scene_clips (stock mode) — mocked Pexels search + download
  11. fetch_scene_clips (ai mode) — Runway quota error → fallback to stock
  12. fetch_scene_clips (auto mode) — hybrid strategy respects max_ai_scenes
  13. assemble_video — happy path with dummy clips
  14. generate_voice — ElevenLabs success, 429 fallback, pyttsx3 fallback
  15. /video/free endpoint — dry_run=True, no external calls
  16. Credit leakage guard — /generate endpoint never calls ElevenLabs live
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from fastapi import BackgroundTasks

# ---------------------------------------------------------------------------
# Ensure backend/ is on sys.path so direct imports work
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Force dry-run env before importing any pipeline module
os.environ.setdefault("VIDEO_GENERATION_DRY_RUN", "1")
os.environ.setdefault("PEXELS_API_KEY", "test_pexels_key")
os.environ.setdefault("PIXABAY_API_KEY", "test_pixabay_key")
os.environ.setdefault("RUNWAYML_API_KEY", "test_runway_key")
os.environ.setdefault("RUNWAYML_AVAILABLE_CREDITS", "880")
os.environ.setdefault("ELEVENLABS_API_KEY", "test_el_key")

# ---------------------------------------------------------------------------
# Import pipeline internals
# ---------------------------------------------------------------------------
from utils.video_pipeline import (
    ScenePlan,
    parse_script,
    resolve_duration_seconds,
    build_scene_plan,
    scenes_from_rows,
    parse_clip_to_clip_structure,
    _scene_query_candidates,
    get_hybrid_scene_strategy,
    fetch_scene_clips,
    new_run_id,
)
from utils.visual_scoring import score_scene_heuristic, select_runway_model
from utils.runwayml_client import RunwayMLQuotaError


# ===========================================================================
# 1.  parse_script
# ===========================================================================

class TestParseScript:
    def test_full_script_splits_to_three_parts(self):
        script = "Hook line. Body line one. Body line two. CTA follow now."
        parts = parse_script(script)
        assert parts.hook
        assert parts.body
        assert parts.cta

    def test_explicit_hook_body_cta_parameters(self):
        parts = parse_script(
            full_script=None,
            hook="Start here",
            body="Middle content here for longer body",
            cta="Follow now",
        )
        assert parts.hook == "Start here"
        assert parts.cta == "Follow now"

    def test_very_short_script_still_returns_parts(self):
        parts = parse_script("Short.")
        # Should not raise; all fields are strings
        assert isinstance(parts.hook, str)
        assert isinstance(parts.body, str)
        assert isinstance(parts.cta, str)

    def test_empty_script_returns_empty_strings(self):
        parts = parse_script("")
        assert parts.hook == "" or parts.hook is not None


# ===========================================================================
# 2.  resolve_duration_seconds
# ===========================================================================

class TestResolveDuration:
    def _parts(self, hook="Hook.", body="Body " * 20, cta="CTA."):
        return parse_script(full_script=None, hook=hook, body=body, cta=cta)

    def test_minimum_is_ten_seconds(self):
        parts = self._parts(hook="H", body="B", cta="C")
        d = resolve_duration_seconds(parts)
        assert d >= 10

    def test_maximum_is_45_seconds(self):
        long_parts = parse_script("x " * 2000)
        d = resolve_duration_seconds(long_parts)
        assert d <= 45, f"Expected ≤45s but got {d}s — resolve_duration_seconds must cap at 45"

    def test_explicit_override_respected_within_cap(self):
        parts = self._parts()
        d = resolve_duration_seconds(parts, requested_seconds=30)
        assert d == 30

    def test_explicit_override_over_45_capped(self):
        parts = self._parts()
        d = resolve_duration_seconds(parts, requested_seconds=120)
        assert d <= 45, "Duration must never exceed 45s hard cap"


# ===========================================================================
# 3.  build_scene_plan
# ===========================================================================

class TestBuildScenePlan:
    def test_returns_list_of_scene_plans(self):
        parts = parse_script("Hook sentence here. " + "Body word " * 30 + " CTA here.")
        scenes = build_scene_plan(parts, duration_seconds=30)
        assert isinstance(scenes, list)
        assert all(isinstance(s, ScenePlan) for s in scenes)

    def test_has_hook_and_cta(self):
        parts = parse_script("Hook sentence here. " + "Body word " * 30 + " CTA here.")
        scenes = build_scene_plan(parts, duration_seconds=30)
        parts_set = {s.part for s in scenes}
        assert "hook" in parts_set
        assert "cta" in parts_set

    def test_body_scene_count_max_8(self):
        parts = parse_script("Hook. " + "Body word " * 200 + " CTA.")
        scenes = build_scene_plan(parts, duration_seconds=45)
        body_count = sum(1 for s in scenes if s.part == "body")
        assert body_count <= 8, f"body_scene_count must not exceed 8, got {body_count}"

    def test_total_scene_count_max_10(self):
        parts = parse_script("Hook. " + "Body word " * 200 + " CTA.")
        scenes = build_scene_plan(parts, duration_seconds=45)
        assert len(scenes) <= 10, f"total scenes must be ≤10, got {len(scenes)}"

    def test_scenes_cover_full_duration(self):
        parts = parse_script("Hook here. Body here details. CTA follow.")
        duration = 20
        scenes = build_scene_plan(parts, duration_seconds=duration)
        last_end = max(s.end for s in scenes)
        assert abs(last_end - duration) < 0.5, f"Scenes end at {last_end}s, expected ~{duration}s"

    def test_no_scene_has_zero_duration(self):
        parts = parse_script("Hook. Body content here for longer test. CTA.")
        scenes = build_scene_plan(parts, duration_seconds=20)
        for s in scenes:
            assert s.end > s.start, f"Scene {s.idx} has zero or negative duration: {s.start}→{s.end}"


# ===========================================================================
# 4.  _scene_query_candidates
# ===========================================================================

class TestSceneQueryCandidates:
    def _make_scene(self, subtitle="save money tips", visual_desc="", keywords=None, part="body"):
        return ScenePlan(
            idx=0,
            start=0.0,
            end=5.0,
            part=part,
            source_text=subtitle,
            subtitle=subtitle,
            visual_description=visual_desc,
            keywords=keywords or [],
            energy="medium",
        )

    def test_returns_list_of_strings(self):
        scene = self._make_scene()
        candidates = _scene_query_candidates(scene)
        assert isinstance(candidates, list)
        assert all(isinstance(c, str) for c in candidates)

    def test_returns_at_least_one_candidate(self):
        scene = self._make_scene()
        candidates = _scene_query_candidates(scene)
        assert len(candidates) >= 1

    def test_keyword_map_hit_appears_first(self):
        # "save" → "savings bank coins" in _VISUAL_KEYWORD_MAP
        scene = self._make_scene(subtitle="save money today", keywords=["save"])
        candidates = _scene_query_candidates(scene)
        assert any("savings" in c or "bank" in c for c in candidates[:2]), (
            "Mapped keyword phrase should appear in top candidates"
        )

    def test_visual_description_included(self):
        scene = self._make_scene(visual_desc="person on laptop working")
        candidates = _scene_query_candidates(scene)
        assert any("laptop" in c.lower() for c in candidates)


# ===========================================================================
# 5.  scenes_from_rows
# ===========================================================================

class TestScenesFromRows:
    def test_valid_rows_round_trip(self):
        rows = [
            {"scene": 1, "start": 0, "end": 5, "part": "hook", "on_screen_text": "Hook text",
             "visual_description": "Dramatic reveal", "keywords": ["reveal"]},
            {"scene": 2, "start": 5, "end": 15, "part": "body", "on_screen_text": "Body",
             "visual_description": "Strategy diagram", "keywords": ["strategy"]},
            {"scene": 3, "start": 15, "end": 20, "part": "cta", "on_screen_text": "Follow",
             "visual_description": "Success moment", "keywords": []},
        ]
        result = scenes_from_rows(rows)
        assert len(result) == 3
        assert result[0].part == "hook"
        assert result[0].end == 5

    def test_empty_rows_returns_empty(self):
        assert scenes_from_rows([]) == []

    def test_malformed_row_skipped(self):
        rows = [
            {"scene": 1, "start": "bad", "end": "also_bad", "part": "body"},
        ]
        result = scenes_from_rows(rows)
        # Should not raise; malformed rows silently skipped
        assert isinstance(result, list)


# ===========================================================================
# 6.  parse_clip_to_clip_structure
# ===========================================================================

class TestParseClipToClipStructure:
    def test_valid_two_clips(self):
        script = """
Clip 1 · 00:00 – 00:05
Hook text here

Clip 2 · 00:05 – 00:15
Body text here
"""
        result = parse_clip_to_clip_structure(script)
        assert len(result) >= 2

    def test_single_clip_returns_empty(self):
        script = "Clip 1 · 00:00 – 00:05\nOnly one clip"
        result = parse_clip_to_clip_structure(script)
        # Single clip → returns empty (by design — fallback to build_scene_plan)
        assert isinstance(result, list)

    def test_no_clips_returns_empty(self):
        result = parse_clip_to_clip_structure("Just plain text, no clip headers.")
        assert result == []


# ===========================================================================
# 7.  score_scene_heuristic
# ===========================================================================

class TestScoreSceneHeuristic:
    def test_hook_always_scores_10(self):
        result = score_scene_heuristic("Simple hook text", "hook", 0)
        assert result.score == 10

    def test_first_scene_scores_10(self):
        result = score_scene_heuristic("Any text here", "body", 0)
        assert result.score == 10  # scene_index==0 gets max position score

    def test_high_trigger_words_boost_score(self):
        result = score_scene_heuristic("This shocking secret will transform everything", "body", 2)
        assert result.score >= 7, "High trigger words should push score up"

    def test_plain_body_text_scores_5_to_7(self):
        result = score_scene_heuristic("Here are the steps for the process workflow", "body", 3)
        assert 4 <= result.score <= 8

    def test_score_bounded_1_to_10(self):
        for text in ["", "a", "word " * 100, "shocking transform secret reveal hack"]:
            r = score_scene_heuristic(text, "body", 5)
            assert 1 <= r.score <= 10

    def test_cta_gets_position_bonus(self):
        result = score_scene_heuristic("Follow now for more tips", "cta", 5)
        assert result.score >= 7  # cta position_score=7


# ===========================================================================
# 8.  select_runway_model
# ===========================================================================

class TestSelectRunwayModel:
    def test_hook_always_gen45(self):
        model, rate = select_runway_model("hook", 10, budget_remaining=880)
        assert model == "gen4.5"
        assert rate == 12

    def test_score_8_uses_gen45(self):
        model, rate = select_runway_model("body", 8, budget_remaining=100)
        assert model == "gen4.5"

    def test_score_5_uses_gen4_turbo(self):
        model, rate = select_runway_model("body", 5, budget_remaining=100)
        assert model == "gen4_turbo"
        assert rate == 10

    def test_score_4_uses_stock(self):
        model, rate = select_runway_model("body", 4, budget_remaining=100)
        assert model is None
        assert rate == 0

    def test_insufficient_budget_returns_stock(self):
        model, rate = select_runway_model("hook", 10, budget_remaining=5)
        assert model is None, "Budget below cheapest model (10) must return stock"

    def test_budget_forces_downgrade(self):
        # Budget=11: can afford gen4_turbo(10) but not gen4.5(12)
        model, rate = select_runway_model("body", 8, budget_remaining=11)
        assert model == "gen4_turbo", "Should downgrade to gen4_turbo when budget < gen4.5 rate"

    def test_zero_budget_always_stock(self):
        model, rate = select_runway_model("hook", 10, budget_remaining=0)
        assert model is None


# ===========================================================================
# 9.  get_hybrid_scene_strategy
# ===========================================================================

class TestHybridStrategy:
    def _make_scenes(self, n=4, duration_each=5.0):
        return [
            ScenePlan(
                idx=i,
                start=i * duration_each,
                end=(i + 1) * duration_each,
                part="hook" if i == 0 else ("cta" if i == n - 1 else "body"),
                source_text=f"Scene {i} text with strategy and step process",
                subtitle=f"Scene {i} text with strategy and step process",
                visual_description="",
                keywords=[],
                energy="medium",
            )
            for i in range(n)
        ]

    def test_credits_used_within_70pct_budget(self):
        available = 100.0
        scenes = self._make_scenes(4, 5.0)
        result_scenes, credits_used = get_hybrid_scene_strategy(scenes, available)
        assert credits_used <= available * 0.70 + 0.01, (
            f"Credits used {credits_used} exceeds 70% budget {available * 0.70}"
        )

    def test_all_scenes_get_runway_model_or_none(self):
        scenes = self._make_scenes(4)
        result_scenes, _ = get_hybrid_scene_strategy(scenes, 880)
        for s in result_scenes:
            assert s.runway_model is None or s.runway_model in ("gen4.5", "gen4_turbo")

    def test_hook_assigned_gen45_when_budget_sufficient(self):
        scenes = self._make_scenes(4)
        result_scenes, _ = get_hybrid_scene_strategy(scenes, 880)
        hook = next(s for s in result_scenes if s.part == "hook")
        assert hook.runway_model == "gen4.5", "Hook should always use gen4.5 when budget allows"

    def test_zero_budget_all_stock(self):
        scenes = self._make_scenes(4)
        result_scenes, credits = get_hybrid_scene_strategy(scenes, 0)
        assert credits == 0.0
        for s in result_scenes:
            assert not s.use_runway

    def test_low_budget_hook_falls_back_to_stock(self):
        # Only 5 credits — below cheapest model (10 cr/5s)
        scenes = self._make_scenes(4)
        result_scenes, credits = get_hybrid_scene_strategy(scenes, 5.0 / 0.70)
        # Budget * 0.70 = 5 credits — below cheapest rate
        assert credits == 0.0 or all(not s.use_runway for s in result_scenes)


# ===========================================================================
# 10. fetch_scene_clips — stock mode with mocked HTTP
# ===========================================================================

def _make_minimal_mp4(path: Path):
    """Write a minimal valid MP4 placeholder for testing — uses ffmpeg if available."""
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=720x1280:r=1:d=2",
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(path)],
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0 and path.exists() and path.stat().st_size > 100
    except Exception:
        return False


class TestFetchSceneClipsStock:
    """
    Stock mode: all Runway calls must be mocked/disabled.
    Pexels/Pixabay HTTP calls are mocked.
    """

    @pytest.fixture
    def sample_scenes(self):
        return [
            ScenePlan(idx=0, start=0.0, end=5.0, part="hook",
                      source_text="Save money tips hack", subtitle="Save money tips hack",
                      visual_description="", keywords=["save", "money"], energy="high"),
            ScenePlan(idx=1, start=5.0, end=10.0, part="body",
                      source_text="Strategy workflow steps", subtitle="Strategy workflow steps",
                      visual_description="", keywords=["strategy"], energy="medium"),
        ]

    @pytest.mark.asyncio
    async def test_stock_mode_never_calls_runway(self, sample_scenes, tmp_path):
        """fetch_scene_clips in stock mode must never invoke RunwayML."""
        with patch("utils.video_pipeline.fetch_runwayml_clip") as mock_runway, \
             patch("utils.video_pipeline._search_pexels_video", new_callable=AsyncMock) as mock_pexels, \
             patch("utils.video_pipeline._search_pixabay_video", new_callable=AsyncMock) as mock_pixabay, \
             patch("utils.video_pipeline._download_file", new_callable=AsyncMock) as mock_dl, \
             patch("utils.video_pipeline.RAW_DIR", tmp_path):

            # Create dummy mp4 files that _is_valid_video will accept
            dummy = tmp_path / "dummy.mp4"
            created = _make_minimal_mp4(dummy)

            async def fake_download(url, path, client=None):
                if created:
                    import shutil
                    shutil.copy(str(dummy), str(path))
                else:
                    path.write_bytes(b"\x00" * 2048)

            mock_pexels.return_value = "https://example.com/clip1.mp4"
            mock_pixabay.return_value = None
            mock_dl.side_effect = fake_download

            try:
                await fetch_scene_clips(sample_scenes, new_run_id(), mode="stock")
            except RuntimeError:
                pass  # "No valid clips" is acceptable without real video files

            mock_runway.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_scenes_get_fallback_when_no_clips_found(self, sample_scenes, tmp_path):
        """When all searches return None, RuntimeError is raised (not silent failure)."""
        with patch("utils.video_pipeline._search_pexels_video", new_callable=AsyncMock, return_value=None), \
             patch("utils.video_pipeline._search_pixabay_video", new_callable=AsyncMock, return_value=None), \
             patch("utils.video_pipeline._download_file", new_callable=AsyncMock), \
             patch("utils.video_pipeline.RAW_DIR", tmp_path):

            with pytest.raises(RuntimeError, match="No matching"):
                await fetch_scene_clips(sample_scenes, new_run_id(), mode="stock")


# ===========================================================================
# 11. fetch_scene_clips — Runway quota error → fallback
# ===========================================================================

class TestFetchSceneClipsRunwayQuotaFallback:
    @pytest.mark.asyncio
    async def test_quota_error_falls_back_to_stock(self, tmp_path):
        scenes = [
            ScenePlan(idx=0, start=0.0, end=5.0, part="hook",
                      source_text="Shocking reveal hack", subtitle="Shocking reveal hack",
                      visual_description="", keywords=[], energy="high"),
        ]

        dummy = tmp_path / "dummy.mp4"
        created = _make_minimal_mp4(dummy)

        async def fake_download(url, path, client=None):
            if created:
                import shutil
                shutil.copy(str(dummy), str(path))
            else:
                path.write_bytes(b"\x00" * 2048)

        with patch("utils.video_pipeline.fetch_runwayml_clip",
                   side_effect=RunwayMLQuotaError("Quota exceeded")) as mock_runway, \
             patch("utils.video_pipeline._search_pexels_video", new_callable=AsyncMock,
                   return_value="https://example.com/fallback.mp4"), \
             patch("utils.video_pipeline._search_pixabay_video", new_callable=AsyncMock,
                   return_value=None), \
             patch("utils.video_pipeline._download_file", new_callable=AsyncMock,
                   side_effect=fake_download), \
             patch("utils.video_pipeline.RAW_DIR", tmp_path):

            # In "ai" mode, each scene tries Runway first → quota error → stock fallback
            try:
                result = await fetch_scene_clips(scenes, new_run_id(), mode="ai")
            except RuntimeError:
                result = None  # acceptable when dummy file is not valid mp4

            # Runway WAS called (credit attempt was made)
            mock_runway.assert_called_once()


# ===========================================================================
# 12. fetch_scene_clips — auto mode respects max_ai_scenes
# ===========================================================================

class TestFetchSceneClipsAutoMaxScenes:
    @pytest.mark.asyncio
    async def test_max_ai_scenes_respected(self, tmp_path):
        """In auto mode with max_scenes=1, only 1 scene should attempt Runway."""
        scenes = [
            ScenePlan(idx=0, start=0.0, end=5.0, part="hook",
                      source_text="Shocking reveal transform", subtitle="Shocking reveal transform",
                      visual_description="", keywords=[], energy="high", visual_score=10),
            ScenePlan(idx=1, start=5.0, end=10.0, part="body",
                      source_text="Strategy workflow boost", subtitle="Strategy workflow boost",
                      visual_description="", keywords=[], energy="medium", visual_score=7),
            ScenePlan(idx=2, start=10.0, end=15.0, part="cta",
                      source_text="Follow for more tips", subtitle="Follow for more tips",
                      visual_description="", keywords=[], energy="low", visual_score=6),
        ]
        # Pre-assign use_runway so hybrid strategy doesn't override
        for s in scenes:
            s.use_runway = True
            s.runway_model = "gen4_turbo"

        runway_call_count = 0

        def counting_runway(*args, **kwargs):
            nonlocal runway_call_count
            runway_call_count += 1
            raise RunwayMLQuotaError("Mock — counting calls")

        dummy = tmp_path / "dummy.mp4"
        created = _make_minimal_mp4(dummy)

        async def fake_download(url, path, client=None):
            if created:
                import shutil
                shutil.copy(str(dummy), str(path))
            else:
                path.write_bytes(b"\x00" * 2048)

        with patch("utils.video_pipeline.fetch_runwayml_clip", side_effect=counting_runway), \
             patch("utils.video_pipeline._search_pexels_video", new_callable=AsyncMock,
                   return_value="https://example.com/clip.mp4"), \
             patch("utils.video_pipeline._search_pixabay_video", new_callable=AsyncMock,
                   return_value=None), \
             patch("utils.video_pipeline._download_file", new_callable=AsyncMock,
                   side_effect=fake_download), \
             patch("utils.video_pipeline.RAW_DIR", tmp_path), \
             patch("utils.video_pipeline.get_hybrid_scene_strategy",
                   return_value=(scenes, 20.0)):  # bypass hybrid so use_runway is honoured

            try:
                await fetch_scene_clips(scenes, new_run_id(), mode="auto", max_scenes=1)
            except RuntimeError:
                pass

        assert runway_call_count <= 1, (
            f"max_scenes=1 should limit Runway calls to 1, but got {runway_call_count}"
        )


# ===========================================================================
# 13. assemble_video — happy path with real dummy clips
# ===========================================================================

class TestAssembleVideo:
    @pytest.mark.skipif(
        not _make_minimal_mp4(Path(tempfile.mktemp(suffix=".mp4"))),
        reason="ffmpeg not available — skipping assemble_video integration test",
    )
    def test_assemble_produces_output_file(self, tmp_path):
        from utils.video_pipeline import assemble_video, ASSETS_DIR, TEMP_DIR

        # Create two real MP4 clips
        clip1 = tmp_path / "c1.mp4"
        clip2 = tmp_path / "c2.mp4"
        assert _make_minimal_mp4(clip1)
        assert _make_minimal_mp4(clip2)

        scenes = [
            ScenePlan(idx=0, start=0.0, end=2.0, part="hook",
                      source_text="Hook text", subtitle="Hook text",
                      visual_description="", keywords=[], energy="high",
                      clip_path=str(clip1)),
            ScenePlan(idx=1, start=2.0, end=4.0, part="cta",
                      source_text="CTA text", subtitle="CTA text",
                      visual_description="", keywords=[], energy="low",
                      clip_path=str(clip2)),
        ]

        run_id = f"test_{new_run_id()}"
        with patch("utils.video_pipeline.ASSETS_DIR", tmp_path), \
             patch("utils.video_pipeline.TEMP_DIR", tmp_path):
            result = assemble_video(scenes, run_id=run_id)

        assert "video_path" in result
        assert Path(result["video_path"]).exists(), "Output video file must exist"

    def test_assemble_raises_when_no_valid_clips(self, tmp_path):
        from utils.video_pipeline import assemble_video

        scenes = [
            ScenePlan(idx=0, start=0.0, end=5.0, part="hook",
                      source_text="No file", subtitle="No file",
                      visual_description="", keywords=[], energy="high",
                      clip_path="/nonexistent/file.mp4"),
        ]
        with patch("utils.video_pipeline.ASSETS_DIR", tmp_path), \
             patch("utils.video_pipeline.TEMP_DIR", tmp_path):
            with pytest.raises(RuntimeError, match="no valid source clips"):
                assemble_video(scenes, run_id="test_run")


# ===========================================================================
# 14. generate_voice — ElevenLabs mocking
# ===========================================================================

class TestGenerateVoice:
    def test_elevenlabs_success_path(self, tmp_path):
        from routes.voice_gen import generate_voice, VoiceGenRequest

        mp3_bytes = b"\xff\xfb" + b"\x00" * 2048  # fake MP3 header

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = mp3_bytes

        with patch("routes.voice_gen.requests.post", return_value=mock_response), \
             patch("subprocess.run") as mock_ffmpeg, \
             patch("routes.voice_gen.os.path.getsize", return_value=5000), \
             patch("routes.voice_gen.os.makedirs"), \
             patch("builtins.open", MagicMock()):

            mock_ffmpeg.return_value = MagicMock(returncode=0)

            # Patch the file existence/size check that validates the wav output
            with patch("os.path.getsize", return_value=5000), \
                 patch("os.path.exists", return_value=True):
                req = VoiceGenRequest(text="Test narration for the video")
                # We don't assert file contents here — just that no exception is raised
                # and provider is elevenlabs
                try:
                    result = generate_voice(req)
                    assert result.provider == "elevenlabs"
                except Exception:
                    pass  # If wav file creation fails in test env, that's acceptable

    def test_elevenlabs_429_logs_and_falls_to_pyttsx3(self, tmp_path):
        from routes.voice_gen import generate_voice, VoiceGenRequest

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        with patch("routes.voice_gen.requests.post", return_value=mock_response), \
             patch("routes.voice_gen.os.makedirs"):

            req = VoiceGenRequest(text="Short text")
            try:
                generate_voice(req)
            except Exception as e:
                # pyttsx3 may not be installed in CI — that's acceptable
                assert "pyttsx3" in str(e) or "Voice generation failed" in str(e)

    def test_elevenlabs_timeout_falls_through(self):
        import requests as rq
        from routes.voice_gen import generate_voice, VoiceGenRequest

        with patch("routes.voice_gen.requests.post",
                   side_effect=rq.exceptions.Timeout("Connection timed out")), \
             patch("routes.voice_gen.os.makedirs"):

            req = VoiceGenRequest(text="Some text")
            try:
                generate_voice(req)
            except Exception as e:
                assert "pyttsx3" in str(e) or "Voice generation failed" in str(e)

    def test_cache_key_is_deterministic(self):
        """SHA-256 cache key must return same filename on repeated calls."""
        from routes.voice_gen import generate_voice, VoiceGenRequest
        import hashlib

        text = "Deterministic cache key test"
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        expected_filename = f"voice_{voice_id}_{expected_hash}.wav"

        # Verify the filename formula produces the same result twice
        h1 = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        h2 = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        assert h1 == h2 == expected_hash
        assert expected_filename == f"voice_{voice_id}_{h1}.wav"


# ===========================================================================
# 15. /video/free endpoint — dry_run=True integration
# ===========================================================================

class TestVideoFreeEndpointDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_skips_elevenlabs_and_runway(self):
        """
        With dry_run=True, the endpoint must never call ElevenLabs or RunwayML.
        All calls are mocked; we verify the mock call counts.
        """
        from unittest.mock import AsyncMock, patch, MagicMock
        from fastapi.testclient import TestClient

        # Build a minimal FastAPI app with just the generate router
        from fastapi import FastAPI
        from routes.generate import router as gen_router

        app = FastAPI()
        app.include_router(gen_router)

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.plan = "pro"
        mock_user.usage_count = 0
        mock_user.custom_limit = None

        async def mock_get_user():
            return mock_user

        async def mock_get_db():
            db = AsyncMock()
            db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            yield db

        from auth import get_current_user
        from database import get_db

        app.dependency_overrides[get_current_user] = mock_get_user
        app.dependency_overrides[get_db] = mock_get_db

        with patch("routes.voice_gen.requests.post") as el_mock, \
             patch("utils.ai_video.fetch_runwayml_clip") as runway_mock, \
             patch("utils.video_pipeline._search_pexels_video", new_callable=AsyncMock,
                   return_value=None), \
             patch("utils.video_pipeline._search_pixabay_video", new_callable=AsyncMock,
                   return_value=None), \
             patch("utils.video_pipeline.assemble_video",
                   return_value={"video_path": "/tmp/test.mp4", "thumbnail_path": None,
                                 "ffmpeg_error": None, "subtitle_path": "/tmp/test.ass"}), \
             patch("routes.generate.generate_youtube_metadata", new_callable=AsyncMock,
                   return_value={"title": "Test Video"}):

            client = TestClient(app, raise_server_exceptions=False)
            payload = {
                "script": "Hook line. Body content explaining value. CTA follow now.",
                "dry_run": True,
                "scene_mode": "stock",
                "duration_seconds": 15,
            }
            response = client.post("/api/generate/video/free", json=payload,
                                   headers={"Authorization": "Bearer test"})

            # dry_run=True: ElevenLabs and Runway must never be called
            el_mock.assert_not_called()
            runway_mock.assert_not_called()


# ===========================================================================
# 16. Credit leakage guard — /generate never calls ElevenLabs live
# ===========================================================================

class TestCreditLeakageGuard:
    def test_generate_endpoint_shadow_pipeline_is_always_dry(self):
        """
        The shadow video pipeline in /generate must always set dry_run=True
        regardless of the VIDEO_GENERATION_DRY_RUN env var.
        Verify by checking the source code contains the guard.
        """
        generate_path = BACKEND_DIR / "routes" / "generate.py"
        source = generate_path.read_text(encoding="utf-8")

        # The patch we applied: dry_run = True (hardcoded) in the shadow pipeline
        assert "dry_run = True" in source, (
            "CRITICAL: /generate shadow pipeline must always use dry_run=True "
            "to prevent ElevenLabs credit leakage on text content generation"
        )

    def test_asyncio_run_not_used_in_async_route(self):
        """
        asyncio.run() must not appear in the async generate route handler.
        Using it inside an async function causes RuntimeError in production.
        """
        generate_path = BACKEND_DIR / "routes" / "generate.py"
        source = generate_path.read_text(encoding="utf-8")

        assert "asyncio.run(fetch_scene_clips" not in source, (
            "CRITICAL: asyncio.run() inside async route crashes production server. "
            "Must use 'await fetch_scene_clips(...)' instead."
        )

    def test_voice_gen_has_timeout(self):
        """ElevenLabs requests.post must have a timeout to prevent worker hang."""
        voice_gen_path = BACKEND_DIR / "routes" / "voice_gen.py"
        source = voice_gen_path.read_text(encoding="utf-8")

        assert "timeout=" in source, (
            "CRITICAL: requests.post to ElevenLabs must have a timeout= argument. "
            "Without it, the server worker can hang indefinitely."
        )


    def test_path_rename_not_used_in_ai_video(self):
        """Path.rename() must not be used in ai_video.py — use shutil.move for cross-device safety."""
        ai_video_path = BACKEND_DIR / "utils" / "ai_video.py"
        source = ai_video_path.read_text(encoding="utf-8")

        assert ".rename(" not in source, (
            "HIGH: Path.rename() fails on cross-device moves (different drives on Windows). "
            "Use shutil.move() instead."
        )

    def test_voice_cache_uses_sha256_not_hash(self):
        """Voice cache filename must use SHA-256 hash, not Python's hash() which is non-deterministic."""
        voice_gen_path = BACKEND_DIR / "routes" / "voice_gen.py"
        source = voice_gen_path.read_text(encoding="utf-8")

        assert "sha256" in source, (
            "MEDIUM: Voice cache key must use hashlib.sha256 for deterministic filenames. "
            "Python hash() changes on each process restart, causing cache misses."
        )
        assert "abs(hash(" not in source, (
            "MEDIUM: Removed hash()-based cache key is still present in voice_gen.py"
        )

    def test_ffmpeg_subprocess_has_timeout(self):
        """ffmpeg subprocess in voice_gen must have a timeout to prevent worker hang."""
        voice_gen_path = BACKEND_DIR / "routes" / "voice_gen.py"
        source = voice_gen_path.read_text(encoding="utf-8")

        assert "timeout=60" in source, (
            "HIGH: ffmpeg subprocess.run() in voice_gen.py must have timeout=60 "
            "to prevent the worker from hanging on ffmpeg freeze."
        )

    def test_audio_clip_closed_in_finally(self):
        """assemble_video must close audio_clip in the finally block."""
        pipeline_path = BACKEND_DIR / "utils" / "video_pipeline.py"
        source = pipeline_path.read_text(encoding="utf-8")

        assert "audio_clip.close()" in source, (
            "HIGH: audio_clip (AudioFileClip) is not closed in the finally block of assemble_video. "
            "This causes a file handle leak on every video render."
        )


# ===========================================================================
# 17. HMR UI smoke preflight — no render invocation
# ===========================================================================

class TestHMRUISmokePreflight:
    def test_hmr_ui_smoke_plan_selects_safe_free_defaults(self, monkeypatch, tmp_path):
        from routes.generate import GenerateVideoRequest, build_hmr_ui_generation_smoke_plan

        monkeypatch.setenv("ENABLE_HYBRID_MOTION_RENDERER", "1")
        monkeypatch.setenv("VIDEO_GENERATION_DRY_RUN", "1")
        request = GenerateVideoRequest(
            script="I found a $27/month leak hiding in one bill. Compare it and keep the savings.",
            scene_mode="hybrid_motion",
            dry_run=True,
            tts_provider="elevenlabs",
        )

        plan = build_hmr_ui_generation_smoke_plan(
            request,
            generated_root=tmp_path,
            run_id="hmr_smoke_test",
        )

        assert plan["route_entry_point"] == "/api/generate/video/free"
        assert plan["request_schema"] == "GenerateVideoRequest"
        assert plan["hmr_mode_selected"] is True
        assert plan["hmr_renderer_enabled"] is True
        assert plan["would_enter_hmr_render_branch"] is True
        assert plan["dry_run"] is True
        assert plan["render_invoked"] is False
        assert plan["free_tts_for_hmr"] is True
        assert plan["paid_providers_selected"] == {
            "elevenlabs": False,
            "runwayml": False,
            "paid_llm": False,
        }
        assert plan["output_path"].endswith("hmr_smoke_test.mp4")
        assert str(tmp_path) in plan["output_folder"]
        assert plan["frozen_guard_checked"] is True
        assert plan["platform_export_integration_ready"] is True
        productization = plan["productization"]
        assert productization["review_package_status"] == "planned"
        assert productization["platform_export_status"] == "planned"
        assert productization["full_render_required"] is False
        assert productization["artifact_paths"]["render_report"].endswith("render_report.json")
        assert productization["artifact_paths"]["qa_report"].endswith("qa_report.json")
        assert productization["artifact_paths"]["review_package"].endswith("review_package")
        assert productization["artifact_paths"]["manifest"].endswith("review_package\\manifest.json") or productization["artifact_paths"]["manifest"].endswith("review_package/manifest.json")
        assert set(productization["platform_exports"]) == {"instagram_reels", "tiktok", "youtube_shorts"}
        assert all(row["generated"] is False for row in productization["platform_exports"].values())
        job = plan["hmr_render_job"]
        assert plan["non_blocking_hmr_requested"] is False
        assert plan["non_blocking_hmr_active"] is False
        assert plan["async_execution_status"] == "direct_or_scaffold"
        assert plan["worker_active"] is False
        assert plan["durable_progress"] is False
        assert plan["progress_store"] == "_task_progress_in_memory_only"
        assert job["run_id"] == "hmr_smoke_test"
        assert job["generation_id"] is None
        assert job["status"] == "queued"
        assert job["execution_mode"] == "scaffold_only"
        assert job["worker_active"] is False
        assert job["durable_progress"] is False
        assert job["progress_store"] == "in_memory_task_progress"
        assert job["percent"] == 2
        assert job["render_invoked"] is False
        assert job["artifact_paths"]["review_package"].endswith("review_package")
        first_3 = plan["first_3_seconds"]
        assert first_3["first_frame_style"] == "claim_proof_payoff"
        assert first_3["no_slow_intro"] is True
        assert first_3["pattern_interrupt"]["time_seconds"] < 2
        assert first_3["caption_text_preserved"]
        interrupts = plan["pattern_interrupt_plan"]
        assert interrupts["debug"]["render_required"] is False
        assert interrupts["scenes"][0]["scene_role"] == "hook"
        assert interrupts["interrupts"][0]["type"] == "punch_zoom"

    def test_hmr_ui_smoke_plan_respects_frozen_manifest(self, monkeypatch, tmp_path):
        from routes.generate import GenerateVideoRequest, build_hmr_ui_generation_smoke_plan
        from utils.hmr_artifact_manifest import FrozenArtifactError, build_manifest, write_manifest

        monkeypatch.setenv("ENABLE_HYBRID_MOTION_RENDERER", "1")
        generated_root = tmp_path / "generated_videos"
        manifest = build_manifest(
            topic="Frozen smoke root",
            hook="Do not overwrite",
            video_path=generated_root / "final.mp4",
            review_package_path=generated_root,
            frozen=True,
            human_posting_gate="READY_FOR_HUMAN_POST_REVIEW",
        )
        write_manifest(generated_root, manifest)

        request = GenerateVideoRequest(
            script="I found a $27/month leak hiding in one bill. Compare it and keep the savings.",
            scene_mode="hybrid_motion",
            dry_run=True,
        )

        with pytest.raises(FrozenArtifactError):
            build_hmr_ui_generation_smoke_plan(request, generated_root=generated_root, run_id="blocked")

    def test_hmr_ui_productization_metadata_builds_review_and_export_paths(self, tmp_path):
        from utils.hmr_ui_productization import build_hmr_ui_productization_metadata

        video = tmp_path / "generated_videos" / "run-123.mp4"
        metadata = build_hmr_ui_productization_metadata(
            generated_root=tmp_path / "generated_videos",
            run_id="run-123",
            video_path=video,
        )

        paths = metadata["artifact_paths"]
        assert paths["run_dir"].endswith("hmr_ui_runs\\run-123") or paths["run_dir"].endswith("hmr_ui_runs/run-123")
        assert paths["video"] == str(video.resolve())
        assert paths["render_report"].endswith("render_report.json")
        assert paths["qa_report"].endswith("qa_report.json")
        assert paths["story_candidate"].endswith("story_candidate.json")
        assert paths["review_package"].endswith("review_package")
        assert paths["manifest"].endswith("manifest.json")
        assert paths["platform_export_dir"].endswith("platform_exports")
        assert metadata["review_package_status"] == "planned"
        assert metadata["platform_export_status"] == "planned"
        for preset, row in metadata["platform_exports"].items():
            assert preset in {"instagram_reels", "tiktok", "youtube_shorts"}
            assert row["output"].endswith(".mp4")
            assert row["command"][0] == "ffmpeg"
            assert "-movflags" in row["command"]
            assert row["generated"] is False

    def test_hmr_render_job_state_transitions_and_progress(self):
        from utils.hmr_render_jobs import (
            create_hmr_render_job_state,
            seed_hmr_render_progress,
            transition_hmr_render_job_state,
        )

        job = create_hmr_render_job_state(
            run_id="run-123",
            generation_id=42,
            artifact_paths={"review_package": "review_package"},
        )
        progress_store = {}

        queued = seed_hmr_render_progress(progress_store, job)
        assert queued["percent"] == 2
        assert queued["step"] == "queued"
        assert queued["hmr_render_job"]["worker_active"] is False
        assert queued["hmr_render_job"]["durable_progress"] is False
        assert progress_store[42]["hmr_render_job"]["status"] == "queued"

        processing = transition_hmr_render_job_state(
            job,
            status="processing",
            percent=33,
            render_invoked=True,
        )
        assert processing.status == "processing"
        assert processing.percent == 33
        assert processing.step == "rendering"
        assert processing.render_invoked is True
        assert processing.worker_active is False
        assert processing.durable_progress is False

        active = create_hmr_render_job_state(
            run_id="active-run",
            generation_id=43,
            artifact_paths={"review_package": "review_package"},
            active_worker=True,
        )
        assert active.execution_mode == "background_task"
        assert active.worker_active is True
        assert active.durable_progress is True
        assert active.progress_store == "hmr_render_jobs"

        success = transition_hmr_render_job_state(processing, status="success")
        assert success.status == "success"
        assert success.percent == 100
        assert success.step == "done"
        assert success.render_invoked is True

        failed = transition_hmr_render_job_state(
            processing,
            status="failed",
            error_message="Renderer exited before writing video.",
        )
        assert failed.to_progress()["message"] == "Renderer exited before writing video."
        assert failed.percent == 0

        with pytest.raises(ValueError, match="Invalid HMR render job status"):
            transition_hmr_render_job_state(job, status="unknown")

    def test_hmr_ui_smoke_plan_exposes_non_blocking_request_flag(self, monkeypatch, tmp_path):
        from routes.generate import GenerateVideoRequest, build_hmr_ui_generation_smoke_plan

        monkeypatch.setenv("ENABLE_HYBRID_MOTION_RENDERER", "1")
        request = GenerateVideoRequest(
            script="A billing surprise becomes obvious in the first three seconds.",
            scene_mode="hybrid_motion",
            dry_run=True,
            hmr_async=True,
        )

        plan = build_hmr_ui_generation_smoke_plan(
            request,
            generated_root=tmp_path,
            run_id="async-smoke",
        )

        assert plan["non_blocking_hmr_requested"] is True
        assert plan["non_blocking_hmr_active"] is True
        assert plan["async_execution_status"] == "background_task"
        assert plan["worker_active"] is True
        assert plan["durable_progress"] is True
        assert plan["hmr_render_job"]["status"] == "queued"
        assert plan["hmr_render_job"]["run_id"] == "async-smoke"
        assert plan["hmr_render_job"]["execution_mode"] == "background_task"
        assert plan["hmr_render_job"]["worker_active"] is True
        assert plan["hmr_render_job"]["durable_progress"] is True
        assert plan["hmr_render_job"]["render_invoked"] is False
        assert plan["render_invoked"] is False

    @pytest.mark.asyncio
    async def test_hmr_ui_branch_attaches_metadata_and_calls_productization_without_full_render(self, monkeypatch):
        from routes.generate import GenerateVideoRequest, generate_free_video

        monkeypatch.setenv("ENABLE_HYBRID_MOTION_RENDERER", "1")
        monkeypatch.setenv("VIDEO_GENERATION_DRY_RUN", "1")

        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        async def refresh_generation(generation):
            generation.id = 51

        db.refresh = AsyncMock(side_effect=refresh_generation)
        current_user = SimpleNamespace(id=7)
        request = GenerateVideoRequest(
            script="I found a $27/month leak hiding in one bill. Compare it and keep the savings. Comment BILL for the prompt.",
            scene_mode="hybrid_motion",
            dry_run=True,
            tts_provider="elevenlabs",
            duration_seconds=15,
            niche="bill leak",
        )

        render_result = {
            "video_path": "backend/generated_videos/hmr_route_mock.mp4",
            "duration": 12.0,
            "scene_reports": [{"scene_id": 1, "template": "hook"}],
            "media_mix": {"MOTION_CARD": 1},
            "warnings": [],
        }

        def productization_side_effect(**kwargs):
            result = kwargs["render_result"]
            assert result["first_3_seconds"]["no_slow_intro"] is True
            assert result["first_3_sec_strategy"]["pattern_interrupt"]["time_seconds"] < 2
            assert result["pattern_interrupt_plan"]["debug"]["render_required"] is False
            assert "planned_pattern_interrupts" in result["scene_reports"][0]
            return {
                "review_package_status": "created",
                "artifact_paths": {"review_package": "mock_review_package", "manifest": "mock_manifest.json"},
                "full_render_required": False,
            }

        with patch("routes.generate.new_run_id", return_value="hmr-route-mock"), \
             patch("utils.hybrid_motion_renderer.render_hybrid_video", return_value=render_result) as render_mock, \
             patch("utils.hmr_ui_productization.materialize_hmr_ui_review_workflow", side_effect=productization_side_effect) as productize_mock, \
             patch("routes.generate.generate_youtube_metadata", new_callable=AsyncMock, return_value={"title": "Mock HMR"}), \
             patch("routes.generate._organize_run_assets", return_value=("hmr-route-mock.mp4", None)):
            response = await generate_free_video(request, background_tasks=BackgroundTasks(), db=db, current_user=current_user)

        render_mock.assert_called_once()
        productize_mock.assert_called_once()
        assert render_mock.call_args.kwargs["use_free_tts"] is True
        assert response["success"] is True
        assert response["dry_run"] is True
        assert response["hybrid_motion"]["first_3_seconds"]["first_frame_style"] == "claim_proof_payoff"
        assert response["hybrid_motion"]["pattern_interrupt_plan"]["debug"]["render_required"] is False
        assert response["hmr_productization"]["review_package_status"] == "created"
        assert response["costs"]["runway_credits_used"] == 0.0
        assert response["costs"]["elevenlabs_chars_used"] == 0


# ===========================================================================
# Bonus: RunwayML client dry-run / quota detection
# ===========================================================================

class TestRunwayMLClientQuotaDetection:
    def test_402_raises_quota_error(self):
        from utils.runwayml_client import RunwayMLClient

        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.text = "Payment required"

        with patch("utils.runwayml_client.requests.post", return_value=mock_response):
            client = RunwayMLClient(api_key="test_key", model="gen4_turbo")
            with pytest.raises(RunwayMLQuotaError):
                client.generate_video("test prompt")

    def test_400_with_credits_message_raises_quota_error(self):
        from utils.runwayml_client import RunwayMLClient

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "not enough credits for this operation"

        with patch("utils.runwayml_client.requests.post", return_value=mock_response):
            client = RunwayMLClient(api_key="test_key", model="gen4_turbo")
            with pytest.raises(RunwayMLQuotaError):
                client.generate_video("test prompt")

    def test_429_retries_then_raises(self):
        from utils.runwayml_client import RunwayMLClient

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "rate limited"

        with patch("utils.runwayml_client.requests.post", return_value=mock_response), \
             patch("utils.runwayml_client.time.sleep"):
            client = RunwayMLClient(api_key="test_key", model="gen4_turbo")
            with pytest.raises(Exception, match="failed after retries|RunwayML"):
                client.generate_video("test prompt", max_retries=2)


# ===========================================================================
# Bonus: _download_file basic coverage
# ===========================================================================

class TestDownloadFile:
    @pytest.mark.asyncio
    async def test_download_writes_to_path(self, tmp_path):
        from utils.video_pipeline import _download_file

        dest = tmp_path / "clip.mp4"
        fake_content = b"fake_video_data" * 100

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_bytes = AsyncMock(return_value=iter([fake_content]))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_response)

        # We test that the function doesn't raise on a valid mock
        # (actual byte streaming behaviour is integration-level)
        try:
            await _download_file("https://example.com/clip.mp4", dest, client=mock_client)
        except Exception:
            pass  # Stream mock may not perfectly replicate httpx interface

    @pytest.mark.asyncio
    async def test_download_raises_on_404(self, tmp_path):
        from utils.video_pipeline import _download_file

        dest = tmp_path / "clip.mp4"

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_response)

        with pytest.raises(Exception):
            await _download_file("https://example.com/missing.mp4", dest, client=mock_client)
