"""
Semantic Emphasis Map Engine

Maps narration meaning to editorial treatment.
Meaning should drive motion.
"""

from typing import List, Dict, Any, Set
from .schema import StoryboardScene


class SemanticPattern:
    """A semantic pattern that triggers editorial treatment."""

    def __init__(self, keywords: Set[str], interrupt_type: str, motion_boost: str = "",
                 emphasis_level: str = "medium"):
        self.keywords = keywords
        self.interrupt_type = interrupt_type
        self.motion_boost = motion_boost
        self.emphasis_level = emphasis_level

    def matches(self, text: str) -> bool:
        """Check if this pattern matches the text."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)


class SemanticEmphasisEngine:
    """Engine for mapping semantic meaning to editorial treatment."""

    def __init__(self):
        self.patterns = [
            # Dollar amount -> counter slam
            SemanticPattern(
                keywords={"$", "dollars", "bucks", "cost", "price", "spend", "save"},
                interrupt_type="freeze_emphasis",
                motion_boost="value_tick",
                emphasis_level="high"
            ),

            # Contrast words -> contradiction interrupt
            SemanticPattern(
                keywords={"but", "however", "instead", "yet", "although", "versus", "vs"},
                interrupt_type="contradiction_card",
                motion_boost="hard_cutaway",
                emphasis_level="high"
            ),

            # Proof words -> magnifier punch
            SemanticPattern(
                keywords={"proof", "evidence", "data", "shows", "reveals", "proves", "confirms"},
                interrupt_type="proof_flash",
                motion_boost="magnifier_crop",
                emphasis_level="high"
            ),

            # CTA keywords -> terminal emphasis snap
            SemanticPattern(
                keywords={"comment", "subscribe", "like", "share", "follow", "click", "download"},
                interrupt_type="snap_zoom",
                motion_boost="punch_zoom",
                emphasis_level="high"
            ),

            # Question words -> curiosity interrupt
            SemanticPattern(
                keywords={"what if", "imagine", "think about", "consider", "wonder"},
                interrupt_type="pulse_glow",
                motion_boost="shake_pan",
                emphasis_level="medium"
            ),

            # Time words -> urgency interrupt
            SemanticPattern(
                keywords={"now", "today", "immediately", "fast", "quick", "instant"},
                interrupt_type="rapid_zoom",
                motion_boost="flash_cut",
                emphasis_level="medium"
            )
        ]

    def analyze_scene(self, scene: StoryboardScene) -> Dict[str, Any]:
        """Analyze scene for semantic emphasis opportunities."""
        narration = scene.narration_text or ""
        caption = scene.caption_text or ""
        full_text = f"{narration} {caption}"

        matching_patterns = []
        emphasis_terms = set()

        for pattern in self.patterns:
            if pattern.matches(full_text):
                matching_patterns.append(pattern)
                emphasis_terms.update(pattern.keywords)

        # Generate editorial treatments
        treatments = {
            "interrupt_types": [p.interrupt_type for p in matching_patterns],
            "motion_boosts": [p.motion_boost for p in matching_patterns if p.motion_boost],
            "emphasis_terms": list(emphasis_terms),
            "emphasis_level": max([p.emphasis_level for p in matching_patterns], default="low")
        }

        return treatments

    def apply_semantic_emphasis(self, scene: StoryboardScene) -> None:
        """Apply semantic emphasis to scene in place."""
        analysis = self.analyze_scene(scene)

        # Add emphasis terms
        scene.emphasis_terms.extend(analysis["emphasis_terms"])
        scene.emphasis_terms = list(set(scene.emphasis_terms))  # Deduplicate

        # Boost motion profile if high emphasis
        if analysis["emphasis_level"] == "high" and scene.motion_intensity.value == "low":
            scene.motion_intensity = scene.motion_intensity.__class__("med")

        # Add semantic interrupts to micro_beats
        for interrupt_type in analysis["interrupt_types"]:
            if interrupt_type not in scene.micro_beats:
                scene.micro_beats.append(interrupt_type)

        # Add motion boosts
        for motion_boost in analysis["motion_boosts"]:
            if motion_boost not in scene.micro_beats:
                scene.micro_beats.append(motion_boost)

    def get_semantic_recommendations(self, scene: StoryboardScene) -> List[str]:
        """Get editorial recommendations based on semantic analysis."""
        analysis = self.analyze_scene(scene)
        recommendations = []

        if not analysis["interrupt_types"]:
            recommendations.append("Consider adding semantic interrupts based on content keywords")

        if analysis["emphasis_level"] == "high" and len(scene.micro_beats) < 2:
            recommendations.append("High-emphasis content detected - add more motion beats")

        if analysis["emphasis_terms"] and not scene.emphasis_terms:
            recommendations.append(f"Add emphasis terms: {', '.join(analysis['emphasis_terms'])}")

        return recommendations