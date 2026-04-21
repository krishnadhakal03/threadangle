import base64
import asyncio
import io
import os
import tempfile
import time
import uuid

import httpx
import requests
from PIL import Image

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


class RunwayMLClient:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or RUNWAYML_API_KEY
        self.model = model or RUNWAYML_MODEL
        if not self.api_key:
            raise ValueError("RunwayML API key not set.")

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": RUNWAYML_API_VERSION,
        }

    def generate_video(self, prompt, num_frames=24, seed=None, motion="cinematic", max_retries=2):
        duration_seconds = max(2, int(round(float(num_frames) / 12.0)))
        duration_bucket = 5 if duration_seconds <= 6 else 10
        data = {
            "model": self.model,
            "promptText": prompt,
            "duration": duration_bucket,
            "ratio": "720:1280",
        }
        # Keep backward-compatible fields; ignored by newer endpoints.
        data["prompt"] = prompt
        data["num_frames"] = num_frames
        data["motion"] = motion
        if seed is not None:
            data["seed"] = seed

        headers = self._headers
        for attempt in range(max_retries):
            response = requests.post(RUNWAYML_API_URL, json=data, headers=headers)
            if response.status_code in (200, 201):
                ctype = (response.headers.get("content-type") or "").lower()
                # Legacy/direct binary response
                if "video" in ctype or "application/octet-stream" in ctype:
                    out_path = f"runwayml_{int(time.time())}.mp4"
                    with open(out_path, "wb") as f:
                        f.write(response.content)
                    return out_path

                # Current API returns async task JSON
                task_payload = response.json() if response.text else {}
                task_id = task_payload.get("id") or task_payload.get("taskId")
                if not task_id:
                    raise Exception(f"RunwayML returned success but no task id: {task_payload}")

                return self._poll_and_download_task(task_id, headers=headers)
            elif response.status_code == 402:
                # Payment required / quota exceeded
                raise RunwayMLQuotaError("RunwayML quota exceeded or payment required.")
            elif response.status_code == 400 and "enough credits" in (response.text or "").lower():
                raise RunwayMLQuotaError("RunwayML credits are insufficient for this task.")
            elif response.status_code == 429:
                # Rate limit, back off and retry
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
        img_base64 = self._image_to_base64(image)

        async with httpx.AsyncClient(timeout=90.0) as client:
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
        task_url = RUNWAYML_TASK_URL.format(task_id=task_id)
        start = time.time()

        while time.time() - start < timeout_seconds:
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
        task_url = RUNWAYML_TASK_URL.format(task_id=task_id)
        start = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            while time.time() - start < timeout_seconds:
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
        # Official API pricing: https://docs.dev.runwayml.com/guides/pricing
        # gen4.5: 12 credits/sec, gen4_turbo: 5 credits/sec, gen4_aleph: 15/sec
        credits_per_second = {"gen4.5": 12, "gen4_turbo": 5, "gen4_aleph": 15}
        return duration * credits_per_second.get(model, 12)

    def check_quota(self):
        # RunwayML does not have a public quota endpoint, so we can only infer from errors
        # Optionally, implement a test call with a minimal prompt to check quota
        pass
