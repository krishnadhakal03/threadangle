"""
Day7 Coffee Fireship50 Rebuild Test

Take the exact coffee script and rebuild visuals only using new editorial density engine.
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storyboard.schema import load_storyboard, save_storyboard, StoryboardScene, BeatRole, MotionProfile, MotionIntensity
from storyboard.editorial_density import EditorialDensityEngine
from storyboard.pattern_interrupts import apply_interrupt_rules, InterruptCadence
from storyboard.semantic_emphasis import SemanticEmphasisEngine
from storyboard.cutaway_engine import CutawayEngine
from storyboard.multi_layer import LayeredComposition


def rebuild_coffee_with_density(original_path: Path, output_path: Path, repo_root: Path) -> None:
    """Rebuild coffee storyboard with editorial density engine."""

    # Load original
    storyboard = load_storyboard(original_path)

    # Initialize engines
    density_engine = EditorialDensityEngine()
    emphasis_engine = SemanticEmphasisEngine()
    cutaway_engine = CutawayEngine(repo_root)

    print(f"Original storyboard: {len(storyboard.scenes)} scenes")

    # Apply editorial density to each scene
    for scene in storyboard.scenes:
        print(f"Processing scene: {scene.scene_id}")

        # Apply semantic emphasis
        emphasis_engine.apply_semantic_emphasis(scene)

        # Apply cutaway routing
        cutaway_engine.apply_cutaway_routing(scene)

        # Add layered compositions based on content
        _add_layered_composition(scene)

        # Boost motion profiles for non-payoff scenes
        if scene.beat_role != BeatRole.payoff:
            scene.motion_profile = MotionProfile.fireship_dynamic
            scene.motion_intensity = MotionIntensity.high

        # Add micro beats if missing
        if not scene.micro_beats:
            scene.micro_beats = ["punch_zoom", "proof_flash"]

    # Apply interrupt cadence
    apply_interrupt_rules(storyboard.scenes, InterruptCadence.fireship50)

    # Validate with density engine
    issues = density_engine.check_storyboard(storyboard)
    print(f"Density check found {len(issues)} issues")

    for issue in issues:
        if issue['severity'] == 'error':
            print(f"ERROR: {issue['message']} (scene: {issue.get('scene_id', 'unknown')})")

    # Save rebuilt storyboard
    save_storyboard(storyboard, output_path)
    print(f"Rebuilt storyboard saved to: {output_path}")


def _add_layered_composition(scene: StoryboardScene) -> None:
    """Add layered composition based on scene content."""

    layers = []

    # All non-payoff scenes get at least background + overlay
    if scene.beat_role != BeatRole.payoff:
        # Add background asset if we have cutaways
        if scene.supporting_cutaways:
            layers.append(f"background_asset:{scene.supporting_cutaways[0]}")

        # Add proof overlay for proof scenes
        if scene.beat_role == BeatRole.proof:
            layers.append("proof_overlay:proof_screenshot.png:0.8")

        # Add magnifier for emphasis terms
        if scene.emphasis_terms:
            layers.append("magnifier_crop:proof_screenshot.png:200,300,400,300")

        # Add caption layer
        if scene.caption_text:
            layers.append(f"caption_layer:::{scene.caption_text}")

    scene.visual_layers = layers


def compare_original_vs_rebuild(original_path: Path, rebuild_path: Path) -> None:
    """Compare original vs rebuilt storyboard."""

    original = load_storyboard(original_path)
    rebuild = load_storyboard(rebuild_path)

    print("\n=== COMPARISON REPORT ===")

    for i, (orig_scene, reb_scene) in enumerate(zip(original.scenes, rebuild.scenes)):
        print(f"\nScene {i+1}: {orig_scene.scene_id}")
        print(f"  Original - Layers: {len(orig_scene.visual_layers)}, Beats: {len(orig_scene.micro_beats)}, Cutaways: {len(orig_scene.supporting_cutaways)}")
        print(f"  Rebuild  - Layers: {len(reb_scene.visual_layers)}, Beats: {len(reb_scene.micro_beats)}, Cutaways: {len(reb_scene.supporting_cutaways)}")

        if reb_scene.visual_layers:
            print(f"    Layers: {reb_scene.visual_layers}")
        if reb_scene.micro_beats:
            print(f"    Beats: {reb_scene.micro_beats}")
        if reb_scene.emphasis_terms:
            print(f"    Emphasis: {reb_scene.emphasis_terms}")


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent.parent
    original_path = repo_root / "backend" / "day7_coffee_storyboard.json"
    rebuild_path = repo_root / "backend" / "day7_coffee_fireship50_storyboard.json"

    rebuild_coffee_with_density(original_path, rebuild_path, repo_root)
    compare_original_vs_rebuild(original_path, rebuild_path)