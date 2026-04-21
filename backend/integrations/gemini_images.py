import asyncio
import base64
import os
import re
import time
import urllib.parse
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

try:
    import httpx as _httpx  # type: ignore[reportMissingImports]
except Exception:
    _httpx = None

from PIL import Image, ImageDraw

try:
    from google import genai as _new_genai  # type: ignore[reportMissingImports]
    from google.genai import types as _genai_types  # type: ignore[reportMissingImports]
except Exception:
    _new_genai = None
    _genai_types = None

# Module-level counters — survive new GeminiImageGenerator instantiations within the same process.
_gemini_used_today: int = 0
_gemini_quota_exhausted_until: float = 0.0  # epoch seconds; module-level so new instances share it


class GeminiImageGenerator:
    """
    Generate character images with Gemini image output.
    Falls back to deterministic placeholder images when API/key is unavailable.
    """

    def __init__(self) -> None:
        self.api_key = (os.getenv("GOOGLE_GEMINI_API_KEY") or "").strip()
        self.hf_token = (os.getenv("HF_TOKEN") or "").strip()
        self.model_name = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
        self.daily_quota = int(os.getenv("GEMINI_DAILY_QUOTA", "500"))
        self._client = None
        self._use_pollinations = os.getenv("GEMINI_USE_POLLINATIONS", "1") != "0"

        if _new_genai and self.api_key:
            self._client = _new_genai.Client(api_key=self.api_key)
            print(f"[Gemini] Initialized client with model: {self.model_name}")
        else:
            print(f"[Gemini] WARNING — Gemini client NOT initialized. Using Pollinations.ai (free) for storyboard images.")

    async def generate_character_image(
        self,
        scene_description: str,
        character_type: str = "professional person",
        style: str = "photorealistic",
        consistent_features: Optional[Dict[str, Any]] = None,
        image_provider: str = "pollinations",  # "pollinations" | "gemini"
        variation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        global _gemini_used_today
        if image_provider == "gemini" and _gemini_used_today >= self.daily_quota:
            raise RuntimeError(f"Gemini daily quota exceeded ({self.daily_quota}/day).")

        prompt = self._build_character_prompt(
            scene_description=scene_description,
            character_type=character_type,
            style=style,
            consistent_features=consistent_features or {},
            variation_token=variation_token,
        )

        image = None
        provider = "fallback"
        use_gemini_first = (image_provider == "gemini")
        use_hf = (image_provider == "huggingface")

        # --- Gemini path (paid) ---
        if use_gemini_first and self._client:
            if time.time() < _gemini_quota_exhausted_until:
                remaining = int(_gemini_quota_exhausted_until - time.time())
                print(f"[Gemini] Quota cooldown active — {remaining}s remaining, falling back to Pollinations")
            else:
                image = await self._generate_with_gemini(prompt)
                if image is not None:
                    provider = "gemini"

        # --- Hugging Face path (free with token, FLUX.1-schnell) ---
        if image is None and use_hf:
            if not self.hf_token:
                print("[HuggingFace] HF_TOKEN not set — falling back to Pollinations")
            else:
                image = await self._generate_with_huggingface(prompt, variation_token=variation_token)
                if image is not None:
                    provider = "huggingface"

        # --- Pollinations path (free, no key) ---
        # Used when: provider=pollinations (default), OR gemini/hf failed
        if image is None and self._use_pollinations and _httpx is not None:
            image = await self._generate_with_pollinations(prompt, variation_token=variation_token)
            if image is not None:
                provider = "pollinations"

        # --- Last resort: deterministic coloured placeholder ---
        if image is None:
            image = self._generate_placeholder_image(
                scene_description=scene_description,
                character_type=character_type,
                consistent_features=consistent_features or {},
            )

        # Resize to 720×1280 (RunwayML portrait optimal input size)
        image = image.resize((720, 1280), Image.Resampling.LANCZOS)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        if provider == "gemini":
            _gemini_used_today += 1
        return {
            "image": image,
            "image_url": f"data:image/png;base64,{img_str}",
            "prompt_used": prompt,
            "credits_used": 0,
            "width": 720,
            "height": 1280,
            "provider": provider,
        }

    async def generate_scene_sequence(self, scenes: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for idx, scene in enumerate(scenes):
            result = await self.generate_character_image(
                scene_description=scene.get("description", "Presenter speaking to camera"),
                character_type=character_profile.get("type", "professional person"),
                style=character_profile.get("style", "photorealistic"),
                consistent_features=character_profile,
            )
            results.append(
                {
                    **result,
                    "scene_index": idx,
                    "scene_description": scene.get("description", ""),
                    "duration": int(scene.get("duration", 5) or 5),
                }
            )
        return results

    async def _generate_with_pollinations(self, prompt: str, variation_token: Optional[str] = None) -> Optional[Image.Image]:
        """Fetch an image from Pollinations.ai — completely free, no API key required."""
        encoded = urllib.parse.quote(prompt)
        seed_basis = f"{prompt}|{variation_token or 'base'}|{time.time_ns() if variation_token else ''}"
        seed = abs(hash(seed_basis)) % 99999
        # Request at full 1080p portrait resolution for RunwayML input quality
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model=flux&nologo=true&enhance=true&seed={seed}"
        for attempt in range(2):  # retry once on 429 or timeout
            try:
                async with _httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code == 200:
                        print(f"[Pollinations] Image generated OK ({len(resp.content)} bytes)")
                        return Image.open(BytesIO(resp.content)).convert("RGB")
                    elif resp.status_code == 429:
                        wait = 6 if attempt == 0 else 0
                        print(f"[Pollinations] HTTP 429 — {'retrying in ' + str(wait) + 's' if wait else 'giving up'}")
                        if wait:
                            await asyncio.sleep(wait)
                            continue
                        return None
                    else:
                        print(f"[Pollinations] HTTP {resp.status_code} — falling back to placeholder")
                        return None
            except Exception as exc:
                print(f"[Pollinations] Request failed (attempt {attempt+1}): {type(exc).__name__}: {exc}")
                if attempt == 0:
                    await asyncio.sleep(3)
                    continue
                return None
        return None

    async def _generate_with_huggingface(self, prompt: str, variation_token: Optional[str] = None) -> Optional[Image.Image]:
        """
        Fetch an image from Hugging Face Inference API using FLUX.1-schnell.
        Free with an HF_TOKEN (rate-limited). Higher quality than Pollinations.
        Docs: https://huggingface.co/docs/api-inference/tasks/text-to-image
        """
        HF_MODEL = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
        api_url = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"

        variant_prompt = f"{prompt}\nVariation cue: {variation_token}" if variation_token else prompt

        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json",
            "Accept": "image/png",
        }
        payload = {
            "inputs": variant_prompt,
            "parameters": {
                "width": 720,
                "height": 1280,
                "num_inference_steps": 4,   # schnell is distilled — 4 steps is optimal
                "guidance_scale": 0.0,      # schnell uses CFG=0
            },
        }

        for attempt in range(2):
            try:
                async with _httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(api_url, headers=headers, json=payload)

                if resp.status_code == 200:
                    print(f"[HuggingFace] Image generated OK ({len(resp.content)} bytes, model={HF_MODEL})")
                    return Image.open(BytesIO(resp.content)).convert("RGB")

                elif resp.status_code == 503:
                    # Model loading (cold start) — HF returns estimated_time
                    try:
                        info = resp.json()
                        wait = min(float(info.get("estimated_time", 20)), 30)
                    except Exception:
                        wait = 20
                    print(f"[HuggingFace] Model loading, waiting {wait:.0f}s...")
                    await asyncio.sleep(wait)
                    continue

                elif resp.status_code == 429:
                    print(f"[HuggingFace] Rate limited — falling back to Pollinations")
                    return None

                elif resp.status_code == 401:
                    print(f"[HuggingFace] Invalid HF_TOKEN — check your token at https://huggingface.co/settings/tokens")
                    return None

                else:
                    print(f"[HuggingFace] HTTP {resp.status_code}: {resp.text[:200]}")
                    if attempt == 0:
                        await asyncio.sleep(3)
                        continue
                    return None

            except Exception as exc:
                print(f"[HuggingFace] Request failed (attempt {attempt+1}): {type(exc).__name__}: {exc}")
                if attempt == 0:
                    await asyncio.sleep(3)
                    continue
                return None
        return None

    async def _generate_with_gemini(self, prompt: str) -> Optional[Image.Image]:
        def _sync_call() -> Tuple[Optional[Image.Image], int]:
            """Returns (image_or_None, retry_delay_seconds). retry_delay > 0 means quota hit."""
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt],
                    config=_genai_types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                    ),
                )
            except Exception as exc:
                exc_str = str(exc)
                print(f"[Gemini] generate_content failed: {type(exc).__name__}: {exc}")
                if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
                    m = re.search(r"'retryDelay':\s*'(\d+)s'", exc_str)
                    delay = int(m.group(1)) if m else 60
                    return None, delay
                return None, 0

            candidates = getattr(response, "candidates", None) or []
            if not candidates:
                print(f"[Gemini] No candidates in response. Prompt feedback: {getattr(response, 'prompt_feedback', None)}")
                return None, 0

            for candidate in candidates:
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", None) or []
                for part in parts:
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data is None:
                        continue
                    data = getattr(inline_data, "data", None)
                    if data is None:
                        continue
                    try:
                        img_bytes = data if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                        return Image.open(BytesIO(img_bytes)).convert("RGB"), 0
                    except Exception as dec_exc:
                        print(f"[Gemini] Image decode failed: {dec_exc}")
                        continue

            print("[Gemini] No image data found in any part — falling back to placeholder")
            return None, 0

        image, quota_delay = await asyncio.to_thread(_sync_call)
        if quota_delay > 0:
            global _gemini_quota_exhausted_until
            _gemini_quota_exhausted_until = time.time() + quota_delay
            print(f"[Gemini] Quota exhausted — circuit breaker active for {quota_delay}s. "
                  f"Enable billing at https://aistudio.google.com to use Gemini image generation.")
        return image

    def _build_character_prompt(
        self,
        scene_description: str,
        character_type: str,
        style: str,
        consistent_features: Dict[str, Any],
        variation_token: Optional[str] = None,
    ) -> str:
        lower = (scene_description or "").lower()
        is_ui = any(token in lower for token in ["dashboard", "screen", "ui", "interface", "app", "website", "phone", "laptop", "monitor", "chart", "graph", "comparison", "split-screen"])
        is_cta = any(token in lower for token in ["cta", "call-to-action", "button", "arrow", "subscribe", "click", "tap"])
        is_montage = any(token in lower for token in ["montage", "before/after", "before-after", "multiple", "quick-cut", "sequence", "collage"])
        is_person = any(token in lower for token in ["person", "man", "woman", "face", "portrait", "presenter", "founder", "speaker", "professional"])

        prompt = [
            f"Generate a {style} vertical 9:16 image for short-form video production.",
            f"Scene brief: {scene_description}",
            "Target: 720x1280 portrait composition, cinematic lighting, crisp focal subject, no watermark, no logos, no readable text.",
        ]

        if is_ui:
            prompt.append("Composition: UI/product explainer frame. Make screens, dashboards, devices, comparison layouts, charts, or interface elements the hero of the image.")
            prompt.append("Avoid forcing a centered portrait unless the scene explicitly mentions a person on camera.")
        elif is_cta:
            prompt.append("Composition: bold high-conversion end card visual with strong focal element, clean background, directional motion, and clear call-to-action energy.")
        elif is_montage:
            prompt.append("Composition: dynamic multi-panel or before/after montage that reads clearly in a single frame.")
        elif is_person:
            prompt.append(f"Subject: {character_type}. Keep the main person visually dominant and expressive.")
        else:
            prompt.append("Composition: match the described scene literally and avoid generic stock-person framing when the scene implies objects, products, or interfaces.")

        if consistent_features and not is_ui:
            prompt.append("Maintain exact features across scenes:")
            for key, value in consistent_features.items():
                if value is None:
                    continue
                prompt.append(f"- {key}: {value}")

        if variation_token:
            prompt.append(f"Variation direction: produce a noticeably different composition and framing than previous attempts. Variant key: {variation_token}")
        return "\n".join(prompt)

    def _generate_placeholder_image(
        self,
        scene_description: str,
        character_type: str,
        consistent_features: Dict[str, Any],
    ) -> Image.Image:
        seed = f"{scene_description}|{character_type}|{sorted(consistent_features.items())}"
        palette = [
            (17, 24, 39),
            (30, 41, 59),
            (15, 23, 42),
            (51, 65, 85),
        ]
        idx = abs(hash(seed)) % len(palette)
        base = palette[idx]

        image = Image.new("RGB", (576, 1024), base)
        draw = ImageDraw.Draw(image)
        draw.ellipse((148, 140, 428, 420), fill=(230, 230, 230))
        draw.rectangle((180, 420, 396, 830), fill=(120, 120, 130))

        label = (scene_description or "Scene").strip()[:60]
        draw.rectangle((30, 880, 546, 980), fill=(0, 0, 0))
        draw.text((44, 915), label, fill=(255, 255, 255))
        return image
