#!/usr/bin/env python3
"""
Generate Day4 flight/travel savings short with hybrid real-browser public
capture plus deterministic privacy-safe local fallback.
"""

import asyncio
import subprocess
import urllib.parse
from pathlib import Path

import pyttsx3
from playwright.async_api import Page

from utils.browser_capture import BrowserCaptureConfig, RealBrowserCapture
from utils.caption_generator import generate_ass_from_scenes
from utils.video_pipeline import ASSETS_DIR, RAW_DIR, TEMP_DIR, ScenePlan


RUN_ID = "day4_flight_hybrid_post_ready_v1"
FINAL_PATH = ASSETS_DIR / "day4_flight_hybrid_post_ready_v1.mp4"
SILENT_PATH = RAW_DIR / "day4_flight_hybrid_post_ready_v1_silent.mp4"
AUDIO_PATH = TEMP_DIR / "day4_flight_hybrid_post_ready_v1.wav"
ASS_PATH = TEMP_DIR / "day4_flight_hybrid_post_ready_v1.ass"
LOG_PATH = TEMP_DIR / "day4_flight_hybrid_post_ready_v1_render.log"
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID

REJECT_TERMS = [
    "login",
    "sign in",
    "captcha",
    "verify you are human",
    "unusual traffic",
    "consent required",
    "password",
    "account",
    "subscription",
    "private",
]

SOURCE_TEXTS = [
    "Don't book flights before checking this.",
    "Search flexible dates and nearby airports first.",
    "Compare Charlotte routes before you pay.",
    "Ask AI to compare flexible dates, airports, and baggage fees.",
    "Example comparison: eight twenty four to seven twelve saves one twelve.",
    "Comment flight for the prompt. Save this before booking.",
]


def run(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed: {result.stderr[-1400:]}")
    return result


def ass_filter_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:")


async def blocking_ui_reason(page: Page) -> str:
    blocker_selectors = [
        "[role='dialog']",
        "[aria-modal='true']",
        "form[action*='login' i]",
        "form:has(input[type='password'])",
        "input[type='password']",
        "[id*='captcha' i]",
        "[class*='captcha' i]",
        "[id*='challenge' i]",
        "[class*='challenge' i]",
        "[id*='consent' i]",
        "[class*='consent' i]",
        "[class*='modal' i]",
        "[id*='modal' i]",
        "[class*='overlay' i]",
        "[id*='overlay' i]",
    ]
    for selector in blocker_selectors:
        try:
            matches = page.locator(selector)
            count = await matches.count()
            for idx in range(min(count, 3)):
                item = matches.nth(idx)
                if await item.is_visible(timeout=400):
                    text = (await item.inner_text(timeout=700)).lower()
                    if any(term in text for term in REJECT_TERMS) or "robot" in text:
                        return f"blocking_ui:{selector}"
        except Exception:
            continue
    return ""


async def search_rejection_reason(
    page: Page,
    typed: bool,
    result_selector: str,
    min_results: int,
) -> str:
    blocker = await blocking_ui_reason(page)
    if blocker:
        return blocker
    if not typed:
        return "no_input_typed"
    try:
        count = await page.locator(result_selector).count()
        if count >= min_results:
            return ""
        return f"insufficient_results:{count}"
    except Exception:
        return "result_selector_failed"


async def page_rejection_reason(page: Page, typed: bool) -> str:
    blocker = await blocking_ui_reason(page)
    if blocker:
        return blocker
    if not typed:
        return "no_input_typed"
    body_text = (await page.locator("body").inner_text(timeout=3000)).strip()
    if len(body_text) < 120:
        return "blank_or_low_content"
    return ""


async def record_public_scene(
    capturer: RealBrowserCapture,
    scene_key: str,
    description: str,
    provider: str,
    action,
    logs: list[str],
) -> tuple[str | None, str | None]:
    output_path = RAW_DIR / f"{RUN_ID}_{scene_key}_{description}_{provider}.mp4"
    video_dir = TEMP_DIR / f"{RUN_ID}_{scene_key}_{provider}_native_video"
    video_dir.mkdir(parents=True, exist_ok=True)
    context = None
    try:
        context = await capturer.browser.new_context(
            viewport={"width": capturer.config.width, "height": capturer.config.height},
            record_video_dir=str(video_dir),
            record_video_size={"width": capturer.config.width, "height": capturer.config.height},
        )
        page = await context.new_page()
        reason = await action(page)
        video = page.video
        await page.close()
        raw_webm = Path(await video.path())
        await context.close()
        context = None
        if reason:
            logs.append(
                f"[REAL_BROWSER] scene={scene_key} provider={provider} "
                f"status=rejected reason={reason}"
            )
            return None, reason
        capturer._convert_clip(raw_webm, output_path, capturer.config.scene_duration, capturer.config.fps)
        frames = capturer._probe_frame_count(output_path)
        logs.append(
            f"[REAL_BROWSER] scene={scene_key} provider={provider} "
            f"status=success reason=clean_public_capture frames={frames} path={output_path}"
        )
        return str(output_path), None
    except Exception as exc:
        logs.append(
            f"[REAL_BROWSER] scene={scene_key} provider={provider} "
            f"status=rejected reason=exception:{str(exc)[:140]}"
        )
        return None, f"exception:{exc}"
    finally:
        if context is not None:
            try:
                await context.close()
            except Exception:
                pass
        for child in video_dir.glob("*"):
            try:
                child.unlink()
            except Exception:
                pass
        try:
            video_dir.rmdir()
        except Exception:
            pass


async def search_duckduckgo(page: Page, query: str) -> str:
    typed = False
    await page.goto("https://duckduckgo.com/", wait_until="domcontentloaded", timeout=25000)
    await page.wait_for_timeout(500)
    box = page.locator("input[name='q'], textarea[name='q']").first
    await box.click(timeout=5000)
    await page.keyboard.type(query[:14] + "x", delay=28)
    await page.wait_for_timeout(180)
    await page.keyboard.press("Backspace")
    await page.keyboard.type(query[14:], delay=24)
    typed = True
    await page.keyboard.press("Enter")
    await page.wait_for_load_state("domcontentloaded", timeout=15000)
    await page.wait_for_timeout(900)
    await page.mouse.wheel(0, 720)
    await page.wait_for_timeout(450)
    await page.mouse.wheel(0, -180)
    await page.wait_for_timeout(450)
    return await search_rejection_reason(
        page,
        typed,
        "article a[href], [data-testid='result'] a[href], .result a[href], #links a[href]",
        3,
    )


async def search_brave(page: Page, query: str) -> str:
    typed = False
    await page.goto("https://search.brave.com/", wait_until="domcontentloaded", timeout=25000)
    await page.wait_for_timeout(500)
    box = page.locator("input[name='q'], textarea[name='q'], input[type='search']").first
    await box.click(timeout=5000)
    await page.keyboard.type(query, delay=24)
    typed = True
    await page.keyboard.press("Enter")
    await page.wait_for_load_state("domcontentloaded", timeout=15000)
    await page.wait_for_timeout(900)
    await page.mouse.wheel(0, 680)
    await page.wait_for_timeout(500)
    return await search_rejection_reason(
        page,
        typed,
        "#results a[href], .snippet a[href], [data-testid='web-result'] a[href], main a[href]",
        3,
    )


async def search_mojeek(page: Page, query: str) -> str:
    typed = False
    await page.goto("https://www.mojeek.com/", wait_until="domcontentloaded", timeout=25000)
    await page.wait_for_timeout(500)
    box = page.locator("input[name='q'], input[type='search']").first
    await box.click(timeout=5000)
    await page.keyboard.type(query, delay=25)
    typed = True
    await page.keyboard.press("Enter")
    await page.wait_for_load_state("domcontentloaded", timeout=15000)
    await page.wait_for_timeout(900)
    await page.mouse.wheel(0, 650)
    await page.wait_for_timeout(500)
    return await search_rejection_reason(
        page,
        typed,
        ".results a[href], .result a[href], main a[href], li a[href]",
        1,
    )


async def try_search_ladder(
    capturer: RealBrowserCapture,
    scene_key: str,
    description: str,
    query: str,
    logs: list[str],
) -> str | None:
    providers = [
        ("duckduckgo", lambda page: search_duckduckgo(page, query)),
        ("brave", lambda page: search_brave(page, query)),
        ("mojeek", lambda page: search_mojeek(page, query)),
    ]
    for provider, action in providers:
        path, _reason = await record_public_scene(
            capturer, scene_key, description, provider, action, logs
        )
        if path:
            return path
    logs.append(
        f"[REAL_BROWSER] scene={scene_key} provider=fallback "
        "status=fallback reason=all_public_search_providers_rejected"
    )
    return None


async def try_duckai(capturer: RealBrowserCapture, logs: list[str]) -> str | None:
    async def action(page: Page) -> str:
        typed = False
        await page.goto("https://duck.ai/", wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(1000)
        content = (await page.content()).lower()
        for term in REJECT_TERMS:
            if term in content:
                return f"policy_term:{term}"
        selectors = [
            "textarea",
            "[contenteditable='true']",
            "input[type='text']",
        ]
        target = None
        for selector in selectors:
            loc = page.locator(selector).first
            try:
                if await loc.count() > 0 and await loc.is_visible(timeout=1500):
                    target = loc
                    break
            except Exception:
                continue
        if target is None:
            return "duckai_prompt_box_not_found"
        await target.click()
        await page.keyboard.type(
            "Compare flight prices using flexible dates, nearby airports, and baggage fees.",
            delay=24,
        )
        typed = True
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1800)
        await page.mouse.wheel(0, 480)
        return await page_rejection_reason(page, typed)

    path, _reason = await record_public_scene(
        capturer, "scene4", "ai_duckai", "duckai", action, logs
    )
    if not path:
        logs.append(
            "[REAL_BROWSER] scene=scene4 provider=fallback "
            "status=fallback reason=duckai_rejected_or_unavailable"
        )
    return path


def local_page(capturer: RealBrowserCapture, title: str, body: str) -> str:
    return capturer._base_html(title, body)


async def main() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    logs: list[str] = []
    raw_paths: list[str] = []
    public_scenes: list[str] = []
    fallback_scenes: list[str] = []
    config = BrowserCaptureConfig(scene_duration=3.4, fps=30, fallback_fps=12)
    capturer = RealBrowserCapture(config)
    await capturer._setup_browser()
    try:
        # Scene 1: local hook card.
        hook_html = local_page(
            capturer,
            "Flight Hook",
            """
<h1>DON'T BOOK FLIGHTS<br>BEFORE CHECKING THIS</h1>
<p class="muted">Real browser-recorded workflow with safe fallback.</p>
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

        path, mode, reason, frames = await capturer._record_scene(
            RUN_ID, "scene1", "hook_card", hook_html, hook_action
        )
        raw_paths.append(path)
        fallback_scenes.append("scene1:local_hook_card")
        logs.append(
            f"[REAL_BROWSER] scene=scene1 provider=fallback status=fallback "
            f"reason=hook_card_local_dom mode={mode} frames={frames} path={path}"
        )

        # Scene 2: validated public DuckDuckGo browser capture.
        path, _reason = await record_public_scene(
            capturer,
            "scene2",
            "search_flexible_dates",
            "duckduckgo",
            lambda page: search_duckduckgo(
                page, "cheap flights flexible dates nearby airports"
            ),
            logs,
        )
        if path:
            raw_paths.append(path)
            public_scenes.append("scene2:public_search")
        else:
            validated_duck = RAW_DIR / "sandbox_duckduckgo_smoke.mp4"
            if validated_duck.exists():
                duck_scene = RAW_DIR / f"{RUN_ID}_scene2_validated_duckduckgo.mp4"
                run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(validated_duck),
                        "-t",
                        f"{config.scene_duration:.2f}",
                        "-vf",
                        f"scale={config.width}:{config.height},fps={config.fps}",
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
                        str(duck_scene),
                    ],
                    "trim validated DuckDuckGo smoke capture",
                )
                raw_paths.append(str(duck_scene))
                public_scenes.append("scene2:validated_duckduckgo_public_capture")
                frames = capturer._probe_frame_count(duck_scene)
                logs.append(
                    f"[REAL_BROWSER] scene=scene2 provider=duckduckgo "
                    f"status=success reason=validated_sandbox_public_capture_reused "
                    f"frames={frames} path={duck_scene}"
                )
            else:
                fallback_scenes.append("scene2:local_search_mock")
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

        # Scene 3: local DOM travel comparison.
        fallback_scenes.append("scene3:local_travel_compare")
        compare_html = local_page(
            capturer,
            "Travel Compare",
            """
<h1>CLT Route Compare</h1><div class="panel"><button id="compare">Compare routes</button>
<div class="progress"><div class="fill" id="fill"></div></div></div>
<div class="grid result" id="results"><div class="card">CLT to NYC<br>$824</div><div class="card">CLT to MCO nearby option<br>$712</div></div>
<script>function go(){fill.style.width='100%';setTimeout(()=>results.classList.add('show'),650)}</script>
""",
        )

        async def compare_action(page: Page):
            await page.click("#compare")
            await page.evaluate("go()")
            await page.wait_for_timeout(900)
            await page.mouse.wheel(0, 420)

        path, mode, reason, frames = await capturer._record_scene(
            RUN_ID, "scene3", "compare_fallback", compare_html, compare_action
        )
        raw_paths.append(path)
        logs.append(
            f"[REAL_BROWSER] scene=scene3 provider=fallback status=fallback "
            f"reason=travel_compare_local_dom mode={mode} frames={frames} path={path}"
        )

        # Scene 4: local DOM AI assistant.
        fallback_scenes.append("scene4:local_ai_assistant")
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

        path, mode, reason, frames = await capturer._record_scene(
            RUN_ID, "scene4", "ai_fallback", ai_html, ai_action
        )
        raw_paths.append(path)
        logs.append(
            f"[REAL_BROWSER] scene=scene4 provider=fallback status=fallback "
            f"reason=ai_assistant_local_dom mode={mode} frames={frames} path={path}"
        )

        # Scene 5: proof comparison local DOM.
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

        path, mode, reason, frames = await capturer._record_scene(
            RUN_ID, "scene5", "proof_comparison", proof_html, proof_action
        )
        raw_paths.append(path)
        fallback_scenes.append("scene5:local_proof_comparison")
        logs.append(
            f"[REAL_BROWSER] scene=scene5 provider=fallback status=fallback "
            f"reason=proof_numbers_local_dom mode={mode} frames={frames} path={path}"
        )

        # Scene 6: CTA local DOM.
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

        path, mode, reason, frames = await capturer._record_scene(
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
                visual_description="Flight savings hybrid browser capture",
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
            "ffmpeg",
            "-y",
            "-i",
            str(SILENT_PATH),
            "-i",
            str(AUDIO_PATH),
            "-filter_complex",
            f"[0:v]ass='{ass_filter_path(ASS_PATH)}'[v];[1:a]apad,atrim=0:20.4[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            "20.4",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(FINAL_PATH),
        ],
        "mux audio and burn captions",
    )

    contact_sheet = REVIEW_DIR / "contact_sheet.jpg"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(FINAL_PATH),
            "-vf",
            "fps=1/3.4,scale=270:-1,tile=6x1",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(contact_sheet),
        ],
        "contact sheet",
    )

    review_frames: list[str] = []
    for idx, ts in enumerate([1.7, 5.1, 8.5, 11.9, 15.3, 18.7], start=1):
        frame_path = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
        run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{ts}",
                "-i",
                str(FINAL_PATH),
                "-frames:v",
                "1",
                "-update",
                "1",
                str(frame_path),
            ],
            f"review frame {idx}",
        )
        review_frames.append(str(frame_path))

    probe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,codec_name,avg_frame_rate,width,height,duration:"
            "format=duration,size,filename",
            "-of",
            "default=nw=1",
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
                f"public_browser_scenes={len(public_scenes)} {public_scenes}",
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
