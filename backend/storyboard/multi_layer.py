"""
Multi-Layer Composition Helpers

Support for background proof, foreground text, moving captions, cutaways, etc.
"""

from typing import List, Dict, Any
from PIL import Image
from pathlib import Path
from .schema import StoryboardScene


class VisualLayer:
    """A visual layer in the composition."""

    def __init__(self, type: str, asset_path: str | None = None, position: tuple = (0, 0), size: tuple | None = None):
        self.type = type  # background, foreground, caption, cutaway, badge, magnifier
        self.asset_path = asset_path
        self.position = position
        self.size = size

    def render(self, base_img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Render this layer onto the base image."""
        if self.type == "background" and self.asset_path:
            try:
                bg = Image.open(self.asset_path).convert("RGB")
                bg = bg.resize(base_img.size, Image.Resampling.LANCZOS)
                return Image.alpha_composite(bg.convert("RGBA"), base_img.convert("RGBA")).convert("RGB")
            except:
                pass
        # Add other layer types as needed
        return base_img


def parse_visual_layers(layers_config: List[str]) -> List[VisualLayer]:
    """Parse visual_layers strings into VisualLayer objects."""
    layers = []
    for config in layers_config:
        # Simple parsing: type:asset_path:x,y
        parts = config.split(":")
        if len(parts) >= 2:
            layer_type = parts[0]
            asset = parts[1] if len(parts) > 1 and parts[1] else None
            layers.append(VisualLayer(layer_type, asset))
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