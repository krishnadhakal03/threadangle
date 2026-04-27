"""
Retention QA for Retention Editing Engine

Checks for attention retention and editing best practices.
"""

from typing import List, Dict
from .schema import StoryboardScene, BeatRole


class RetentionRule:
    """Base class for retention rules."""

    def check_scene(self, scene: StoryboardScene) -> str | None:
        """Check if rule is violated. Return warning message or None."""
        raise NotImplementedError

    def check_storyboard(self, storyboard) -> List[str]:
        """Check across storyboard. Return list of warnings."""
        return []


class VisualChangeRule(RetentionRule):
    """No visual change for >2 seconds."""

    def check_scene(self, scene: StoryboardScene) -> str | None:
        if scene.novelty_interval_seconds > 2.0:
            return f"Novelty interval {scene.novelty_interval_seconds}s exceeds 2s maximum"
        return None


class BeatRoleRule(RetentionRule):
    """Scene lacks beat_role."""

    def check_scene(self, scene: StoryboardScene) -> str | None:
        if not scene.beat_role:
            return "Scene missing beat_role assignment"
        return None


class PayoffTimingRule(RetentionRule):
    """Payoff appears too late in storyboard."""

    def check_storyboard(self, storyboard) -> List[str]:
        warnings = []
        payoff_scenes = [i for i, s in enumerate(storyboard.scenes) if s.beat_role == BeatRole.payoff]
        if payoff_scenes and payoff_scenes[0] / len(storyboard.scenes) > 0.8:
            warnings.append("Payoff scene appears too late in storyboard")
        return warnings


class HookMotionRule(RetentionRule):
    """Hook has no motion in first second."""

    def check_scene(self, scene: StoryboardScene) -> str | None:
        if scene.beat_role == BeatRole.hook and not scene.micro_beats:
            return "Hook scene lacks micro-beats for immediate engagement"
        return None


class StaticScreenshotRule(RetentionRule):
    """Too many static screenshot scenes."""

    def check_storyboard(self, storyboard) -> List[str]:
        from .schema import VisualSource
        static_screenshots = [s for s in storyboard.scenes if s.visual_source == VisualSource.proof_screenshot and not s.micro_beats]
        if len(static_screenshots) > len(storyboard.scenes) * 0.5:
            return [f"Too many static screenshots: {len(static_screenshots)}/{len(storyboard.scenes)}"]
        return []


class CaptionCompetitionRule(RetentionRule):
    """Captions compete with proof text."""

    def check_scene(self, scene: StoryboardScene) -> str | None:
        from .schema import VisualSource
        if scene.visual_source == VisualSource.proof_screenshot and scene.caption_text:
            # Simple heuristic: if caption has numbers and scene has proof
            if any(char.isdigit() for char in scene.caption_text) and scene.proof_label:
                return "Caption may compete with proof text overlay"
        return None


class CTAActionRule(RetentionRule):
    """CTA lacks clear action word."""

    def check_scene(self, scene: StoryboardScene) -> str | None:
        if scene.beat_role == BeatRole.cta:
            action_words = ["click", "sign", "join", "start", "get", "try", "buy", "save"]
            text = (scene.narration_text + " " + (scene.caption_text or "")).lower()
            if not any(word in text for word in action_words):
                return "CTA scene lacks clear action word"
        return None


# Default retention rules
DEFAULT_RETENTION_RULES: List[RetentionRule] = [
    VisualChangeRule(),
    BeatRoleRule(),
    PayoffTimingRule(),
    HookMotionRule(),
    StaticScreenshotRule(),
    CaptionCompetitionRule(),
    CTAActionRule(),
]


def check_retention_rules_scene(scene: StoryboardScene) -> List[str]:
    """Check all retention rules for a scene."""
    warnings = []
    for rule in DEFAULT_RETENTION_RULES:
        warning = rule.check_scene(scene)
        if warning:
            warnings.append(warning)
    return warnings


def check_retention_rules_storyboard(storyboard) -> Dict[str, List[str]]:
    """Check retention rules for all scenes and storyboard-wide."""
    results = {}
    for scene in storyboard.scenes:
        results[scene.scene_id] = check_retention_rules_scene(scene)

    # Storyboard-wide checks
    for rule in DEFAULT_RETENTION_RULES:
        storyboard_warnings = rule.check_storyboard(storyboard)
        if storyboard_warnings:
            # Add to first scene or create special key
            results["storyboard"] = storyboard_warnings

    return results