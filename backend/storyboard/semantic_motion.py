"""
Semantic Motion Mapping

Maps important narration terms to visual motion effects.
"""

from typing import Dict, List
from .schema import StoryboardScene


# Keyword to beat mappings
SEMANTIC_MAPPINGS: Dict[str, List[str]] = {
    "dollar": ["value_tick", "number_pop"],
    "save": ["value_tick", "proof_highlight"],
    "but": ["quick_reframe", "hard_cutaway"],
    "then": ["quick_reframe"],
    "until": ["quick_reframe"],
    "proof": ["proof_highlight", "document_punch"],
    "receipt": ["document_punch", "focus_crop"],
    "ai said": ["text_snap", "split_reveal"],
    "click": ["punch_zoom"],
    "join": ["punch_zoom"],
    "start": ["punch_zoom"],
}


def map_semantic_terms_to_beats(scene: StoryboardScene) -> List[str]:
    """Map narration terms to appropriate micro-beats."""
    text = (scene.narration_text + " " + (scene.caption_text or "")).lower()
    beats = []

    for keyword, beat_list in SEMANTIC_MAPPINGS.items():
        if keyword in text:
            beats.extend(beat_list)

    # Remove duplicates while preserving order
    seen = set()
    unique_beats = []
    for beat in beats:
        if beat not in seen:
            unique_beats.append(beat)
            seen.add(beat)

    return unique_beats


def enhance_scene_with_semantic_motion(scene: StoryboardScene) -> None:
    """Add semantic motion beats to scene."""
    semantic_beats = map_semantic_terms_to_beats(scene)
    scene.micro_beats.extend(semantic_beats)
    # Remove duplicates
    scene.micro_beats = list(dict.fromkeys(scene.micro_beats))