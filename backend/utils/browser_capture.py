#!/usr/bin/env python3
"""
Day4 Real Browser Capture Engine - Trust Through Realism

Uses Playwright native video recording for local DOM workflow pages. Local pages
avoid login/captcha/private-data surfaces while still recording real browser
typing, clicks, scrolling, progress states, tab-like switches, and result reveals.
"""

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Dict, List

from playwright.async_api import Page, async_playwright

from .video_pipeline import RAW_DIR, TEMP_DIR


@dataclass
class BrowserCaptureConfig:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    fallback_fps: int = 12
    scene_duration: float = 3.8


class RealBrowserCapture:
    """Day4 browser capture engine using Playwright-recorded local DOM scenes."""

    SCENE_DESCRIPTIONS = {
        "scene1": "open_browser",
        "scene2": "ai_prompt",
        "scene3": "second_tab",
        "scene4": "calculator",
        "scene5": "export",
    }

    def __init__(self, config: BrowserCaptureConfig = None):
        self.config = config or BrowserCaptureConfig()
        self.playwright = None
        self.browser = None

    async def __aenter__(self):
        await self._setup_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup_browser()

    async def _setup_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                f"--window-size={self.config.width},{self.config.height}",
            ],
        )

    async def _cleanup_browser(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def generate_day4_real_capture(self, run_id: str) -> Dict[str, object]:
        results: Dict[str, object] = {
            "run_id": run_id,
            "real_capture_scenes": [],
            "dom_fallback_scenes": [],
            "videos": {},
            "logs": [],
            "scene_modes": {},
        }

        try:
            await self._setup_browser()
            scene_specs = [
                ("scene1", "open_browser", self._html_workspace(), self._action_workspace),
                ("scene2", "ai_prompt", self._html_ai_assistant(), self._action_ai_assistant),
                ("scene3", "second_tab", self._html_research_tabs(), self._action_research_tabs),
                ("scene4", "calculator", self._html_calculator(), self._action_calculator),
                ("scene5", "export", self._html_export(), self._action_export),
            ]

            for scene_key, description, html, action in scene_specs:
                path, mode, reason, frame_count = await self._record_scene(
                    run_id=run_id,
                    scene_key=scene_key,
                    description=description,
                    html=html,
                    action=action,
                )
                results["real_capture_scenes"].append(scene_key)
                results["scene_modes"][scene_key] = {
                    "mode": mode,
                    "reason": reason,
                    "path": path,
                    "frames": frame_count,
                }
                results["logs"].append(
                    f"{scene_key} mode={mode} reason={reason} path={path} frames={frame_count}"
                )

            results["videos"] = await self._assemble_final_videos(run_id, results)

        except Exception as exc:
            results["logs"].append(f"Error: {exc}")
            fallback_path = await self._generate_dom_fallback_video(run_id)
            results["videos"] = {"dom_fallback": fallback_path}

        finally:
            await self._cleanup_browser()

        return results

    async def _record_scene(
        self,
        run_id: str,
        scene_key: str,
        description: str,
        html: str,
        action: Callable[[Page], Awaitable[None]],
    ) -> tuple[str, str, str, int]:
        output_path = RAW_DIR / f"{run_id}_{scene_key}_{description}.mp4"
        video_dir = TEMP_DIR / f"{run_id}_{scene_key}_native_video"
        video_dir.mkdir(parents=True, exist_ok=True)
        context = None

        try:
            context = await self.browser.new_context(
                viewport={"width": self.config.width, "height": self.config.height},
                record_video_dir=str(video_dir),
                record_video_size={"width": self.config.width, "height": self.config.height},
            )
            page = await context.new_page()
            await page.set_content(html, wait_until="domcontentloaded")
            started = asyncio.get_event_loop().time()
            await action(page)
            elapsed = asyncio.get_event_loop().time() - started
            await asyncio.sleep(max(0.0, self.config.scene_duration - elapsed))
            video = page.video
            await page.close()
            raw_webm = Path(await video.path())
            await context.close()
            self._convert_clip(raw_webm, output_path, self.config.scene_duration, self.config.fps)
            frames = self._probe_frame_count(output_path)
            return str(output_path), "playwright_native_video", "local_dom_record_video_dir", frames
        except Exception as exc:
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
            path, frames = await self._record_scene_screenshot_sequence(
                scene_key=scene_key,
                output_path=output_path,
                html=html,
                action=action,
            )
            return path, "screenshot_sequence", f"native_video_failed:{exc}", frames
        finally:
            shutil.rmtree(video_dir, ignore_errors=True)

    async def _record_scene_screenshot_sequence(
        self,
        scene_key: str,
        output_path: Path,
        html: str,
        action: Callable[[Page], Awaitable[None]],
    ) -> tuple[str, int]:
        frame_dir = TEMP_DIR / f"{output_path.stem}_frames"
        shutil.rmtree(frame_dir, ignore_errors=True)
        frame_dir.mkdir(parents=True, exist_ok=True)
        context = await self.browser.new_context(
            viewport={"width": self.config.width, "height": self.config.height}
        )
        page = await context.new_page()
        await page.set_content(html, wait_until="domcontentloaded")
        action_task = asyncio.create_task(action(page))
        frame_count = int(self.config.scene_duration * self.config.fallback_fps)
        interval = 1.0 / self.config.fallback_fps
        for idx in range(frame_count):
            await page.screenshot(path=str(frame_dir / f"{scene_key}_{idx:04d}.png"), full_page=False)
            await asyncio.sleep(interval)
        await action_task
        await context.close()
        pattern = str(frame_dir / f"{scene_key}_%04d.png")
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(self.config.fallback_fps),
                "-i",
                pattern,
                "-t",
                f"{self.config.scene_duration:.2f}",
                "-vf",
                f"scale={self.config.width}:{self.config.height},fps={self.config.fps}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
        shutil.rmtree(frame_dir, ignore_errors=True)
        return str(output_path), self._probe_frame_count(output_path)

    def _convert_clip(self, src: Path, dst: Path, duration: float, fps: int) -> None:
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(src),
                "-t",
                f"{duration:.2f}",
                "-vf",
                (
                    f"scale={self.config.width}:{self.config.height}:"
                    f"force_original_aspect_ratio=increase,"
                    f"crop={self.config.width}:{self.config.height},fps={fps}"
                ),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(dst),
            ]
        )

    async def _assemble_final_videos(self, run_id: str, results: Dict[str, object]) -> Dict[str, str]:
        videos: Dict[str, str] = {}
        real_output = RAW_DIR / "day4_real_browser_capture_v3.mp4"
        fallback_output = RAW_DIR / "day4_playwright_dom_fallback_v3.mp4"

        scene_paths: List[str] = []
        scene_modes = results.get("scene_modes", {})
        for scene_key in self.SCENE_DESCRIPTIONS:
            meta = scene_modes.get(scene_key, {}) if isinstance(scene_modes, dict) else {}
            path = meta.get("path")
            if path and Path(path).exists():
                scene_paths.append(str(path))

        if scene_paths:
            self._concat_mp4s(scene_paths, real_output)
            videos["real_capture"] = str(real_output)

        fallback_path = await self._generate_dom_fallback_video(run_id)
        if Path(fallback_path) != fallback_output:
            shutil.copyfile(fallback_path, fallback_output)
        videos["dom_fallback"] = str(fallback_output)
        return videos

    async def _generate_dom_fallback_video(self, run_id: str) -> str:
        fallback_output = RAW_DIR / "day4_playwright_dom_fallback_v3.mp4"
        fallback_scenes = [
            ("fallback1", self._html_workspace(), self._action_workspace),
            ("fallback2", self._html_ai_assistant(), self._action_ai_assistant),
            ("fallback3", self._html_research_tabs(), self._action_research_tabs),
            ("fallback4", self._html_calculator(), self._action_calculator),
            ("fallback5", self._html_export(), self._action_export),
        ]
        paths: List[str] = []
        for scene_key, html, action in fallback_scenes:
            output = RAW_DIR / f"{run_id}_{scene_key}_dom.mp4"
            path, _frames = await self._record_scene_screenshot_sequence(scene_key, output, html, action)
            paths.append(path)
        self._concat_mp4s(paths, fallback_output)
        return str(fallback_output)

    def _concat_mp4s(self, paths: List[str], output_path: Path) -> None:
        list_path = TEMP_DIR / f"{output_path.stem}_concat.txt"
        lines = []
        for path in paths:
            safe_path = str(Path(path).resolve()).replace("\\", "/").replace("'", "'\\''")
            lines.append(f"file '{safe_path}'")
        list_path.write_text("\n".join(lines), encoding="utf-8")
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-vf",
                f"scale={self.config.width}:{self.config.height},fps={self.config.fps}",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )

    def _run_ffmpeg(self, cmd: List[str]) -> None:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _probe_frame_count(self, path: Path) -> int:
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=nb_frames",
                    "-of",
                    "default=nw=1:nk=1",
                    str(path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            value = (result.stdout or "").strip()
            return int(value) if value.isdigit() else 0
        except Exception:
            return 0

    async def _type_text(self, page: Page, selector: str, text: str, delay: int = 35):
        await page.click(selector)
        await page.keyboard.type(text, delay=delay)

    async def _action_workspace(self, page: Page):
        await self._type_text(page, "#address", "threadforge://day4/workflow", 22)
        await page.click("#load")
        await page.wait_for_timeout(450)
        await page.evaluate("startLoad()")
        await page.wait_for_timeout(900)
        await page.mouse.wheel(0, 720)
        await page.wait_for_timeout(450)
        await page.click("#reveal")

    async def _action_ai_assistant(self, page: Page):
        await self._type_text(page, "#prompt", "Write a 20 second AI workflow short", 28)
        await page.click("#generate")
        await page.wait_for_timeout(500)
        await page.evaluate("generateResult()")
        await page.wait_for_timeout(1200)
        await page.mouse.wheel(0, 420)

    async def _action_research_tabs(self, page: Page):
        await self._type_text(page, "#query", "best workflow proof points", 24)
        await page.click("#tab2")
        await page.wait_for_timeout(450)
        await page.click("#search")
        await page.evaluate("runResearch()")
        await page.wait_for_timeout(1100)
        await page.mouse.wheel(0, 620)

    async def _action_calculator(self, page: Page):
        await self._type_text(page, "#calc", "12 videos x 90 minutes saved", 24)
        await page.click("#calculate")
        await page.evaluate("calculateSavings()")
        await page.wait_for_timeout(900)
        await page.click("#details")
        await page.mouse.wheel(0, 360)

    async def _action_export(self, page: Page):
        await page.click("#startExport")
        await page.evaluate("startExport()")
        await page.wait_for_timeout(850)
        await self._type_text(page, "#filename", "day4_browser_workflow.mp4", 25)
        await page.click("#download")
        await page.wait_for_timeout(900)
        await page.mouse.wheel(0, 420)

    def _base_html(self, title: str, body: str) -> str:
        return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  width: 1080px;
  min-height: 1920px;
  font-family: Arial, Helvetica, sans-serif;
  background: #f4f6f8;
  color: #121417;
}}
.browser {{
  min-height: 1920px;
  background: linear-gradient(#eef1f4 0 92px, #ffffff 92px);
}}
.tabs {{
  height: 42px;
  display: flex;
  align-items: end;
  gap: 8px;
  padding: 8px 18px 0;
  background: #dfe4ea;
}}
.tab {{
  min-width: 230px;
  height: 34px;
  padding: 9px 16px;
  border-radius: 8px 8px 0 0;
  background: #ffffff;
  font-size: 15px;
}}
.bar {{
  height: 50px;
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 8px 18px;
  background: #ffffff;
  border-bottom: 1px solid #d7dde4;
}}
.navdot {{ width: 15px; height: 15px; border-radius: 50%; background: #b8c0ca; }}
.address {{
  flex: 1;
  height: 34px;
  border: 1px solid #c8d0da;
  border-radius: 18px;
  padding: 7px 16px;
  font-size: 15px;
  background: #f7f9fb;
}}
.page {{
  padding: 34px 38px 120px;
}}
h1 {{ font-size: 46px; margin: 0 0 14px; letter-spacing: 0; }}
h2 {{ font-size: 26px; margin: 0 0 16px; }}
p, label, input, textarea, button {{ font-size: 24px; }}
.panel {{
  border: 1px solid #d7dde4;
  border-radius: 8px;
  background: #ffffff;
  padding: 24px;
  margin: 18px 0;
}}
input, textarea {{
  width: 100%;
  border: 1px solid #c8d0da;
  border-radius: 6px;
  padding: 16px;
  background: #ffffff;
}}
textarea {{ min-height: 170px; resize: none; }}
button {{
  border: 0;
  border-radius: 6px;
  background: #1769e0;
  color: white;
  padding: 15px 22px;
  margin: 12px 8px 0 0;
}}
.muted {{ color: #667085; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.card {{
  border: 1px solid #e0e5eb;
  border-radius: 8px;
  padding: 18px;
  background: #fbfcfd;
  min-height: 120px;
}}
.progress {{
  height: 16px;
  background: #e6ebf1;
  border-radius: 999px;
  overflow: hidden;
  margin-top: 18px;
}}
.fill {{
  height: 100%;
  width: 0%;
  background: #10a37f;
  transition: width 1.1s ease;
}}
.spinner {{
  display: inline-block;
  width: 22px;
  height: 22px;
  border: 3px solid #c8d0da;
  border-top-color: #1769e0;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
.hidden {{ display: none; }}
.result {{
  opacity: 0;
  transform: translateY(14px);
  transition: opacity 0.55s ease, transform 0.55s ease;
}}
.result.show {{ opacity: 1; transform: translateY(0); }}
</style>
</head>
<body>
<div class="browser">
  <div class="tabs"><div class="tab">{title}</div><div class="tab muted">Research</div></div>
  <div class="bar"><div class="navdot"></div><div class="navdot"></div><div class="navdot"></div><input class="address" id="address" value="about:blank"></div>
  <main class="page">{body}</main>
</div>
</body>
</html>
"""

    def _html_workspace(self) -> str:
        return self._base_html(
            "Threadforge Workflow",
            """
<h1>Day4 Workflow Console</h1>
<p class="muted">Local browser page, no account session.</p>
<div class="panel">
  <button id="load">Open workflow</button>
  <button id="reveal">Reveal plan</button>
  <div class="progress"><div class="fill" id="loadFill"></div></div>
  <p id="loadStatus"><span class="spinner"></span> Waiting for workflow...</p>
</div>
<div class="grid">
  <div class="card">Script draft</div><div class="card">Voice pass</div>
  <div class="card">Browser proof</div><div class="card">Export checklist</div>
</div>
<div class="panel result" id="plan"><h2>Plan ready</h2><p>Five browser-recorded scenes queued for review.</p></div>
<script>
function startLoad() {
  loadFill.style.width = '100%';
  loadStatus.innerHTML = 'Workflow loaded with live browser proof.';
}
reveal.onclick = () => plan.classList.add('show');
</script>
""",
        )

    def _html_ai_assistant(self) -> str:
        return self._base_html(
            "Local AI Assistant",
            """
<h1>AI Assistant Draft</h1>
<p class="muted">Local DOM assistant page. No ChatGPT login page.</p>
<div class="panel">
  <textarea id="prompt" placeholder="Enter short video prompt"></textarea>
  <button id="generate">Generate</button>
  <div class="progress"><div class="fill" id="aiFill"></div></div>
  <p id="aiStatus">Ready.</p>
</div>
<div class="panel result" id="aiResult">
  <h2>Result reveal</h2>
  <p>Hook: Stop making shorts the hard way.</p>
  <p>Proof: Record the workflow, then export the final cut.</p>
</div>
<script>
function generateResult() {
  aiStatus.innerHTML = '<span class="spinner"></span> Drafting script...';
  aiFill.style.width = '100%';
  setTimeout(() => { aiStatus.textContent = 'Draft complete.'; aiResult.classList.add('show'); }, 850);
}
</script>
""",
        )

    def _html_research_tabs(self) -> str:
        return self._base_html(
            "Research Tabs",
            """
<h1>Research Browser</h1>
<div class="panel">
  <input id="query" placeholder="Search proof points">
  <button id="tab2">Switch tab</button>
  <button id="search">Search</button>
  <p id="tabState">Active tab: workflow notes</p>
  <div class="progress"><div class="fill" id="researchFill"></div></div>
</div>
<div class="grid result" id="researchResults">
  <div class="card">Typing captured</div><div class="card">Tab switch captured</div>
  <div class="card">Loading captured</div><div class="card">Result reveal captured</div>
</div>
<script>
tab2.onclick = () => { tabState.textContent = 'Active tab: proof research'; };
function runResearch() {
  researchFill.style.width = '100%';
  setTimeout(() => researchResults.classList.add('show'), 650);
}
</script>
""",
        )

    def _html_calculator(self) -> str:
        return self._base_html(
            "Savings Calculator",
            """
<h1>Workflow Calculator</h1>
<div class="panel">
  <input id="calc" placeholder="Enter calculation">
  <button id="calculate">Calculate</button>
  <button id="details">Details</button>
  <div class="progress"><div class="fill" id="calcFill"></div></div>
</div>
<div class="panel result" id="calcResult">
  <h2>Time saved</h2>
  <p>18 hours saved across 12 short videos.</p>
</div>
<div class="panel"><p>Review assumptions, export proof, then compare against manual editing time.</p></div>
<script>
function calculateSavings() {
  calcFill.style.width = '100%';
  setTimeout(() => calcResult.classList.add('show'), 650);
}
details.onclick = () => calcResult.scrollIntoView({behavior: 'smooth', block: 'center'});
</script>
""",
        )

    def _html_export(self) -> str:
        return self._base_html(
            "Export Proof",
            """
<h1>Export Center</h1>
<div class="panel">
  <button id="startExport">Start export</button>
  <input id="filename" placeholder="Filename">
  <button id="download">Download</button>
  <div class="progress"><div class="fill" id="exportFill"></div></div>
  <p id="exportStatus">Waiting.</p>
</div>
<div class="panel result" id="exportResult">
  <h2>Export ready</h2>
  <p>day4_browser_workflow.mp4 prepared for review.</p>
</div>
<script>
function startExport() {
  exportStatus.innerHTML = '<span class="spinner"></span> Rendering frames...';
  exportFill.style.width = '100%';
}
download.onclick = () => {
  exportStatus.textContent = 'Download staged locally.';
  exportResult.classList.add('show');
};
</script>
""",
        )
