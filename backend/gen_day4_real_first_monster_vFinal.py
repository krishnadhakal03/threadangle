#!/usr/bin/env python3
"""Generate Day4 Monster Mode with authenticated sandbox Google Flights capture."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pyttsx3

from utils.caption_generator import generate_ass_from_scenes
from utils.video_pipeline import ASSETS_DIR, BASE_DIR, RAW_DIR, TEMP_DIR, ScenePlan


RUN_ID = "day4_real_first_monster_vFinal"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
AUDIO_PATH = TEMP_DIR / f"{RUN_ID}.wav"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
NODE_SCRIPT_PATH = TEMP_DIR / f"{RUN_ID}_capture.js"
CAPTURE_JSON_PATH = TEMP_DIR / f"{RUN_ID}_capture.json"
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID

USER_DATA_DIR = Path(r"F:\Threadforge\backend\.browser_profiles\threadforge_sandbox")
PROFILE_DIRECTORY = "Profile 1"
PROFILE_PATH = USER_DATA_DIR / PROFILE_DIRECTORY if (USER_DATA_DIR / PROFILE_DIRECTORY).exists() else USER_DATA_DIR

WIDTH = 1080
HEIGHT = 1920
FPS = 30
SCENE_DURATION = 3.4
FINAL_DURATION = 20.4

SOURCE_TEXTS = [
    "Don't book flights before checking this.",
    "Search Google Flights from Charlotte to Orlando.",
    "Compare flexible dates and price options before you pay.",
    "Ask AI to compare dates, nearby airports, and baggage fees.",
    "Example comparison: eight twenty four to seven twelve saves one twelve.",
    "Comment flight for the prompt. Save this before booking.",
]


def run(cmd: list[str], label: str, **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed: {result.stderr[-3000:]}")
    return result


def ass_filter_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:")


def ffmpeg_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def js_string(value: Path | str) -> str:
    return json.dumps(str(value))


def write_node_capture_script() -> None:
    NODE_SCRIPT_PATH.write_text(
        f"""
const {{ chromium }} = require('playwright');
const fs = require('fs');
const path = require('path');

const RUN_ID = {json.dumps(RUN_ID)};
const WIDTH = {WIDTH};
const HEIGHT = {HEIGHT};
const RAW_DIR = {js_string(RAW_DIR)};
const TEMP_DIR = {js_string(TEMP_DIR)};
const OUT_JSON = {js_string(CAPTURE_JSON_PATH)};
const PROFILE_PATH = {js_string(PROFILE_PATH)};

const MASK_CSS = ``;

function localHtml(title, body) {{
  return `<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${{title}}</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; width: 1080px; min-height: 1920px; font-family: Arial, Helvetica, sans-serif; background: #f5f7fb; color: #121417; }}
.browser {{ min-height: 1920px; background: linear-gradient(#e8edf4 0 92px, #ffffff 92px); }}
.tabs {{ height: 42px; display: flex; align-items: end; gap: 8px; padding: 8px 18px 0; background: #d9e0ea; }}
.tab {{ width: 245px; height: 34px; padding: 9px 16px; border-radius: 8px 8px 0 0; background: #fff; font-size: 15px; }}
.bar {{ height: 50px; display: flex; gap: 14px; align-items: center; padding: 8px 18px; background: #fff; border-bottom: 1px solid #d5dce5; }}
.dot {{ width: 15px; height: 15px; border-radius: 50%; background: #b8c0ca; }}
.address {{ flex: 1; height: 34px; border: 1px solid #c8d0da; border-radius: 18px; padding: 7px 16px; font-size: 15px; background: #f7f9fb; }}
.page {{ padding: 46px 42px 120px; }}
h1 {{ font-size: 64px; line-height: 0.98; margin: 0 0 24px; letter-spacing: 0; }}
h2 {{ font-size: 32px; margin: 0 0 12px; }}
p, input, textarea, button {{ font-size: 25px; }}
.panel {{ border: 1px solid #d7dde4; border-radius: 8px; background: #fff; padding: 26px; margin: 20px 0; }}
.muted {{ color: #667085; }}
input, textarea {{ width: 100%; border: 1px solid #c8d0da; border-radius: 6px; padding: 18px; background: #fff; }}
textarea {{ min-height: 190px; resize: none; }}
button {{ border: 0; border-radius: 6px; background: #1769e0; color: #fff; padding: 16px 24px; margin-top: 14px; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
.card {{ border: 1px solid #dfe5ec; border-radius: 8px; background: #fbfcfd; padding: 24px; min-height: 178px; }}
.price {{ font-size: 64px; font-weight: 800; margin: 10px 0 0; }}
.green {{ color: #0d8f65; }}
.progress {{ height: 16px; background: #e7ecf3; border-radius: 999px; overflow: hidden; margin-top: 18px; }}
.fill {{ height: 100%; width: 0; background: #10a37f; transition: width 1s ease; }}
.result {{ opacity: 0; transform: translateY(16px); transition: opacity .5s ease, transform .5s ease; }}
.show {{ opacity: 1; transform: translateY(0); }}
</style></head><body><div class="browser">
<div class="tabs"><div class="tab">${{title}}</div><div class="tab muted">Review</div></div>
<div class="bar"><div class="dot"></div><div class="dot"></div><div class="dot"></div><input class="address" id="addr" value="threadforge://day4"></div>
<main class="page">${{body}}</main></div></body></html>`;
}}

async function visible(locator, timeout = 1200) {{
  try {{ return await locator.first().isVisible({{ timeout }}); }} catch {{ return false; }}
}}

async function addPrivacy(context, page) {{
  try {{ await context.addInitScript(css => {{
    const style = document.createElement('style');
    style.textContent = css;
    document.documentElement.appendChild(style);
  }}, MASK_CSS); }} catch {{}}
  try {{ await page.addStyleTag({{ content: MASK_CSS }}); }} catch {{}}
}}

async function bodyText(page) {{
  try {{ return await page.locator('body').innerText({{ timeout: 5000 }}); }} catch {{ return ''; }}
}}

async function rejectReason(page, typed) {{
  const text = (await bodyText(page)).toLowerCase();
  for (const term of ['password', 'captcha', 'verify you are human', 'unusual traffic', 'inbox', 'manage your google account', 'personal info']) {{
    if (text.includes(term)) return `private_or_blocking_term:${{term}}`;
  }}
  if (await visible(page.locator('input[type="password"]'), 300)) return 'password_input_visible';
  if (!typed) return 'no_input_typed';
  if (text.trim().length < 80) return 'blank_or_low_content';
  return '';
}}

async function fillFlightField(page, labels, value) {{
  const candidates = [];
  for (const label of labels) {{
    candidates.push(page.getByLabel(label, {{ exact: false }}));
    candidates.push(page.getByText(label, {{ exact: false }}));
    candidates.push(page.locator(`input[aria-label*='${{label}}' i]`));
    candidates.push(page.locator(`[aria-label*='${{label}}' i]`));
  }}
  for (const loc of candidates) {{
    try {{
      if (await visible(loc, 1500)) {{
        await loc.first().click({{ timeout: 2500 }});
        await page.waitForTimeout(260);
        try {{ await page.locator(':focus').fill(value, {{ timeout: 1400 }}); }}
        catch {{ await page.keyboard.press('Control+A'); await page.keyboard.type(value, {{ delay: 34 }}); }}
        await page.waitForTimeout(520);
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(760);
        return true;
      }}
    }} catch {{}}
  }}
  return false;
}}

async function closeClip(context, page, outWebm) {{
  const video = page.video();
  await page.waitForTimeout(250);
  await page.close();
  const raw = await video.path();
  await context.close();
  fs.copyFileSync(raw, outWebm);
}}

async function recordLocal(name, html, action) {{
  const videoDir = path.join(TEMP_DIR, `${{RUN_ID}}_${{name}}_video`);
  fs.rmSync(videoDir, {{ recursive: true, force: true }});
  fs.mkdirSync(videoDir, {{ recursive: true }});
  const browser = await chromium.launch({{ headless: true, args: [`--window-size=${{WIDTH}},${{HEIGHT}}`] }});
  const context = await browser.newContext({{
    viewport: {{ width: WIDTH, height: HEIGHT }},
    recordVideo: {{ dir: videoDir, size: {{ width: WIDTH, height: HEIGHT }} }}
  }});
  const page = await context.newPage();
  await page.setContent(html, {{ waitUntil: 'domcontentloaded' }});
  await action(page);
  await page.waitForTimeout(500);
  const outWebm = path.join(RAW_DIR, `${{RUN_ID}}_${{name}}.webm`);
  await closeClip(context, page, outWebm);
  await browser.close();
  return {{ name, webm: outWebm, real_browser: false, attempted_real: false, privacy_ok: true, reason: '' }};
}}

async function recordFlights(name, variant) {{
  const videoDir = path.join(TEMP_DIR, `${{RUN_ID}}_${{name}}_video`);
  fs.rmSync(videoDir, {{ recursive: true, force: true }});
  fs.mkdirSync(videoDir, {{ recursive: true }});
  let context;
  let status = {{ name, webm: path.join(RAW_DIR, `${{RUN_ID}}_${{name}}.webm`), real_browser: true, attempted_real: true, privacy_ok: false, reason: '' }};
  try {{
    context = await chromium.launchPersistentContext(PROFILE_PATH, {{
      channel: 'chrome',
      headless: false,
      viewport: {{ width: WIDTH, height: HEIGHT }},
      recordVideo: {{ dir: videoDir, size: {{ width: WIDTH, height: HEIGHT }} }},
      args: ['--no-first-run', '--no-default-browser-check', `--window-size=${{WIDTH}},${{HEIGHT}}`, '--window-position=40,20'],
      timeout: 60000
    }});
    const page = context.pages()[0] || await context.newPage();
    await addPrivacy(context, page);
    await page.goto('https://www.google.com/travel/flights', {{ waitUntil: 'domcontentloaded', timeout: 70000 }});
    await page.waitForTimeout(2300);
    await addPrivacy(context, page);
    const originVisible = await visible(page.locator("input[aria-label*='Where from' i], input[aria-label*='From' i], [aria-label*='Where from' i], [aria-label='From']"), 2500);
    const destVisible = await visible(page.locator("input[aria-label*='Where to' i], input[aria-label*='To' i], [aria-label*='Where to' i], [aria-label='To']"), 2500);
    const dateVisible = await visible(page.locator("[aria-label*='Departure' i], [aria-label*='date' i], input[aria-label*='Departure' i], div:has-text('Departure')"), 2500);
    const typedClt = await fillFlightField(page, ['Where from', 'From'], 'CLT');
    const typedMco = await fillFlightField(page, ['Where to', 'To'], 'MCO');
    if (variant === 'search') {{
      for (const loc of [page.getByRole('button', {{ name: /search/i }}), page.locator("button[aria-label*='Search' i], [role='button'][aria-label*='Search' i]")]) {{
        try {{ if (await visible(loc, 1200)) {{ await loc.first().click({{ timeout: 2500 }}); break; }} }} catch {{}}
      }}
      await page.waitForTimeout(900);
      await page.mouse.move(820, 950, {{ steps: 18 }});
      await page.waitForTimeout(450);
    }} else {{
      for (const loc of [page.getByRole('button', {{ name: /search/i }}), page.locator("button[aria-label*='Search' i], [role='button'][aria-label*='Search' i]")]) {{
        try {{ if (await visible(loc, 1200)) {{ await loc.first().click({{ timeout: 2500 }}); break; }} }} catch {{}}
      }}
      await page.waitForTimeout(2200);
      await page.mouse.wheel(0, 760);
      await page.waitForTimeout(600);
      await page.mouse.wheel(0, -220);
      await page.waitForTimeout(450);
    }}
    await addPrivacy(context, page);
    const reason = await rejectReason(page, typedClt && typedMco);
    const low = (await bodyText(page)).toLowerCase();
    const reached = ['flights', 'clt', 'mco', 'charlotte', 'orlando', 'departing flights', 'best departing'].some(s => low.includes(s));
    if (reason) status.reason = reason;
    else if (!originVisible || !destVisible || !dateVisible || !typedClt || !typedMco || !reached) {{
      status.reason = `flights_ui_incomplete:origin=${{originVisible}} dest=${{destVisible}} date=${{dateVisible}} clt=${{typedClt}} mco=${{typedMco}} reached=${{reached}}`;
    }} else {{
      status.privacy_ok = true;
    }}
    await closeClip(context, page, status.webm);
    context = null;
    return status;
  }} catch (err) {{
    status.reason = `exception:${{String(err.message || err).slice(0, 300)}}`;
    if (context) await context.close().catch(() => {{}});
    return status;
  }}
}}

async function recordGoogleSearch(name, query, mode) {{
  const videoDir = path.join(TEMP_DIR, `${{RUN_ID}}_${{name}}_video`);
  fs.rmSync(videoDir, {{ recursive: true, force: true }});
  fs.mkdirSync(videoDir, {{ recursive: true }});
  let context;
  let status = {{ name, webm: path.join(RAW_DIR, `${{RUN_ID}}_${{name}}.webm`), real_browser: true, attempted_real: true, privacy_ok: false, reason: '' }};
  try {{
    context = await chromium.launchPersistentContext(PROFILE_PATH, {{
      channel: 'chrome',
      headless: false,
      viewport: {{ width: WIDTH, height: HEIGHT }},
      recordVideo: {{ dir: videoDir, size: {{ width: WIDTH, height: HEIGHT }} }},
      args: ['--no-first-run', '--no-default-browser-check', `--window-size=${{WIDTH}},${{HEIGHT}}`, '--window-position=40,20'],
      timeout: 60000
    }});
    const page = context.pages()[0] || await context.newPage();
    await page.goto('https://www.google.com', {{ waitUntil: 'domcontentloaded', timeout: 60000 }});
    await page.waitForTimeout(900);
    const box = page.locator("textarea[name='q'], input[name='q']").first();
    await box.click({{ timeout: 5000 }});
    await page.keyboard.type(query.slice(0, Math.max(8, Math.floor(query.length / 2))), {{ delay: 30 }});
    await page.waitForTimeout(220);
    await page.keyboard.type(query.slice(Math.max(8, Math.floor(query.length / 2))), {{ delay: 24 }});
    await page.keyboard.press('Enter');
    await page.waitForLoadState('domcontentloaded', {{ timeout: 20000 }}).catch(() => {{}});
    await page.waitForTimeout(mode === 'proof' ? 1400 : 900);
    await page.mouse.move(760, 920, {{ steps: 18 }});
    await page.waitForTimeout(350);
    await page.mouse.wheel(0, mode === 'proof' ? 980 : 650);
    await page.waitForTimeout(650);
    await page.mouse.wheel(0, -160);
    await page.waitForTimeout(350);
    const reason = await rejectReason(page, true);
    const low = (await bodyText(page)).toLowerCase();
    const hasResults = ['google flights', 'flight', 'flexible dates', 'price', 'search'].some(s => low.includes(s));
    if (reason) status.reason = reason;
    else if (!hasResults) status.reason = 'search_results_not_detected';
    else status.privacy_ok = true;
    await closeClip(context, page, status.webm);
    context = null;
    return status;
  }} catch (err) {{
    status.reason = `exception:${{String(err.message || err).slice(0, 300)}}`;
    if (context) await context.close().catch(() => {{}});
    return status;
  }}
}}

async function recordDuckAi(name) {{
  const videoDir = path.join(TEMP_DIR, `${{RUN_ID}}_${{name}}_video`);
  fs.rmSync(videoDir, {{ recursive: true, force: true }});
  fs.mkdirSync(videoDir, {{ recursive: true }});
  let browser, context;
  let status = {{ name, webm: path.join(RAW_DIR, `${{RUN_ID}}_${{name}}.webm`), real_browser: true, attempted_real: true, privacy_ok: false, reason: '' }};
  try {{
    browser = await chromium.launch({{ headless: false, args: ['--no-first-run', '--no-default-browser-check', `--window-size=${{WIDTH}},${{HEIGHT}}`, '--window-position=40,20'] }});
    context = await browser.newContext({{
      viewport: {{ width: WIDTH, height: HEIGHT }},
      recordVideo: {{ dir: videoDir, size: {{ width: WIDTH, height: HEIGHT }} }}
    }});
    const page = await context.newPage();
    await page.goto('https://duck.ai/', {{ waitUntil: 'domcontentloaded', timeout: 50000 }});
    await page.waitForTimeout(1800);
    const selectors = ['textarea', '[contenteditable="true"]', 'div[role="textbox"]', 'input[type="text"]'];
    let target = null;
    for (const selector of selectors) {{
      const loc = page.locator(selector).first();
      try {{
        if (await visible(loc, 1800)) {{ target = loc; break; }}
      }} catch {{}}
    }}
    if (!target) {{
      status.reason = 'duckai_prompt_box_not_found';
    }} else {{
      await target.click();
      await page.keyboard.type('Compare CLT to MCO using flexible dates, nearby airports, baggage fees, and final fare.', {{ delay: 24 }});
      await page.waitForTimeout(400);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2600);
      await page.mouse.wheel(0, 460);
      const reason = await rejectReason(page, true);
      if (reason) status.reason = reason;
      else status.privacy_ok = true;
    }}
    await closeClip(context, page, status.webm);
    context = null;
    if (browser) await browser.close();
    return status;
  }} catch (err) {{
    status.reason = `exception:${{String(err.message || err).slice(0, 300)}}`;
    if (context) await context.close().catch(() => {{}});
    if (browser) await browser.close().catch(() => {{}});
    return status;
  }}
}}

function markFallback(localStatus, realStatus) {{
  localStatus.attempted_real = true;
  localStatus.fallback_reason = realStatus.reason || 'real_capture_rejected';
  try {{ if (realStatus.webm) fs.rmSync(realStatus.webm, {{ force: true }}); }} catch {{}}
  return localStatus;
}}

(async () => {{
  fs.mkdirSync(RAW_DIR, {{ recursive: true }});
  fs.mkdirSync(TEMP_DIR, {{ recursive: true }});
  const results = [];

  async function fallbackHook(realStatus) {{
    return markFallback(await recordLocal('scene1_hook_card', localHtml('Flight Hook', `
    <h1>DON'T BOOK<br>FLIGHTS YET</h1>
    <p class="muted">Real Google Flights check, then AI comparison.</p>
    <div class="panel"><input id="q" value="CLT to MCO price check"><button id="go">Start</button><div class="progress"><div class="fill" id="fill"></div></div><p id="status">Ready.</p></div>
    <script>go.onclick=()=>{{fill.style.width='100%';status.textContent='Opening Google Flights...';}}</script>
  `), async page => {{
    await page.click('#q'); await page.keyboard.press('Control+A'); await page.keyboard.type('flight price trap check', {{ delay: 28 }});
    await page.click('#go'); await page.waitForTimeout(1150); await page.mouse.wheel(0, 360);
  }}), realStatus);
  }}

  async function fallbackAi(realStatus) {{
    return markFallback(await recordLocal('scene4_local_ai_prompt', localHtml('Local AI Assistant', `
    <h1>AI TRAVEL CHECK</h1><p class="muted">Local DOM assistant. No account login.</p>
    <div class="panel"><textarea id="prompt" placeholder="Ask for a comparison"></textarea><button id="ask">Ask AI</button><div class="progress"><div class="fill" id="fill"></div></div><p id="status">Ready.</p></div>
    <div class="panel result" id="answer"><h2>Check complete</h2><p>Compare flexible dates, nearby airports, baggage fees, and final fare.</p></div>
    <script>ask.onclick=()=>{{fill.style.width='100%';status.textContent='Comparing options...';setTimeout(()=>{{status.textContent='Better route found.';answer.classList.add('show')}},700);}}</script>
  `), async page => {{
    await page.click('#prompt');
    await page.keyboard.type('Compare CLT to MCO using flexible dates, nearby airports, and baggage fees.', {{ delay: 22 }});
    await page.click('#ask'); await page.waitForTimeout(1250); await page.mouse.wheel(0, 420);
  }}), realStatus);
  }}

  async function fallbackProof(realStatus) {{
    return markFallback(await recordLocal('scene5_proof_comparison', localHtml('Proof Comparison', `
    <h1>PRICE CHECK</h1><div class="panel"><button id="show">Reveal savings</button><div class="progress"><div class="fill" id="fill"></div></div></div>
    <div class="grid"><div class="card"><h2>First option</h2><p class="price">$824</p></div><div class="card result" id="better"><h2>Better option</h2><p class="price green">$712</p></div></div>
    <div class="panel result" id="save"><h2>Save $112</h2><p>Example comparison for the workflow.</p></div>
    <script>show.onclick=()=>{{fill.style.width='100%';setTimeout(()=>{{better.classList.add('show');save.classList.add('show')}},650);}}</script>
  `), async page => {{
    await page.click('#show'); await page.waitForTimeout(1250); await page.mouse.wheel(0, 400);
  }}), realStatus);
  }}

  const scene1Real = await recordGoogleSearch('scene1_google_search_hook', 'do not book flights before checking Google Flights flexible dates', 'hook');
  results.push(scene1Real.privacy_ok ? scene1Real : await fallbackHook(scene1Real));

  results.push(await recordFlights('scene2_google_flights_search', 'search'));
  results.push(await recordFlights('scene3_google_flights_results', 'results'));

  const scene4Real = await recordDuckAi('scene4_duckai_prompt');
  results.push(scene4Real.privacy_ok ? scene4Real : await fallbackAi(scene4Real));

  const scene5Real = await recordGoogleSearch('scene5_google_search_proof', 'Google Flights flexible dates price tracking baggage fees compare fare', 'proof');
  results.push(scene5Real.privacy_ok ? scene5Real : await fallbackProof(scene5Real));

  results.push(await recordLocal('scene6_cta_card', localHtml('Flight Prompt CTA', `
    <h1>COMMENT<br>FLIGHT</h1><p>Get the prompt before you book.</p>
    <div class="panel"><input id="comment" placeholder="Type keyword"><button id="send">Send</button><div class="progress"><div class="fill" id="fill"></div></div></div>
    <div class="panel result" id="ready"><h2>Prompt ready</h2><p>Flexible dates, nearby airports, baggage fees, final fare check.</p></div>
    <script>send.onclick=()=>{{fill.style.width='100%';setTimeout(()=>ready.classList.add('show'),650);}}</script>
  `), async page => {{
    await page.click('#comment'); await page.keyboard.type('FLIHGT', {{ delay: 80 }}); await page.keyboard.press('Backspace'); await page.keyboard.press('Backspace'); await page.keyboard.type('HT', {{ delay: 80 }});
    await page.click('#send'); await page.waitForTimeout(1150); await page.mouse.wheel(0, 340);
  }}));
  fs.writeFileSync(OUT_JSON, JSON.stringify({{ profile_path: PROFILE_PATH, results }}, null, 2), 'utf8');
}})().catch(err => {{
  fs.writeFileSync(OUT_JSON, JSON.stringify({{ profile_path: PROFILE_PATH, fatal: String(err.stack || err) }}, null, 2), 'utf8');
  process.exit(1);
}});
""",
        encoding="utf-8",
    )


def convert_clip(src: Path, dst: Path, start_offset: float = 0.0) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start_offset:.2f}",
            "-i",
            str(src),
            "-t",
            f"{SCENE_DURATION:.2f}",
            "-vf",
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
            f"tpad=stop_mode=clone:stop_duration={SCENE_DURATION},fps={FPS}",
            "-an",
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
        ],
        f"convert {dst.name}",
    )


def concat_clips(paths: list[Path]) -> None:
    concat_path = TEMP_DIR / f"{RUN_ID}_concat.txt"
    concat_path.write_text(
        "\n".join(f"file '{ffmpeg_path(path)}'" for path in paths),
        encoding="utf-8",
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            str(SILENT_PATH),
        ],
        "concat raw clips",
    )


def make_audio() -> None:
    narration = " ".join(SOURCE_TEXTS)
    engine = pyttsx3.init()
    engine.setProperty("rate", 184)
    engine.save_to_file(narration, str(AUDIO_PATH))
    engine.runAndWait()
    if not AUDIO_PATH.exists() or AUDIO_PATH.stat().st_size < 1000:
        raise RuntimeError("offline narration missing or too small")


def make_captions(raw_paths: list[Path]) -> int:
    scenes: list[ScenePlan] = []
    cursor = 0.0
    for idx, text in enumerate(SOURCE_TEXTS, start=1):
        end = cursor + SCENE_DURATION
        scenes.append(
            ScenePlan(
                idx=idx,
                start=cursor,
                end=end,
                part="hook" if idx == 1 else ("cta" if idx == 6 else "body"),
                source_text=text,
                subtitle=text,
                visual_description="Day4 authenticated Google Flights Monster Mode",
                keywords=["flight", "travel", "savings"],
                energy="high",
                clip_path=str(raw_paths[idx - 1]),
            )
        )
        cursor = end
    ass = generate_ass_from_scenes(scenes, audio_path=str(AUDIO_PATH))
    ASS_PATH.write_text(ass, encoding="utf-8")
    dialogue_count = ass.count("Dialogue:")
    if dialogue_count <= 0:
        raise RuntimeError("caption generation produced no Dialogue lines")
    return dialogue_count


def mux_final() -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(SILENT_PATH),
            "-i",
            str(AUDIO_PATH),
            "-filter_complex",
            f"[0:v]ass='{ass_filter_path(ASS_PATH)}'[v];[1:a]apad,atrim=0:{FINAL_DURATION:.1f}[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            f"{FINAL_DURATION:.1f}",
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


def make_review_artifacts() -> tuple[Path, list[Path]]:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
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
    review_frames: list[Path] = []
    for idx, ts in enumerate([1.7, 5.1, 8.5, 11.9, 15.3, 18.7], start=1):
        frame = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
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
                str(frame),
            ],
            f"review frame {idx}",
        )
        review_frames.append(frame)
    return contact_sheet, review_frames


def probe(path: Path) -> str:
    return run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,codec_name,avg_frame_rate,width,height,duration:"
            "format=duration,size,filename",
            "-of",
            "default=nw=1",
            str(path),
        ],
        f"probe {path.name}",
    ).stdout.strip()


def main() -> None:
    for directory in [ASSETS_DIR, RAW_DIR, TEMP_DIR, REVIEW_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    if not PROFILE_PATH.exists():
        raise RuntimeError(f"sandbox profile missing: {PROFILE_PATH}")

    write_node_capture_script()
    env = os.environ.copy()
    env["BROWSER_SANDBOX_USER_DATA_DIR"] = str(USER_DATA_DIR)
    env["BROWSER_SANDBOX_PROFILE_DIRECTORY"] = PROFILE_DIRECTORY
    run(["node", str(NODE_SCRIPT_PATH)], "authenticated Google Flights capture", cwd=str(BASE_DIR.parent), env=env)

    capture = json.loads(CAPTURE_JSON_PATH.read_text(encoding="utf-8"))
    if capture.get("fatal"):
        raise RuntimeError(capture["fatal"])

    results = capture.get("results") or []
    if len(results) != 6:
        raise RuntimeError(f"expected 6 captured scenes, got {len(results)}")

    converted_paths: list[Path] = []
    removed_source_webms: list[Path] = []
    logs: list[str] = []
    real_browser_count = 0
    attempted_real_count = 0
    fallback_count = 0
    for idx, item in enumerate(results, start=1):
        webm = Path(item["webm"])
        if not webm.exists() or webm.stat().st_size < 1000:
            raise RuntimeError(f"raw scene missing or too small: {webm}")
        if item.get("real_browser"):
            real_browser_count += 1
            if not item.get("privacy_ok"):
                raise RuntimeError(f"real browser scene rejected: {item.get('name')} reason={item.get('reason')}")
        if item.get("attempted_real"):
            attempted_real_count += 1
        if item.get("attempted_real") and not item.get("real_browser"):
            fallback_count += 1
        mp4 = RAW_DIR / f"{RUN_ID}_scene{idx:02d}.mp4"
        start_offset = 0.0
        if item.get("name") == "scene2_google_flights_search":
            start_offset = 6.6
        elif item.get("name") == "scene3_google_flights_results":
            start_offset = 8.6
        elif item.get("name") == "scene4_duckai_prompt":
            start_offset = 2.0
        elif item.get("name") == "scene5_google_search_proof":
            start_offset = 2.8
        convert_clip(webm, mp4, start_offset=start_offset)
        converted_paths.append(mp4)
        logs.append(
            f"scene{idx} name={item.get('name')} real_browser={item.get('real_browser')} "
            f"attempted_real={item.get('attempted_real')} privacy_ok={item.get('privacy_ok')} "
            f"reason={item.get('reason') or 'ok'} fallback_reason={item.get('fallback_reason') or ''} "
            f"trim_start={start_offset:.2f} webm={webm} mp4={mp4}"
        )
        try:
            webm.unlink()
            removed_source_webms.append(webm)
        except FileNotFoundError:
            pass

    concat_clips(converted_paths)
    make_audio()
    dialogue_count = make_captions(converted_paths)
    mux_final()
    contact_sheet, review_frames = make_review_artifacts()
    final_probe = probe(FINAL_PATH)

    LOG_PATH.write_text(
        "\n".join(
            [
                f"final={FINAL_PATH}",
                f"profile_path_actually_used={capture.get('profile_path')}",
                f"contact_sheet={contact_sheet}",
                f"review_frames={' | '.join(str(p) for p in review_frames)}",
                f"source_webms_removed={' | '.join(str(p) for p in removed_source_webms)}",
                f"raw_clips={' | '.join(str(p) for p in converted_paths)}",
                f"audio={AUDIO_PATH} provider=pyttsx3_offline size={AUDIO_PATH.stat().st_size}",
                f"ass={ASS_PATH} dialogue_count={dialogue_count}",
                f"real_browser_scene_count={real_browser_count}",
                f"attempted_real_scene_count={attempted_real_count}",
                f"fallback_scene_count={fallback_count}",
                f"real_browser_scene_percent={(real_browser_count / max(1, len(results))) * 100:.1f}",
                f"attempted_real_scene_percent={(attempted_real_count / max(1, len(results))) * 100:.1f}",
                f"fallback_scene_percent={(fallback_count / max(1, len(results))) * 100:.1f}",
                "privacy_confirmation=dummy sandbox signed-in state/avatar/name allowed; no Gmail/account settings/payment/private document pages opened; no password fields recorded; no profile dropdown intentionally opened; real browser scenes passed rejection checks",
                "caption_source_text=" + " | ".join(SOURCE_TEXTS),
                *logs,
                final_probe,
            ]
        ),
        encoding="utf-8",
    )
    print(LOG_PATH)
    print(final_probe)


if __name__ == "__main__":
    main()
