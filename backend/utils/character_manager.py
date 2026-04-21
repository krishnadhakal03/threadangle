import io
import json
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image

from integrations.gemini_images import GeminiImageGenerator


class CharacterManager:
    """Manage generated, uploaded, and preset character image sources."""

    def __init__(self) -> None:
        self.gemini = GeminiImageGenerator()
        self.preset_library = self._load_preset_library()

    async def get_character_image_result(
        self,
        source: str,
        scene_description: str,
        character_id: Optional[str] = None,
        uploaded_image: Optional[bytes] = None,
        character_profile: Optional[Dict[str, Any]] = None,
        image_provider: str = "pollinations",
        variation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        source = (source or "generate").lower()
        profile = character_profile or {}

        if source == "generate":
            return await self.gemini.generate_character_image(
                scene_description=scene_description,
                character_type=profile.get("type", "professional person"),
                style=profile.get("style", "photorealistic"),
                consistent_features=profile,
                image_provider=image_provider,
                variation_token=variation_token,
            )

        if source == "upload":
            if not uploaded_image:
                raise ValueError("No image provided for upload source")
            image = Image.open(io.BytesIO(uploaded_image)).convert("RGB")
            image = image.resize((720, 1280), Image.Resampling.LANCZOS)
            return {
                "image": image,
                "image_url": self._to_data_url(image),
                "prompt_used": "uploaded image",
                "credits_used": 0,
                "width": 720,
                "height": 1280,
                "provider": "upload",
            }

        if source == "preset":
            preset = self.preset_library.get(character_id or "")
            if not preset:
                raise ValueError(f"Preset character {character_id} not found")
            image = Image.open(preset["image_path"]).convert("RGB")
            image = image.resize((720, 1280), Image.Resampling.LANCZOS)
            return {
                "image": image,
                "image_url": self._to_data_url(image),
                "prompt_used": "preset character",
                "credits_used": 0,
                "width": 720,
                "height": 1280,
                "provider": "preset",
                "preset": preset,
            }

        raise ValueError(f"Unknown character source: {source}")

    async def get_character_image(self, **kwargs) -> Image.Image:
        result = await self.get_character_image_result(**kwargs)
        return result["image"]

    def _load_preset_library(self) -> Dict[str, Dict[str, Any]]:
        manifest = Path(__file__).resolve().parents[1] / "characters" / "presets" / "library.json"
        if not manifest.exists():
            return {}

        try:
            raw = json.loads(manifest.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                presets = {}
                for item in raw:
                    pid = str(item.get("id") or "").strip()
                    path_val = item.get("image_path")
                    if not pid or not path_val:
                        continue
                    path = Path(path_val)
                    if not path.is_absolute():
                        path = Path(__file__).resolve().parents[1] / path
                    if not path.exists():
                        continue
                    item["image_path"] = str(path)
                    presets[pid] = item
                return presets
            if isinstance(raw, dict):
                return raw
        except Exception:
            return {}
        return {}

    @staticmethod
    def _to_data_url(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return "data:image/png;base64," + __import__("base64").b64encode(buffer.getvalue()).decode("utf-8")
