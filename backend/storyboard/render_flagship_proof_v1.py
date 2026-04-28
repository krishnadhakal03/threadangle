"""Render Day7 Coffee Flagship Proof Draft - Final render of repaired storyboard

Uses free/local-only rendering:
- TTS: local or fallback (no ElevenLabs)
- Visuals: proof_screenshot cards, local_dom_reconstruction, generated_card fallback
- FFmpeg for encoding
- No Runway, no paid APIs

Output: day7_coffee_flagship_proof_v1.mp4
"""

import json
from pathlib import Path

from backend.storyboard.schema import load_storyboard, RenderMode, VideoFormat
from backend.storyboard.render import render_draft_video


def main():
    repo_root = Path(__file__).resolve().parents[2]
    
    # Use repaired storyboard
    sb_path = repo_root / "backend" / "generated_videos" / "storyboard_review" / "day7_coffee_fireship50_repaired.json"
    output_dir = repo_root / "backend" / "generated_videos" / "storyboard_review" / "day7_coffee_flagship_proof_v1"
    
    print(f"Loading repaired storyboard: {sb_path}")
    if not sb_path.exists():
        print("ERROR: Repaired storyboard not found. Run repair_fireship50_visuals.py first.")
        return
    
    storyboard = load_storyboard(sb_path)
    print(f"Loaded storyboard: {storyboard.project_id} with {len(storyboard.scenes)} scenes")
    
    # Update project ID for output
    storyboard.project_id = "day7_coffee_flagship_proof_v1"
    storyboard.title = "Coffee Savings Proof - Flagship Draft v1"
    storyboard.render_mode = RenderMode.draft
    storyboard.format = VideoFormat.short_9x16
    
    print(f"\nStarting render to: {output_dir}")
    try:
        result = render_draft_video(storyboard, repo_root, output_dir)
        print(f"\n✓ Render successful!")
        print(json.dumps(result, indent=2))
        
        # Write final result
        result_path = output_dir / "flagship_proof_result.json"
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Result saved to: {result_path}")
        
        return result_path
    except Exception as e:
        print(f"✗ Render failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
