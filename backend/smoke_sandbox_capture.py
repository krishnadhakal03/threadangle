#!/usr/bin/env python3
"""Smoke-test the authenticated sandbox Chrome profile for browser capture."""

import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import Page, async_playwright

from utils.video_pipeline import BASE_DIR, RAW_DIR, TEMP_DIR


load_dotenv(BASE_DIR / ".env")

USER_DATA_DIR = Path(os.getenv("BROWSER_SANDBOX_USER_DATA_DIR", "")).expanduser()
PROFILE_DIRECTORY = os.getenv("BROWSER_SANDBOX_PROFILE_DIRECTORY", "Profile 1")
ENABLE_AUTH_SANDBOX_CAPTURE = os.getenv("ENABLE_AUTH_SANDBOX_CAPTURE", "0") == "1"
PLAYWRIGHT_USER_DATA_DIR = (
    USER_DATA_DIR / PROFILE_DIRECTORY
    if (USER_DATA_DIR / PROFILE_DIRECTORY).exists()
    else USER_DATA_DIR
)

OUT_DIR = RAW_DIR
REVIEW_DIR = BASE_DIR / "generated_videos" / "review" / "sandbox_smoke"
LOG_PATH = TEMP_DIR / "sandbox_smoke_capture.log"

PRIVATE_TERMS = [
    "@gmail.com",
    "@outlook.com",
    "@yahoo.com",
    "password",
    "payment",
    "inbox",
    "manage your google account",
    "personal info",
]

BLOCK_TERMS = [
    "captcha",
    "verify you are human",
    "unusual traffic",
]


def run(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed: {result.stderr[-4000:]}")
    return result


def convert_clip(src: Path, dst: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-t",
            "5",
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "tpad=stop_mode=clone:stop_duration=1,fps=30",
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


def probe(path: Path) -> str:
    return run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,avg_frame_rate,duration,nb_frames:format=size,duration,filename",
            "-of",
            "default=nw=1",
            str(path),
        ],
        f"probe {path.name}",
    ).stdout.strip()


async def install_privacy_mask(page: Page) -> None:
    css = """
[aria-label*="Google Account" i],
[aria-label*="Account" i],
[aria-label*="profile" i],
a[href*="accounts.google"],
a[href*="SignOutOptions"],
img[src*="googleusercontent"],
img[alt*="profile" i],
button:has(img) {
  visibility: hidden !important;
}
body::after {
  content: "";
  position: fixed;
  top: 0;
  right: 0;
  width: 230px;
  height: 100px;
  background: #fff;
  z-index: 2147483647;
  pointer-events: none;
}
"""
    await page.add_style_tag(content=css)


async def page_risk(page: Page, allow_sign_in: bool = False) -> tuple[str, bool, bool]:
    sign_in_visible = False
    try:
        sign_in_visible = await page.locator(
            "a[href*='ServiceLogin'], a[href*='accounts.google.com'], "
            "a[aria-label*='Sign in' i], button:has-text('Sign in'), a:has-text('Sign in')"
        ).first.is_visible(timeout=700)
    except Exception:
        sign_in_visible = False
    try:
        await install_privacy_mask(page)
    except Exception:
        pass
    text = ""
    try:
        text = (await page.locator("body").inner_text(timeout=4000)).lower()
    except Exception:
        return "body_text_unavailable", False, False
    email_visible = any(term in text for term in ["@gmail.com", "@outlook.com", "@yahoo.com"])
    avatar_visible = False
    try:
        avatar_visible = await page.locator(
            "[aria-label*='Google Account' i], img[src*='googleusercontent'], a[href*='SignOutOptions']"
        ).first.is_visible(timeout=500)
    except Exception:
        avatar_visible = False
    for term in PRIVATE_TERMS:
        if term in text:
            return f"private_data_visible:{term}", email_visible, avatar_visible
    for term in BLOCK_TERMS:
        if term in text:
            return f"blocked:{term}", email_visible, avatar_visible
    if not allow_sign_in and "sign in" in text:
        return "login_visible:sign in", email_visible, avatar_visible
    if not allow_sign_in and sign_in_visible:
        return "login_visible:sign in button", email_visible, avatar_visible
    return "", email_visible, avatar_visible


async def capture_smoke(name: str, url: str, allow_sign_in: bool = False) -> dict:
    result = {
        "name": name,
        "url": url,
        "launched": False,
        "recorded": False,
        "path": "",
        "reason": "",
        "email_visible": False,
        "avatar_visible": False,
        "probe": "",
    }
    video_dir = TEMP_DIR / f"{name}_native_video"
    shutil.rmtree(video_dir, ignore_errors=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    playwright = None
    context = None
    try:
        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(PLAYWRIGHT_USER_DATA_DIR),
            channel="chrome",
            headless=False,
            viewport={"width": 1080, "height": 1920},
            record_video_dir=str(video_dir),
            record_video_size={"width": 1080, "height": 1920},
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=1080,1920",
                "--window-position=40,20",
            ],
            timeout=45000,
        )
        result["launched"] = True
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(1200)
        reason, email_visible, avatar_visible = await page_risk(page, allow_sign_in=allow_sign_in)
        result["email_visible"] = email_visible
        result["avatar_visible"] = avatar_visible
        if reason:
            result["reason"] = reason
            video = page.video
            await page.close()
            _ = await video.path()
            return result
        await install_privacy_mask(page)
        await page.mouse.move(740, 780, steps=18)
        await page.wait_for_timeout(500)
        await page.mouse.wheel(0, 720)
        await page.wait_for_timeout(1200)
        await page.mouse.wheel(0, -180)
        await page.wait_for_timeout(1500)
        video = page.video
        await page.close()
        raw_webm = Path(await video.path())
        await context.close()
        context = None
        out_path = OUT_DIR / f"{name}.mp4"
        convert_clip(raw_webm, out_path)
        result["recorded"] = True
        result["path"] = str(out_path)
        result["probe"] = probe(out_path)
    except Exception as exc:
        result["reason"] = f"exception:{str(exc)[:2000]}"
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
    return result


async def main() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    if not ENABLE_AUTH_SANDBOX_CAPTURE:
        results.append({"name": "config", "reason": "ENABLE_AUTH_SANDBOX_CAPTURE is not enabled"})
    elif not USER_DATA_DIR.exists():
        results.append({"name": "config", "reason": f"user_data_dir_missing:{USER_DATA_DIR}"})
    else:
        results.append(
            await capture_smoke(
                "sandbox_google_flights_smoke",
                "https://www.google.com/travel/flights",
                allow_sign_in=False,
            )
        )
        results.append(
            await capture_smoke(
                "sandbox_duckduckgo_smoke",
                "https://duckduckgo.com/?q=cheap+flights+flexible+dates+nearby+airports",
                allow_sign_in=True,
            )
        )

    recorded_paths = [Path(r["path"]) for r in results if r.get("recorded") and r.get("path")]
    contact_sheet = REVIEW_DIR / "sandbox_smoke_contact_sheet.jpg"
    if len(recorded_paths) == 1:
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(recorded_paths[0]),
                "-vf",
                "scale=270:-1",
                "-frames:v",
                "1",
                "-update",
                "1",
                str(contact_sheet),
            ],
            "contact sheet",
        )
    elif recorded_paths:
        inputs = []
        for path in recorded_paths:
            inputs.extend(["-i", str(path)])
        labels = "".join(f"[{idx}:v]scale=270:-1[v{idx}];" for idx in range(len(recorded_paths)))
        stack_inputs = "".join(f"[v{idx}]" for idx in range(len(recorded_paths)))
        filter_complex = f"{labels}{stack_inputs}hstack=inputs={len(recorded_paths)}[out]"
        run(
            [
                "ffmpeg",
                "-y",
                *inputs,
                "-filter_complex",
                filter_complex,
                "-map",
                "[out]",
                "-frames:v",
                "1",
                "-update",
                "1",
                str(contact_sheet),
            ],
            "contact sheet",
        )

    log = {
        "user_data_dir": str(USER_DATA_DIR),
        "profile_directory": PROFILE_DIRECTORY,
        "playwright_user_data_dir": str(PLAYWRIGHT_USER_DATA_DIR),
        "contact_sheet": str(contact_sheet) if contact_sheet.exists() else "",
        "results": results,
    }
    LOG_PATH.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
