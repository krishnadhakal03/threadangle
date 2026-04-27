"""
Pattern Interrupt Engine

Injects visual changes every ~1–2 seconds unless payoff hold.
Strengthened for Fireship-style editorial energy.
"""

from typing import List
from enum import Enum
from .schema import StoryboardScene, BeatRole


class InterruptCadence(str, Enum):
    light = "light"      # Every 2.0 seconds
    medium = "medium"    # Every 1.5 seconds
    fireship50 = "fireship50"  # Every 1.0 seconds


class InterruptType(str, Enum):
    hard_cutaway = "hard_cutaway"
    contradiction_card = "contradiction_card"
    analogy_insert = "analogy_insert"
    snap_zoom = "snap_zoom"
    freeze_emphasis = "freeze_emphasis"
    proof_flash = "proof_flash"
    text_snap = "text_snap"
    pulse_glow = "pulse_glow"
    shake_pan = "shake_pan"


def get_cadence_interval(cadence: InterruptCadence) -> float:
    """Get novelty interval for cadence profile."""
    intervals = {
        InterruptCadence.light: 2.0,
        InterruptCadence.medium: 1.5,
        InterruptCadence.fireship50: 1.0
    }
    return intervals[cadence]


def should_inject_interrupt(scene: StoryboardScene, cadence: InterruptCadence = InterruptCadence.fireship50) -> bool:
    """Check if scene should have pattern interrupts injected."""
    if scene.beat_role == BeatRole.payoff:
        return False  # No interrupts for payoff
    if not scene.interrupt_allowed:
        return False

    interval = get_cadence_interval(cadence)
    return scene.duration > interval


def get_interrupt_sequence(scene: StoryboardScene, cadence: InterruptCadence) -> List[str]:
    """Generate interrupt sequence based on scene content and cadence."""
    if not should_inject_interrupt(scene, cadence):
        return []

    interval = get_cadence_interval(cadence)
    num_interrupts = int(scene.duration / interval) - 1

    # Base interrupt types
    base_interrupts = [
        InterruptType.snap_zoom,
        InterruptType.proof_flash,
        InterruptType.freeze_emphasis,
        InterruptType.pulse_glow,
        InterruptType.shake_pan
    ]

    # Add content-aware interrupts
    content_interrupts = []

    # Check for contradiction words
    narration = (scene.narration_text or "").lower()
    if any(word in narration for word in ["but", "however", "instead", "yet", "although"]):
        content_interrupts.append(InterruptType.contradiction_card)

    # Check for dollar amounts
    if "$" in narration:
        content_interrupts.append(InterruptType.freeze_emphasis)

    # Check for proof words
    if any(word in narration for word in ["proof", "evidence", "data", "shows", "reveals"]):
        content_interrupts.append(InterruptType.proof_flash)

    # Combine and cycle
    all_interrupts = content_interrupts + base_interrupts
    if not all_interrupts:
        all_interrupts = base_interrupts

    interrupts = []
    for i in range(num_interrupts):
        interrupt_type = all_interrupts[i % len(all_interrupts)]
        interrupts.append(interrupt_type.value)

    return interrupts


def inject_pattern_interrupts(scene: StoryboardScene, cadence: InterruptCadence = InterruptCadence.fireship50) -> List[str]:
    """Inject pattern interrupts into scene's micro_beats."""
    if not should_inject_interrupt(scene, cadence):
        return scene.micro_beats

    beats = scene.micro_beats.copy()
    interrupts = get_interrupt_sequence(scene, cadence)

    # Insert interrupts at regular intervals
    interval = get_cadence_interval(cadence)
    for i, interrupt in enumerate(interrupts):
        insert_position = int((i + 1) * interval / scene.duration * len(beats)) if beats else 0
        if insert_position >= len(beats):
            beats.append(interrupt)
        else:
            beats.insert(insert_position, interrupt)

    return beats


def apply_interrupt_rules(scenes: List[StoryboardScene], cadence: InterruptCadence = InterruptCadence.fireship50) -> None:
    """Apply interrupt injection to all scenes in place."""
    for scene in scenes:
        scene.micro_beats = inject_pattern_interrupts(scene, cadence)
        # Update novelty interval to match cadence
        scene.novelty_interval_seconds = get_cadence_interval(cadence)