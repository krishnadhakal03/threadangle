"""
Editorial Density Rules Engine

Enforces hard rules for visual density in scenes.
No text-only scenes except payoff. Every scene must have layered storytelling.
"""

from typing import List, Dict, Any
from .schema import StoryboardScene, BeatRole


class DensityRule:
    """A rule for editorial density."""

    def __init__(self, name: str, description: str, severity: str = "warning"):
        self.name = name
        self.description = description
        self.severity = severity  # error, warning, info

    def check(self, scene: StoryboardScene) -> Dict[str, Any] | None:
        """Check if scene violates this rule. Return issue dict if violation."""
        raise NotImplementedError


class NoTextOnlyScenesRule(DensityRule):
    """No scene may be text card only except payoff."""

    def __init__(self):
        super().__init__(
            "no_text_only_scenes",
            "No scene may be 'text card only' except payoff scenes",
            "error"
        )

    def check(self, scene: StoryboardScene) -> Dict[str, Any] | None:
        if scene.beat_role == BeatRole.payoff:
            return None  # Payoff can be text-only

        # Check if scene has only generated_card with no layers or beats
        if (scene.visual_source.value == "generated_card" and
            not scene.visual_layers and
            not scene.micro_beats and
            not scene.supporting_cutaways):
            return {
                "severity": self.severity,
                "code": self.name,
                "message": "Scene is text-card only with no visual density elements",
                "scene_id": scene.scene_id
            }
        return None


class MinimumDensityElementsRule(DensityRule):
    """Each non-payoff scene must contain at least 2 density elements."""

    def __init__(self):
        super().__init__(
            "minimum_density_elements",
            "Non-payoff scenes must have at least 2 density elements",
            "error"
        )

    def check(self, scene: StoryboardScene) -> Dict[str, Any] | None:
        if scene.beat_role == BeatRole.payoff:
            return None

        density_elements = 0

        # Count density elements
        if scene.supporting_cutaways:
            density_elements += 1  # cutaway insert

        if len(scene.visual_layers) > 1:  # layered foreground overlay
            density_elements += 1

        if scene.micro_beats:  # motion beat cluster
            density_elements += 1

        if scene.emphasis_terms:  # semantic emphasis event
            density_elements += 1

        # Check for proof artifacts (non-generated visuals)
        if scene.visual_source.value not in ["generated_card"]:
            density_elements += 1

        # Check for interrupt events (pattern interrupts)
        if scene.interrupt_allowed and scene.duration > scene.novelty_interval_seconds:
            density_elements += 1

        if density_elements < 2:
            return {
                "severity": self.severity,
                "code": self.name,
                "message": f"Scene has only {density_elements} density elements, needs at least 2",
                "scene_id": scene.scene_id,
                "density_score": density_elements
            }
        return None


class LowDensitySceneRule(DensityRule):
    """Warn about scenes with low editorial density."""

    def __init__(self):
        super().__init__(
            "low_density_scene",
            "Scene has low editorial density (events/second < 0.5)",
            "warning"
        )

    def check(self, scene: StoryboardScene) -> Dict[str, Any] | None:
        if scene.beat_role == BeatRole.payoff:
            return None

        # Calculate events per second
        total_events = (
            len(scene.micro_beats) +
            len(scene.supporting_cutaways) +
            len(scene.visual_layers) +
            len(scene.emphasis_terms)
        )

        if scene.duration > 0:
            events_per_second = total_events / scene.duration
            if events_per_second < 0.5:
                return {
                    "severity": self.severity,
                    "code": self.name,
                    "message": ".2f",
                    "scene_id": scene.scene_id,
                    "events_per_second": round(events_per_second, 2)
                }
        return None


class SingleLayerSceneRule(DensityRule):
    """Warn about single-layer scenes."""

    def __init__(self):
        super().__init__(
            "single_layer_scene",
            "Scene uses only single visual layer",
            "warning"
        )

    def check(self, scene: StoryboardScene) -> Dict[str, Any] | None:
        if scene.beat_role == BeatRole.payoff:
            return None

        if not scene.visual_layers or len(scene.visual_layers) <= 1:
            return {
                "severity": self.severity,
                "code": self.name,
                "message": "Scene has minimal layering - consider adding background, overlay, or cutaway",
                "scene_id": scene.scene_id
            }
        return None


class StaticProofRiskRule(DensityRule):
    """Warn about static proof scenes that could be more dynamic."""

    def __init__(self):
        super().__init__(
            "static_proof_risk",
            "Proof scene is static - consider adding motion or emphasis",
            "info"
        )

    def check(self, scene: StoryboardScene) -> Dict[str, Any] | None:
        if scene.beat_role != BeatRole.proof:
            return None

        if (scene.motion_profile.value == "static_clean" and
            not scene.micro_beats and
            not scene.emphasis_terms):
            return {
                "severity": self.severity,
                "code": self.name,
                "message": "Proof scene is static - add motion beats or emphasis terms for better retention",
                "scene_id": scene.scene_id
            }
        return None


class EditorialDensityEngine:
    """Main engine for enforcing editorial density rules."""

    def __init__(self):
        self.rules = [
            NoTextOnlyScenesRule(),
            MinimumDensityElementsRule(),
            LowDensitySceneRule(),
            SingleLayerSceneRule(),
            StaticProofRiskRule(),
        ]

    def check_scene(self, scene: StoryboardScene) -> List[Dict[str, Any]]:
        """Check a single scene against all density rules."""
        issues = []
        for rule in self.rules:
            issue = rule.check(scene)
            if issue:
                issues.append(issue)
        return issues

    def check_storyboard(self, storyboard) -> List[Dict[str, Any]]:
        """Check entire storyboard for density violations."""
        all_issues = []
        for scene in storyboard.scenes:
            issues = self.check_scene(scene)
            all_issues.extend(issues)
        return all_issues

    def calculate_density_score(self, scene: StoryboardScene) -> float:
        """Calculate editorial density score (events per second)."""
        total_events = (
            len(scene.micro_beats) +
            len(scene.supporting_cutaways) +
            len(scene.visual_layers) +
            len(scene.emphasis_terms) +
            (1 if scene.interrupt_allowed and scene.duration > scene.novelty_interval_seconds else 0)
        )

        if scene.duration > 0:
            return total_events / scene.duration
        return 0.0