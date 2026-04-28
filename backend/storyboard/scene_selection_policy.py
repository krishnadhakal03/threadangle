"""Scene Selection Policy Engine v1 (SSP3)

Coordinates provider detection, planning (Anthropic or fallback), critic
pass, and writes out scene_selection_plan.json and critic report.
"""
import json
from pathlib import Path
from typing import List, Dict

from . import provider_availability
from .anthropic_planner import plan_with_anthropic
from .scene_critic import run_critic

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_storyboard(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    # assume top level 'scenes' key
    scenes = data.get("scenes") or data.get("shots") or []
    return scenes


def run_policy_on_storyboard(sb_path: Path, out_prefix: str):
    providers = provider_availability.check_providers()
    scenes = load_storyboard(sb_path)
    plan = plan_with_anthropic(scenes)
    critic = run_critic(plan)

    plan_path = OUT_DIR / f"scene_selection_plan_{out_prefix}.json"
    critic_path = OUT_DIR / f"critic_report_{out_prefix}.json"
    provider_path = OUT_DIR / "provider_availability_report.json"

    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    critic_path.write_text(json.dumps(critic, indent=2), encoding="utf-8")
    provider_path.write_text(json.dumps(providers, indent=2), encoding="utf-8")

    return plan_path, critic_path, provider_path, plan, critic, providers


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m backend.storyboard.scene_selection_policy <storyboard.json> <prefix>")
        raise SystemExit(2)
    sb = Path(sys.argv[1])
    prefix = sys.argv[2]
    run_policy_on_storyboard(sb, prefix)
