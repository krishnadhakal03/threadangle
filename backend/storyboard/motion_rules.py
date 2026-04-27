"""
Motion Rules for Editorial Motion Engine

Defines rules for motion timing and novelty to ensure engaging content.
"""

from typing import Dict, List
from .schema import StoryboardScene, MotionProfile


class MotionRule:
    """Base class for motion rules."""

    def check(self, scene: StoryboardScene) -> str | None:
        """Check if rule is violated. Return warning message or None."""
        raise NotImplementedError


class StaticHoldRule(MotionRule):
    """No static hold longer than threshold unless payoff."""

    def __init__(self, max_hold: float = 1.8):
        self.max_hold = max_hold

    def check(self, scene: StoryboardScene) -> str | None:
        if scene.motion_profile == MotionProfile.static_clean and scene.duration > self.max_hold:
            if not self._is_payoff_scene(scene):
                return f"Static scene exceeds {self.max_hold}s hold time without payoff"
        return None

    def _is_payoff_scene(self, scene: StoryboardScene) -> bool:
        # Simple heuristic: check if narration contains payoff words
        payoff_words = ["save", "earn", "profit", "result", "outcome", "final"]
        return any(word in scene.narration_text.lower() for word in payoff_words)


class NoveltyInjectionRule(MotionRule):
    """Inject micro-change if scene exceeds threshold without motion."""

    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold

    def check(self, scene: StoryboardScene) -> str | None:
        if scene.duration > self.threshold and not scene.micro_beats:
            return f"Long scene ({scene.duration}s) lacks micro-beats for visual novelty"
        return None


class StillnessAllowanceRule(MotionRule):
    """Allow intentional stillness only for payoff cards."""

    def check(self, scene: StoryboardScene) -> str | None:
        if scene.motion_profile == MotionProfile.static_clean and scene.micro_beats:
            return "Static profile should not have micro-beats"
        return None


# Default rules
DEFAULT_MOTION_RULES: List[MotionRule] = [
    StaticHoldRule(),
    NoveltyInjectionRule(),
    StillnessAllowanceRule(),
]


def check_motion_rules(scene: StoryboardScene) -> List[str]:
    """Check all motion rules for a scene. Return list of warnings."""
    warnings = []
    for rule in DEFAULT_MOTION_RULES:
        warning = rule.check(scene)
        if warning:
            warnings.append(warning)
    return warnings


def check_storyboard_motion_rules(storyboard) -> Dict[str, List[str]]:
    """Check motion rules for all scenes in storyboard."""
    results = {}
    for scene in storyboard.scenes:
        results[scene.scene_id] = check_motion_rules(scene)
    return results