import base64
import asyncio
import io
import os
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import requests
from PIL import Image

from utils.paid_provider_guard import PaidProviderBlockedError, assert_paid_provider_allowed

try:
    import cv2  # type: ignore[reportMissingImports]
except Exception:
    cv2 = None

RUNWAYML_API_KEY = os.getenv("RUNWAYML_API_KEY")
RUNWAYML_API_URL = os.getenv("RUNWAYML_API_URL", "https://api.dev.runwayml.com/v1/text_to_video")
RUNWAYML_IMAGE_TO_VIDEO_URL = os.getenv("RUNWAYML_IMAGE_TO_VIDEO_URL", "https://api.dev.runwayml.com/v1/image_to_video")
RUNWAYML_API_VERSION = os.getenv("RUNWAYML_API_VERSION", "2024-11-06")
RUNWAYML_TASK_URL = os.getenv("RUNWAYML_TASK_URL", "https://api.dev.runwayml.com/v1/tasks/{task_id}")
RUNWAYML_MODEL = os.getenv("RUNWAYML_MODEL", "gen4.5")

class RunwayMLQuotaError(Exception):
    pass


def _write_blocked_runway_fallback_video(prompt: str, duration: int = 5, ratio: str = "720:1280") -> str:
    """Create a local/free fallback clip and return a file path.

    This is intentionally inside the Runway client module so direct image_to_video /
    extend_video callers also get a no-spend fallback instead of a fatal error.
    """
    from PIL import ImageDraw, ImageFont
    import numpy as np
    from moviepy.editor import ImageSequenceClip

    width, height = (720, 1280)
    if str(ratio).replace(" ", "") in {"1280:720", "16:9"}:
        width, height = (1280, 720)

    out_dir = Path(__file__).resolve().parents[1] / "generated_videos" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"runway_blocked_fallback_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp4"

    fps = 24
    frame_count = max(1, int(max(2, duration) * fps))
    safe_prompt = " ".join(str(prompt or "AI scene").split())[:140]

    try:
        title_font = ImageFont.truetype("arialbd.ttf", 48)
        body_font = ImageFont.truetype("arial.ttf", 30)
        small_font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    def wrap(draw, text, font, max_width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines[:5]

    frames = []
    for i in range(frame_count):
        p = i / max(1, frame_count - 1)
        img = Image.new("RGB", (width, height), (7, 12, 24))
        draw = ImageDraw.Draw(img)
        draw.ellipse([-width * 0.25 + int(80 * p), 80, width * 0.75, height * 0.55], fill=(8, 70, 78))
        draw.ellipse([width * 0.30, height * 0.35 - int(90 * p), width * 1.25, height * 1.1], fill=(44, 26, 92))
        pad = int(width * 0.075)
        draw.rounded_rectangle([pad, int(height * 0.15), width - pad, int(height * 0.85)], radius=34, fill=(13, 20, 35), outline=(90, 235, 210), width=3)
        draw.text((pad + 26, int(height * 0.22)), "LOCAL FALLBACK", font=title_font, fill=(255, 255, 255))
        draw.text((pad + 26, int(height * 0.29)), "Runway blocked — no paid credits used", font=small_font, fill=(130, 255, 210))
        y = int(height * 0.40)
        for line in wrap(draw, safe_prompt, body_font, width - 2 * pad - 52):
            draw.text((pad + 26, y), line, font=body_font, fill=(242, 246, 255))
            y += 45
        bar_w = int((width - 2 * pad - 52) * (0.2 + 0.8 * p))
        draw.rounded_rectangle([pad + 26, int(height * 0.75), pad + 26 + bar_w, int(height * 0.77)], radius=10, fill=(90, 160, 255))
        frames.append(np.array(img))

    clip = ImageSequenceClip(frames, fps=fps)
    clip.write_videofile(
        str(out_path),
        fps=fps,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )
    clip.close()
    return str(out_path)


class RunwayMLClient:
    def __init__(self, api_key=None, model=None):
        self._blocked = False
        self._blocked_reason = None
        try:
            assert_paid_provider_allowed("runwayml")
        except PaidProviderBlockedError as exc:
            self._blocked = True
            self._blocked_reason = str(exc)
        self.api_key = api_key or RUNWAYML_API_KEY
        self.model = model or RUNWAYML_MODEL
        if not self._blocked and not self.api_key:
            raise ValueError("RunwayML API key not set.")

    @property
    def _headers(self):
        assert_paid_provider_allowed("runwayml")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": RUNWAYML_API_VERSION,
        }

    def generate_video(self, prompt, num_frames=24, seed=None, motion="cinematic", max_retries=2):
        if self._blocked:
            print(f"[RUNWAYML] Blocked by backend safety; using local fallback: {self._blocked_reason}")
            return _write_blocked_runway_fallback_video(prompt, duration=max(2, int(round(float(num_frames) / 12.0))))
        assert_paid_provider_allowed("runwayml")
        duration_seconds = max(2, int(round(float(num_frames) / 12.0)))
        duration_bucket = 5 if duration_seconds <= 6 else 10
        data = {
            "model": self.model,
            "promptText": prompt,
            "duration": duration_bucket,
            "ratio": "720:1280",
        }
        data["prompt"] = prompt
        data["num_frames"] = num_frames
        data["motion"] = motion
        if seed is not None:
            data["seed"] = seed

        headers = self._headers
        for attempt in range(max_retries):
            assert_paid_provider_allowed("runwayml")
            response = requests.post(RUNWAYML_API_URL, json=data, headers=headers)
            if response.status_code in (200, 201):
                ctype = (response.headers.get("content-type") or "").lower()
                if "video" in ctype or "application/octet-stream" in ctype:
                    out_path = f"runwayml_{int(time.time())}.mp4"
                    with open(out_path, "wb") as f:
                        f.write(response.content)
                    return out_path

                task_payload = response.json() if response.text else {}
                task_id = task_payload.get("id") or task_payload.get("taskId")
                if not task_id:
                    raise Exception(f"RunwayML returned success but no task id: {task_payload}")

                return self._poll_and_download_task(task_id, headers=headers)
            elif response.status_code == 402:
                raise RunwayMLQuotaError("RunwayML quota exceeded or payment required.")
            elif response.status_code == 400 and "enough credits" in (response.text or "").lower():
                raise RunwayMLQuotaError("RunwayML credits are insufficient for this task.")
            elif response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            elif response.status_code == 400 and "X-Runway-Version header" in (response.text or ""):
                raise Exception(
                    "RunwayML version header rejected. "
                    "Set RUNWAYML_API_VERSION to the value shown in current Runway docs. "
                    f"Current configured value: {RUNWAYML_API_VERSION}. Raw response: {response.text}"
                )
            elif response.status_code == 404 and "/v1/generate/video" in RUNWAYML_API_URL:
                raise Exception(
                    "RunwayML endpoint not found (legacy URL). "
                    "Set RUNWAYML_API_URL=https://api.dev.runwayml.com/v1/text_to_video"
                )
            else:
                raise Exception(f"RunwayML error: {response.status_code} {response.text}")
        raise Exception("RunwayML API failed after retries.")

    async def image_to_video(self, image: Image.Image, prompt: str, duration: int = 5, model: str = "gen4.5", ratio: str = "720:1280"):
        if self._blocked:
            print(f"[RUNWAYML] image_to_video blocked by backend safety; using local fallback: {self._blocked_reason}")
            local_path = _write_blocked_runway_fallback_video(prompt, duration=duration, ratio=ratio)
            return {
                "video_url": local_path,
                "video_path": local_path,
                "task_id": None,
                "credits_used": 0,
                "duration": duration,
                "method": "local_fallback_runway_blocked",
                "paid_provider_blocked": True,
            }
        assert_paid_provider_allowed("runwayml")
        img_base64 = self._image_to_base64(image)

        async with httpx.AsyncClient(timeout=90.0) as client:
            assert_paid_provider_allowed("runwayml")
            response = await client.post(
                RUNWAYML_IMAGE_TO_VIDEO_URL,
                headers=self._headers,
                json={
                    "model": model,
                    "promptImage": f"data:image/png;base64,{img_base64}",
                    "promptText": prompt,
                    "duration": duration,
                    "ratio": ratio,
                },
            )

        if response.status_code in (402, 429):
            raise RunwayMLQuotaError("RunwayML quota exceeded or insufficient credits.")
        if response.status_code not in (200, 201):
            raise Exception(f"RunwayML image-to-video error: {response.status_code} {response.text}")

        payload = response.json() if response.text else {}
        task_id = payload.get("id") or payload.get("taskId")
        if not task_id:
            raise Exception(f"RunwayML image-to-video response missing task id: {payload}")

        video_url = await self._poll_task_url(task_id)
        return {
            "video_url": video_url,
            "task_id": task_id,
            "credits_used": self._calculate_credits(duration=duration, model=model, method="image_to_video"),
            "duration": duration,
            "method": "image_to_video",
        }

    async def extend_video(self, previous_video_url: str, prompt: str, duration: int = 5, model: str = "gen4.5", ratio: str = "720:1280"):
        if self._blocked:
            print(f"[RUNWAYML] extend_video blocked by backend safety; using local fallback: {self._blocked_reason}")
            local_path = _write_blocked_runway_fallback_video(prompt, duration=duration, ratio=ratio)
            return {
                "video_url": local_path,
                "video_path": local_path,
                "task_id": None,
                "credits_used": 0,
                "duration": duration,
                "method": "local_fallback_runway_blocked",
                "paid_provider_blocked": True,
            }
        assert_paid_provider_allowed("runwayml")
        if cv2 is None:
            raise RuntimeError("opencv-python is required for extend_video.")

        async with httpx.AsyncClient(timeout=120.0) as client:
            prev = await client.get(previous_video_url)
        if prev.status_code != 200:
            raise Exception(f"Unable to fetch previous clip: {prev.status_code}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uuid.uuid4().hex}.mp4") as tmp:
            tmp.write(prev.content)
            temp_path = tmp.name

        last_frame_b64 = self._extract_last_frame(temp_path)

        async with httpx.AsyncClient(timeout=90.0) as client:
            assert_paid_provider_allowed("runwayml")
            response = await client.post(
                RUNWAYML_IMAGE_TO_VIDEO_URL,
                headers=self._headers,
                json={
                    "model": model,
                    "promptImage": f"data:image/png;base64,{last_frame_b64}",
                    "promptText": prompt,
                    "duration": duration,
                    "ratio": ratio,
                },
            )

        if response.status_code in (402, 429):
            raise RunwayMLQuotaError("RunwayML quota exceeded or insufficient credits.")
        if response.status_code not in (200, 201):
            raise Exception(f"RunwayML extend error: {response.status_code} {response.text}")

        payload = response.json() if response.text else {}
        task_id = payload.get("id") or payload.get("taskId")
        if not task_id:
            raise Exception(f"RunwayML extend response missing task id: {payload}")

        video_url = await self._poll_task_url(task_id)
        return {
            "video_url": video_url,
            "task_id": task_id,
            "credits_used": self._calculate_credits(duration=duration, model=model, method="extend"),
            "duration": duration,
            "method": "extend",
        }

    def _poll_and_download_task(self, task_id: str, headers: dict, timeout_seconds: int = 600) -> str:
        assert_paid_provider_allowed("runwayml")
        task_url = RUNWAYML_TASK_URL.format(task_id=task_id)
        start = time.time()

        while time.time() - start < timeout_seconds:
            assert_paid_provider_allowed("runwayml")
            resp = requests.get(task_url, headers=headers)
            if resp.status_code != 200:
                raise Exception(f"RunwayML task poll error: {resp.status_code} {resp.text}")

            payload = resp.json() if resp.text else {}
            status = str(payload.get("status") or payload.get("state") or "").upper()
            if status in ("SUCCEEDED", "SUCCESS", "COMPLETED"):
                output_url = self._extract_output_url(payload)
                if not output_url:
                    raise Exception(f"RunwayML task succeeded but no output URL in payload: {payload}")

                out_path = f"runwayml_{int(time.time())}.mp4"
                dl = requests.get(output_url, timeout=120)
                if dl.status_code != 200:
                    raise Exception(f"RunwayML output download failed: {dl.status_code} {dl.text[:300]}")
                with open(out_path, "wb") as f:
                    f.write(dl.content)
                return out_path

            if status in ("FAILED", "ERROR", "CANCELED", "CANCELLED"):
                reason = payload.get("failure") or payload.get("error") or payload
                raise Exception(f"RunwayML task failed: {reason}")

            time.sleep(2)

        raise Exception(f"RunwayML task timed out after {timeout_seconds}s (task_id={task_id})")

    def _extract_output_url(self, payload: dict) -> str | None:
        output = payload.get("output")
        if isinstance(output, list) and output:
            first = output[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                return first.get("url") or first.get("videoUrl")
        if isinstance(output, dict):
            return output.get("url") or output.get("videoUrl")
        return payload.get("url") or payload.get("videoUrl")

    async def _poll_task_url(self, task_id: str, timeout_seconds: int = 600) -> str:
        assert_paid_provider_allowed("runwayml")
        task_url = RUNWAYML_TASK_URL.format(task_id=task_id)
        start = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            while time.time() - start < timeout_seconds:
                assert_paid_provider_allowed("runwayml")
                resp = await client.get(task_url, headers=self._headers)
                if resp.status_code != 200:
                    raise Exception(f"RunwayML task poll error: {resp.status_code} {resp.text}")

                payload = resp.json() if resp.text else {}
                status = str(payload.get("status") or payload.get("state") or "").upper()
                if status in ("SUCCEEDED", "SUCCESS", "COMPLETED"):
                    output_url = self._extract_output_url(payload)
                    if not output_url:
                        raise Exception(f"RunwayML task succeeded but no output URL: {payload}")
                    return output_url
                if status in ("FAILED", "ERROR", "CANCELED", "CANCELLED"):
                    reason = payload.get("failure") or payload.get("error") or payload
                    raise Exception(f"RunwayML task failed: {reason}")
                await asyncio.sleep(2)

        raise Exception(f"RunwayML task timed out after {timeout_seconds}s (task_id={task_id})")

    def _extract_last_frame(self, video_path: str) -> str:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(total_frames - 1, 0))
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise Exception("Failed to extract last frame")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        return self._image_to_base64(image)

    def _image_to_base64(self, image: Image.Image) -> str:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _calculate_credits(self, duration: int, model: str, method: str):
        credits_per_second = {"gen4.5": 12, "gen4_turbo": 5, "gen4_aleph": 15}
        return duration * credits_per_second.get(model, 12)

    def check_quota(self):
        pass
