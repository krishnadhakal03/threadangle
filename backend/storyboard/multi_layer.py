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
        if not self.asset_path:
            return base_img
        try:
            # Create a magnified crop of the asset
            asset = Image.open(self.asset_path).convert("RGB")
            if self.size:
                crop_size = (int(self.size[0] * 1.5), int(self.size[1] * 1.5))  # 1.5x magnification
                asset_crop = asset.resize(crop_size, Image.Resampling.LANCZOS)
                # Crop to show magnified area
                left = (asset_crop.width - self.size[0]) // 2
                top = (asset_crop.height - self.size[1]) // 2
                magnified = asset_crop.crop((left, top, left + self.size[0], top + self.size[1]))

                result = base_img.convert("RGBA")
                result.paste(magnified.convert("RGBA"), self.position)
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
            result.paste(cutaway.convert("RGBA"), self.position)
            return result.convert("RGB")
        except Exception:
            return base_img

    def _render_caption_layer(self, base_img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Render caption text layer."""
        if not self.text:
            return base_img

        result = base_img.copy()
        draw = ImageDraw.Draw(result)

        # Simple text rendering - in real implementation, use proper font loading
        try:
            # Use default font, position at bottom
            font_size = self.style.get('font_size', 40)
            # For now, just draw text at position
            draw.text(self.position, self.text, fill='white')
        except Exception:
            pass

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


def parse_visual_layers(layers_config: List[str]) -> List[VisualLayer]:
    """Parse visual_layers strings into VisualLayer objects."""
    layers = []
    for config in layers_config:
        # Enhanced parsing: type:asset_path:opacity:text:style_json
        parts = config.split(":")
        if len(parts) >= 1:
            layer_type = parts[0]
            asset = parts[1] if len(parts) > 1 and parts[1] else None
            opacity = float(parts[2]) if len(parts) > 2 and parts[2] else 1.0
            text = parts[3] if len(parts) > 3 and parts[3] else None
            style = {}
            if len(parts) > 4:
                try:
                    import json
                    style = json.loads(parts[4])
                except:
                    pass

            layers.append(VisualLayer(layer_type, asset, opacity=opacity, text=text, style=style))
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