"""
Multi-Layer Composition Engine

Reusable layered composition support for editorial density.
Layer slots: background_asset, foreground_annotation, proof_overlay, magnifier_crop, supporting_cutaway, caption_layer
"""

from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math
from .schema import StoryboardScene


class VisualLayer:
    """A visual layer in the composition."""

    def __init__(self, layer_type: str, asset_path: str | None = None,
                 position: Tuple[int, int] = (0, 0), size: Tuple[int, int] | None = None,
                 opacity: float = 1.0, text: str | None = None, style: Dict[str, Any] | None = None):
        self.layer_type = layer_type
        self.asset_path = asset_path
        self.position = position
        self.size = size
        self.opacity = opacity
        self.text = text
        self.style = style or {}

    def render(self, base_img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Render this layer onto the base image."""
        if self.layer_type == "background_asset" and self.asset_path:
            return self._render_background(base_img)
        elif self.layer_type == "foreground_annotation":
            return self._render_foreground_annotation(base_img, t, scene_duration)
        elif self.layer_type == "proof_overlay":
            return self._render_proof_overlay(base_img, t, scene_duration)
        elif self.layer_type == "magnifier_crop":
            return self._render_magnifier_crop(base_img, t, scene_duration)
        elif self.layer_type == "supporting_cutaway":
            return self._render_cutaway(base_img, t, scene_duration)
        elif self.layer_type == "caption_layer":
            return self._render_caption_layer(base_img, t, scene_duration)
        return base_img

    def _render_background(self, base_img: Image.Image) -> Image.Image:
        """Render background asset layer."""
        if not self.asset_path:
            return base_img
        try:
            bg = Image.open(self.asset_path).convert("RGB")
            bg = bg.resize(base_img.size, Image.Resampling.LANCZOS)
            return Image.alpha_composite(bg.convert("RGBA"), base_img.convert("RGBA")).convert("RGB")
        except Exception:
            return base_img

    def _render_foreground_annotation(self, base_img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Render foreground annotation (arrows, highlights, etc.)."""
        # Placeholder for annotation rendering
        return base_img

    def _render_proof_overlay(self, base_img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Render proof overlay (screenshots, documents, etc.)."""
        if not self.asset_path:
            return base_img
        try:
            overlay = Image.open(self.asset_path).convert("RGBA")
            if self.size:
                overlay = overlay.resize(self.size, Image.Resampling.LANCZOS)

            # Create composite image
            result = base_img.convert("RGBA")
            result.paste(overlay, self.position, overlay)
            return result.convert("RGB")
        except Exception:
            return base_img

    def _render_magnifier_crop(self, base_img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Render magnifier crop effect."""
        try:
            if self.asset_path:
                asset = Image.open(self.asset_path).convert("RGB")
            else:
                asset = base_img
            if self.size:
                crop_size = (int(self.size[0] * 1.5), int(self.size[1] * 1.5))  # 1.5x magnification
                asset_crop = asset.resize(crop_size, Image.Resampling.LANCZOS)
                left = max(0, (asset_crop.width - self.size[0]) // 2)
                top = max(0, (asset_crop.height - self.size[1]) // 2)
                magnified = asset_crop.crop((left, top, left + self.size[0], top + self.size[1]))

                result = base_img.convert("RGBA")
                result.paste(magnified.convert("RGBA"), self.position, magnified.convert("RGBA"))
                return result.convert("RGB")
        except Exception:
            return base_img
        return base_img

    def _render_cutaway(self, base_img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Render supporting cutaway."""
        if not self.asset_path:
            return base_img
        try:
            cutaway = Image.open(self.asset_path).convert("RGB")
            if self.size:
                cutaway = cutaway.resize(self.size, Image.Resampling.LANCZOS)

            result = base_img.convert("RGBA")
            result.paste(cutaway.convert("RGBA"), self.position, cutaway.convert("RGBA"))
            return result.convert("RGB")
        except Exception:
            return base_img

    def _render_caption_layer(self, base_img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Render caption text layer."""
        if not self.text:
            return base_img

        result = base_img.copy()
        draw = ImageDraw.Draw(result)
        caption_font = self.style.get('font')
        if not caption_font:
            try:
                caption_font = ImageFont.load_default()
            except Exception:
                caption_font = None

        font_size = self.style.get('font_size', 40)
        if caption_font and hasattr(caption_font, 'size') and caption_font.size != font_size:
            try:
                caption_font = ImageFont.truetype(caption_font.path, font_size)
            except Exception:
                caption_font = ImageFont.load_default()

        color = self.style.get('color', 'white')
        x, y = self.position
        text = self.text
        max_width = self.style.get('max_width', base_img.width - x - 40)

        lines = []
        current = ""
        for word in text.split():
            test_line = f"{current} {word}".strip()
            try:
                w, _ = draw.textsize(test_line, font=caption_font)
            except Exception:
                w = len(test_line) * 10
            if w <= max_width:
                current = test_line
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        for idx, line in enumerate(lines):
            line_y = y + idx * (font_size + 8)
            draw.text((x, line_y), line, fill=color, font=caption_font)

        return result


class LayeredComposition:
    """Reusable layered composition layouts."""

    @staticmethod
    def proof_with_magnifier(proof_asset: str, magnifier_crop: str) -> List[VisualLayer]:
        """Proof + magnifier layout."""
        return [
            VisualLayer("background_asset", proof_asset),
            VisualLayer("magnifier_crop", magnifier_crop, position=(50, 100), size=(300, 200))
        ]

    @staticmethod
    def split_compare(left_asset: str, right_asset: str, labels: Tuple[str, str] = ("BEFORE", "AFTER")) -> List[VisualLayer]:
        """Split compare layout."""
        return [
            VisualLayer("proof_overlay", left_asset, position=(0, 0), size=(540, 960)),
            VisualLayer("proof_overlay", right_asset, position=(540, 0), size=(540, 960)),
            VisualLayer("caption_layer", text=labels[0], position=(200, 900)),
            VisualLayer("caption_layer", text=labels[1], position=(740, 900))
        ]

    @staticmethod
    def prompt_response_overlay(prompt_asset: str, response_asset: str) -> List[VisualLayer]:
        """Prompt + response overlay layout."""
        return [
            VisualLayer("background_asset", prompt_asset),
            VisualLayer("proof_overlay", response_asset, position=(100, 200), size=(800, 600), opacity=0.9)
        ]

    @staticmethod
    def code_with_zoom_focus(code_asset: str, zoom_area: Tuple[int, int, int, int]) -> List[VisualLayer]:
        """Code + zoom focus layout."""
        return [
            VisualLayer("background_asset", code_asset),
            VisualLayer("magnifier_crop", code_asset, position=(200, 300), size=(400, 300))
        ]

    @staticmethod
    def number_reveal(base_asset: str, number_text: str) -> List[VisualLayer]:
        """Number reveal composition."""
        return [
            VisualLayer("background_asset", base_asset),
            VisualLayer("caption_layer", text=number_text, position=(400, 800),
                       style={'font_size': 60, 'color': 'yellow'})
        ]


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _parse_coords(value: str) -> tuple[int, int] | tuple[int, int, int, int] | None:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        return None
    if all(part.lstrip("+-").replace(".", "", 1).isdigit() for part in parts):
        coords = [int(float(part)) for part in parts]
        if len(coords) == 2:
            return tuple(coords)
        if len(coords) == 4:
            return tuple(coords)
    return None


def parse_visual_layers(layers_config: List[str]) -> List[VisualLayer]:
    """Parse visual_layers strings into VisualLayer objects."""
    layers: list[VisualLayer] = []
    for config in layers_config:
        parts = config.split(":")
        if not parts:
            continue

        layer_type = parts[0]
        asset = parts[1] if len(parts) > 1 and parts[1] else None
        opacity = 1.0
        position: tuple[int, int] = (0, 0)
        size: tuple[int, int] | None = None
        text = None
        style: dict[str, Any] = {}

        extra = parts[2:]
        while extra and extra[0] == "":
            extra = extra[1:]

        if extra:
            first = extra[0]
            if _is_number(first):
                opacity = float(first)
                extra = extra[1:]
            else:
                coords = _parse_coords(first)
                if coords is not None:
                    if len(coords) == 2:
                        position = coords
                    elif len(coords) == 4:
                        position = (coords[0], coords[1])
                        size = (coords[2], coords[3])
                    extra = extra[1:]
                elif first.startswith("{") and first.endswith("}"):
                    try:
                        import json
                        style = json.loads(first)
                    except Exception:
                        pass
                    extra = extra[1:]

        if extra:
            candidate = extra[0]
            if candidate.startswith("{") and candidate.endswith("}"):
                try:
                    import json
                    style = json.loads(candidate)
                except Exception:
                    pass
            else:
                text = candidate

        layers.append(VisualLayer(layer_type, asset, position=position, size=size, opacity=opacity, text=text, style=style))
    return layers


def composite_layers(base_img: Image.Image, layers: List[VisualLayer], t: float, scene_duration: float) -> Image.Image:
    """Composite multiple layers onto base image."""
    result = base_img
    for layer in layers:
        result = layer.render(result, t, scene_duration)
    return result


def apply_multi_layer_composition(scene: StoryboardScene, base_img: Image.Image, t: float) -> Image.Image:
    """Apply multi-layer composition for scene."""
    if not scene.visual_layers:
        return base_img

    layers = parse_visual_layers(scene.visual_layers)
    return composite_layers(base_img, layers, t, scene.duration)