"""
Pattern Interrupt Engine

Injects visual changes every 0.8-1.8 seconds unless payoff_hold.
"""

from typing import List
from .schema import StoryboardScene, BeatRole


def should_inject_interrupt(scene: StoryboardScene) -> bool:
    """Check if scene should have pattern interrupts injected."""
    if scene.beat_role == BeatRole.payoff:
        return False  # No interrupts for payoff
    if not scene.interrupt_allowed:
        return False
    return scene.duration > scene.novelty_interval_seconds


def inject_pattern_interrupts(scene: StoryboardScene) -> List[str]:
    """Inject pattern interrupts into scene's micro_beats."""
    if not should_inject_interrupt(scene):
        return scene.micro_beats

    beats = scene.micro_beats.copy()
    num_interrupts = int(scene.duration / scene.novelty_interval_seconds) - 1
    interrupt_types = ["punch_zoom", "hard_cutaway", "text_snap", "proof_flash"]

    for i in range(num_interrupts):
        if len(beats) < i + 1:
            beats.append(interrupt_types[i % len(interrupt_types)])

    return beats


def apply_interrupt_rules(scenes: List[StoryboardScene]) -> None:
    """Apply interrupt injection to all scenes in place."""
    for scene in scenes:
        scene.micro_beats = inject_pattern_interrupts(scene)