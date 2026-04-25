#!/usr/bin/env python3
"""
Generate Day4 authenticated sandbox short.

Uses Playwright persistent context with backend/.browser_profiles/threadforge_sandbox
for sandbox-only authenticated captures, then falls back to the existing local DOM
browser-recorded scenes when policy checks fail.
"""

import asyncio
import shutil
import subprocess
from pathlib import Path

import pyttsx3
from playwright.async_api import Page, async_playwright

from utils.browser_capture import BrowserCaptureConfig, RealBrowserCapture
from utils.caption_generator import generate_ass_from_scenes
from utils.video_pipeline import ASSETS_DIR, BASE_DIR, RAW_DIR, TEMP_DIR, ScenePlan


RUN_ID = "day4_authenticated_sandbox_v1"
FINAL_PATH = ASSETS_DIR / "day4_authenticated_sandbox_v1.mp4"
SILENT_PATH = RAW_DIR / "day4_authenticated_sandbox_v1_silent.mp4"
AUDIO_PATH = TEMP_DIR / "day4_authenticated_sandbox_v1.wav"
ASS_PATH = TEMP_DIR / "day4_authenticated_sandbox_v1.ass"
LOG_PATH = TEMP_DIR / "day4_authenticated_sandbox_v1_render.log"
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID
PROFILE_DIR = BASE_DIR / ".browser_profiles" / "threadforge_sandbox"

SOURCE_TEXTS = [
    "Don't book flights before checking this.",
    "Search Google Flights with flexible dates first.",
    "Ask the sandbox assistant to compare airports and baggage fees.",
    "Compare Charlotte routes before you pay.",
    "Example comparison: eight twenty four to seven twelve saves one twelve.",
    "Comment flight for the prompt. Save this before booking.",
]

BLOCK_TERMS = [
    "captcha",
    "verify you are human",
    "unusual traffic",
    "consent required",
    "password",
]

PRIVATE_TERMS = [
    "@gmail.com",
    "@outlook.com",
    "@yahoo.com",
    "manage your google account",
    "personal info",
    "inbox",
    "profile dropdown",
]


def run(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed: {result.stderr[-1400:]}")
    return result


def ass_filter_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:")


async def mask_account_ui(page: Page) -> None:
    css = """
[aria-label*="Google Account" i],
[aria-label*="Account" i],
[aria-label*="profile" i],
[data-testid*="profile" i],
a[href*="SignOutOptions"],
a[href*="accounts.google"],
button:has(img),
img[src*="googleusercontent"],
img[alt*="profile" i],
header a[href*="/account"],
nav a[href*="/account"] {
  visibility: hidden !important;
}
body::after {
  content: "";
  position: fixed;
  top: 0;
  right: 0;
  width: 190px;
  height: 92px;
  background: #fff;
  z-index: 2147483647;
  pointer-events: none;
}
"""
    try:
        await page.add_style_tag(content=css)
    except Exception:
        pass


async def sandbox_rejection_reason(page: Page, typed: bool, min_text_len: int = 80) -> str:
    try:
        await mask_account_ui(page)
    except Exception:
        pass
    body_text = ""
    try:
        body_text = (await page.locator("body").inner_text(timeout=4000)).lower()
    except Exception:
        return "body_text_unavailable"
    for term in BLOCK_TERMS:
        if term in body_text:
            return f"blocking_term:{term}"
    for term in PRIVATE_TERMS:
        if term in body_text:
            return f"private_surface:{term}"
    if not typed:
        return "no_input_typed"
    if len(body_text.strip()) < min_text_len:
        return "blank_or_low_content"
    return ""


async def record_sandbox_scene(
    scene_key: str,
    description: str,
    provider: str,
    action,
    config: BrowserCaptureConfig,
    logs: list[str],
) -> str | None:
    if not PROFILE_DIR.exists():
        logs.append(
            f"[REAL_BROWSER] scene={scene_key} provider={provider} "
            f"status=fallback reason=sandbox_profile_missing:{PROFILE_DIR}"
        )
        return None

    output_path = RAW_DIR / f"{RUN_ID}_{scene_key}_{description}_{provider}.mp4"
    video_dir = TEMP_DIR / f"{RUN_ID}_{scene_key}_{provider}_native_video"
    shutil.rmtree(video_dir, ignore_errors=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    playwright = None
    context = None
    try:
        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": config.width, "height": config.height},
            record_video_dir=str(video_dir),
            record_video_size={"width": config.width, "height": config.height},
            args=[
                "--disable-dev-shm-usage",
                "--window-size=1080,1920",
            ],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await mask_account_ui(page)
        reason = await action(page)
        await mask_account_ui(page)
        video = page.video
        await page.close()
        raw_webm = Path(await video.path())
        await context.close()
        context = None
        await playwright.stop()
        playwright = None
        if reason:
            logs.append(
                f"[REAL_BROWSER] scene={scene_key} provider={provider} "
                f"status=fallback reason={reason}"
            )
            return None
        capturer = RealBrowserCapture(config)
        capturer._convert_clip(raw_webm, output_path, config.scene_duration, config.fps)
        frames = capturer._probe_frame_count(output_path)
        logs.append(
            f"[REAL_BROWSER] scene={scene_key} provider={provider} "
            f"status=success reason=authenticated_sandbox_capture frames={frames} path={output_path}"
        )
        return str(output_path)
    except Exception as exc:
        logs.append(
            f"[REAL_BROWSER] scene={scene_key} provider={provider} "
            f"status=fallback reason=exception:{str(exc)[:160]}"
        )
        return None
    finally:
        if context is not None:
            try:
                await context.close()
            except Exception:
                pass
        if playwright is not None:
            try:
                await playwright.stop()
            except Exception:
                pass
        shutil.rmtree(video_dir, ignore_errors=True)


async def google_flights_action(page: Page) -> str:
    typed = False
    await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded", timeout=35000)
    await page.wait_for_timeout(1200)
    await mask_account_ui(page)
    try:
        await page.keyboard.press("Control+L")
        await page.keyboard.type(
            "https://www.google.com/travel/flights?q=CLT%20to%20NYC%20flexible%20dates",
            delay=10,
        )
        typed = True
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("domcontentloaded", timeout=20000)
    except Exception:
        pass
    await page.wait_for_timeout(1000)
    await mask_account_ui(page)
    await page.mouse.move(830, 760, steps=18)
    await page.wait_for_timeout(300)
    await page.mouse.wheel(0, 620)
    await page.wait_for_timeout(500)
    await page.mouse.wheel(0, -180)
    await page.wait_for_timeout(450)
    return await sandbox_rejection_reason(page, typed)


async def sandbox_ai_action(page: Page) -> str:
    typed = False
    candidate_urls = [
        "https://chatgpt.com/",
        "https://duck.ai/",
    ]
    last_reason = "not_attempted"
    for url in candidate_urls:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=35000)
            await page.wait_for_timeout(1600)
            await mask_account_ui(page)
            selectors = [
                "textarea",
                "[contenteditable='true']",
                "div[role='textbox']",
                "input[type='text']",
            ]
            target = None
            for selector in selectors:
                loc = page.locator(selector).first
                try:
                    if await loc.count() > 0 and await loc.is_visible(timeout=1600):
                        target = loc
                        break
                except Exception:
                    continue
            if target is None:
                last_reason = f"prompt_box_not_found:{url}"
                continue
            await target.click()
            await page.keyboard.type(
                "Compare flight prices using flexible dates, nearby airports, and baggage fees.",
                delay=24,
            )
            typed = True
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2500)
            await mask_account_ui(page)
            await page.mouse.wheel(0, 480)
            await page.wait_for_timeout(500)
            reason = await sandbox_rejection_reason(page, typed, min_text_len=160)
            if not reason:
                return ""
            last_reason = reason
        except Exception as exc:
            last_reason = f"exception:{str(exc)[:80]}"
    return last_reason


def local_page(capturer: RealBrowserCapture, title: str, body: str) -> str:
    return capturer._base_html(title, body)


async def main() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    logs: list[str] = []
    raw_paths: list[str] = []
    sandbox_scenes: list[str] = []
    fallback_scenes: list[str] = []
    config = BrowserCaptureConfig(scene_duration=3.4, fps=30, fallback_fps=12)
    capturer = RealBrowserCapture(config)
    await capturer._setup_browser()
    try:
        hook_html = local_page(
            capturer,
            "Flight Hook",
            """
<h1>DON'T BOOK FLIGHTS<br>BEFORE CHECKING THIS</h1>
<p class="muted">Authenticated sandbox capture with privacy-safe fallback.</p>
<div class="panel"><input id="address" value="threadforge://flight-check">
<button id="start">Start check</button><div class="progress"><div class="fill" id="fill"></div></div>
<p id="status">Ready.</p></div>
<script>function go(){fill.style.width='100%';status.innerHTML='<span class="spinner"></span> Opening flight checklist...';setTimeout(()=>status.textContent='Checklist loaded.',650)}</script>
""",
        )

        async def hook_action(page: Page):
            await page.click("#address")
            await page.keyboard.press("Control+A")
            await page.keyboard.type("flight savings checklist", delay=28)
            await page.click("#start")
            await page.evaluate("go()")
            await page.wait_for_timeout(850)
            await page.mouse.wheel(0, 380)

        path, mode, _reason, frames = await capturer._record_scene(
            RUN_ID, "scene1", "hook_card", hook_html, hook_action
        )
        raw_paths.append(path)
        fallback_scenes.append("scene1:local_hook_card")
        logs.append(
            f"[REAL_BROWSER] scene=scene1 provider=fallback status=fallback "
            f"reason=hook_card_local_dom mode={mode} frames={frames} path={path}"
        )
    finally:
        await capturer._cleanup_browser()

    # Scene 2: authenticated sandbox Google Flights before fallback.
    path = await record_sandbox_scene(
        "scene2", "google_flights", "google_flights_sandbox", google_flights_action, config, logs
    )
    if path:
        raw_paths.append(path)
        sandbox_scenes.append("scene2:google_flights_sandbox")
    else:
        capturer = RealBrowserCapture(config)
        await capturer._setup_browser()
        try:
            search_html = local_page(
                capturer,
                "Flight Search",
                """
<h1>Flight Search</h1><div class="panel"><input id="query" placeholder="Search">
<button id="search">Search</button><div class="progress"><div class="fill" id="fill"></div></div></div>
<div class="grid result" id="results"><div class="card">Flexible date grid</div><div class="card">Nearby airport options</div></div>
<script>function go(){fill.style.width='100%';setTimeout(()=>results.classList.add('show'),600)}</script>
""",
            )

            async def search_action(page: Page):
                await page.click("#query")
                await page.keyboard.type("cheap flights flexible dates nearby airports", delay=24)
                await page.click("#search")
                await page.evaluate("go()")
                await page.wait_for_timeout(900)
                await page.mouse.wheel(0, 420)

            path, _mode, _reason, _frames = await capturer._record_scene(
                RUN_ID, "scene2", "search_fallback", search_html, search_action
            )
            raw_paths.append(path)
            fallback_scenes.append("scene2:local_search_mock")
        finally:
            await capturer._cleanup_browser()

    # Scene 3: authenticated sandbox AI assistant before fallback.
    path = await record_sandbox_scene(
        "scene3", "ai_assistant", "ai_sandbox", sandbox_ai_action, config, logs
    )
    if path:
        raw_paths.append(path)
        sandbox_scenes.append("scene3:ai_sandbox")
    else:
        capturer = RealBrowserCapture(config)
        await capturer._setup_browser()
        try:
            ai_html = local_page(
                capturer,
                "Travel AI Assistant",
                """
<h1>AI Travel Check</h1><p class="muted">Local DOM assistant. No third-party login.</p>
<div class="panel"><textarea id="prompt"></textarea><button id="ask">Ask AI</button>
<div class="progress"><div class="fill" id="fill"></div></div><p id="status">Ready.</p></div>
<div class="panel result" id="result"><h2>Result</h2><p>Compare flexible dates, nearby airports, and baggage fees before booking.</p></div>
<script>function go(){status.innerHTML='<span class="spinner"></span> Checking options...';fill.style.width='100%';setTimeout(()=>{status.textContent='Check complete.';result.classList.add('show')},800)}</script>
""",
            )

            async def ai_action(page: Page):
                await page.click("#prompt")
                await page.keyboard.type(
                    "Compare flight prices using flexible dates, nearby airports, and baggage fees.",
                    delay=22,
                )
                await page.click("#ask")
                await page.evaluate("go()")
                await page.wait_for_timeout(950)
                await page.mouse.wheel(0, 420)

            path, _mode, _reason, _frames = await capturer._record_scene(
                RUN_ID, "scene3", "ai_fallback", ai_html, ai_action
            )
            raw_paths.append(path)
            fallback_scenes.append("scene3:local_ai_assistant")
        finally:
            await capturer._cleanup_browser()

    capturer = RealBrowserCapture(config)
    await capturer._setup_browser()
    try:
        compare_html = local_page(
            capturer,
            "Travel Compare",
            """
<h1>CLT Route Compare</h1><div class="panel"><button id="compare">Compare routes</button>
<div class="progress"><div class="fill" id="fill"></div></div></div>
<div class="grid result" id="results"><div class="card">CLT to NYC<br>$824</div><div class="card">CLT nearby date option<br>$712</div></div>
<script>function go(){fill.style.width='100%';setTimeout(()=>results.classList.add('show'),650)}</script>
""",
        )

        async def compare_action(page: Page):
            await page.click("#compare")
            await page.evaluate("go()")
            await page.wait_for_timeout(900)
            await page.mouse.wheel(0, 420)

        path, mode, _reason, frames = await capturer._record_scene(
            RUN_ID, "scene4", "travel_compare", compare_html, compare_action
        )
        raw_paths.append(path)
        fallback_scenes.append("scene4:local_travel_compare")
        logs.append(
            f"[REAL_BROWSER] scene=scene4 provider=fallback status=fallback "
            f"reason=travel_compare_local_dom mode={mode} frames={frames} path={path}"
        )

        proof_html = local_page(
            capturer,
            "Example Comparison",
            """
<h1>Example Comparison</h1><div class="panel"><button id="show">Reveal savings</button>
<div class="progress"><div class="fill" id="fill"></div></div></div>
<div class="grid"><div class="card"><h2>Original fare</h2><p style="font-size:52px">$824</p></div>
<div class="card result" id="better"><h2>Better option</h2><p style="font-size:52px;color:#0d8f65">$712</p></div></div>
<div class="panel result" id="save"><h2>Estimated savings $112</h2><p>Example comparison label.</p></div>
<script>function go(){fill.style.width='100%';setTimeout(()=>{better.classList.add('show');save.classList.add('show')},650)}</script>
""",
        )

        async def proof_action(page: Page):
            await page.click("#show")
            await page.evaluate("go()")
            await page.wait_for_timeout(850)
            await page.mouse.wheel(0, 420)

        path, mode, _reason, frames = await capturer._record_scene(
            RUN_ID, "scene5", "proof_comparison", proof_html, proof_action
        )
        raw_paths.append(path)
        fallback_scenes.append("scene5:local_proof_comparison")
        logs.append(
            f"[REAL_BROWSER] scene=scene5 provider=fallback status=fallback "
            f"reason=proof_numbers_local_dom mode={mode} frames={frames} path={path}"
        )

        cta_html = local_page(
            capturer,
            "Flight Prompt CTA",
            """
<h1>COMMENT FLIGHT<br>FOR THE PROMPT</h1><p>Save this before booking.</p>
<div class="panel"><input id="comment" placeholder="Type keyword"><button id="send">Send</button>
<div class="progress"><div class="fill" id="fill"></div></div></div>
<div class="panel result" id="result"><h2>Prompt ready</h2><p>Flexible dates, nearby airports, baggage fees, final fare check.</p></div>
<script>function go(){fill.style.width='100%';setTimeout(()=>result.classList.add('show'),650)}</script>
""",
        )

        async def cta_action(page: Page):
            await page.click("#comment")
            await page.keyboard.type("FLIHGT", delay=75)
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Backspace")
            await page.keyboard.type("HT", delay=75)
            await page.click("#send")
            await page.evaluate("go()")
            await page.wait_for_timeout(850)
            await page.mouse.wheel(0, 320)

        path, mode, _reason, frames = await capturer._record_scene(
            RUN_ID, "scene6", "cta", cta_html, cta_action
        )
        raw_paths.append(path)
        fallback_scenes.append("scene6:local_cta")
        logs.append(
            f"[REAL_BROWSER] scene=scene6 provider=fallback status=fallback "
            f"reason=cta_local_dom mode={mode} frames={frames} path={path}"
        )

        capturer._concat_mp4s(raw_paths, SILENT_PATH)
    finally:
        await capturer._cleanup_browser()

    narration = " ".join(SOURCE_TEXTS)
    engine = pyttsx3.init()
    engine.setProperty("rate", 182)
    engine.save_to_file(narration, str(AUDIO_PATH))
    engine.runAndWait()
    if not AUDIO_PATH.exists() or AUDIO_PATH.stat().st_size < 1000:
        raise RuntimeError("offline narration missing or too small")

    scenes = []
    cursor = 0.0
    for idx, text in enumerate(SOURCE_TEXTS, start=1):
        end = cursor + 3.4
        scenes.append(
            ScenePlan(
                idx=idx,
                start=cursor,
                end=end,
                part="hook" if idx == 1 else ("cta" if idx == 6 else "body"),
                source_text=text,
                subtitle=text,
                visual_description="Flight savings authenticated sandbox capture",
                keywords=["flight", "travel", "savings"],
                energy="high",
                clip_path=raw_paths[idx - 1],
            )
        )
        cursor = end

    ass_content = generate_ass_from_scenes(scenes, audio_path=str(AUDIO_PATH))
    ASS_PATH.write_text(ass_content, encoding="utf-8")
    dialogue_count = ass_content.count("Dialogue:")
    if dialogue_count <= 0:
        raise RuntimeError("caption generation produced no Dialogue lines")

    run(
        [
            "ffmpeg", "-y",
            "-i", str(SILENT_PATH),
            "-i", str(AUDIO_PATH),
            "-filter_complex",
            f"[0:v]ass='{ass_filter_path(ASS_PATH)}'[v];[1:a]apad,atrim=0:20.4[a]",
            "-map", "[v]", "-map", "[a]",
            "-t", "20.4",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(FINAL_PATH),
        ],
        "mux audio and burn captions",
    )

    contact_sheet = REVIEW_DIR / "contact_sheet.jpg"
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg", "-y", "-i", str(FINAL_PATH),
            "-vf", "fps=1/3.4,scale=270:-1,tile=6x1",
            "-frames:v", "1", "-update", "1",
            str(contact_sheet),
        ],
        "contact sheet",
    )

    review_frames = []
    for idx, ts in enumerate([1.7, 5.1, 8.5, 11.9, 15.3, 18.7], start=1):
        frame_path = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
        run(
            [
                "ffmpeg", "-y", "-ss", f"{ts}", "-i", str(FINAL_PATH),
                "-frames:v", "1", "-update", "1", str(frame_path),
            ],
            f"review frame {idx}",
        )
        review_frames.append(str(frame_path))

    probe = run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "stream=index,codec_type,codec_name,avg_frame_rate,width,height,duration:"
            "format=duration,size,filename",
            "-of", "default=nw=1",
            str(FINAL_PATH),
        ],
        "probe final",
    ).stdout

    LOG_PATH.write_text(
        "\n".join(
            [
                f"final={FINAL_PATH}",
                f"contact_sheet={contact_sheet}",
                f"review_frames={' | '.join(review_frames)}",
                f"audio={AUDIO_PATH} provider=pyttsx3_offline size={AUDIO_PATH.stat().st_size}",
                f"ass={ASS_PATH} dialogue_count={dialogue_count}",
                f"sandbox_scenes={len(sandbox_scenes)} {sandbox_scenes}",
                f"fallback_scenes={len(fallback_scenes)} {fallback_scenes}",
                f"raw_clip_paths={' | '.join(raw_paths)}",
                *logs,
                "caption_source_text=" + " | ".join(SOURCE_TEXTS),
                probe,
            ]
        ),
        encoding="utf-8",
    )
    print(LOG_PATH)
    print(probe)


if __name__ == "__main__":
    asyncio.run(main())
