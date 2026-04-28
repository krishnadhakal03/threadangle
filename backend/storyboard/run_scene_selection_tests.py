"""Runner for Scene Selection Policy tests (SSP4)

Runs the policy on Day6 and Day7 storyboards, writes reports, and
optionally triggers Day7 render if critic passes.
"""
import json
from pathlib import Path
from subprocess import run

from backend.storyboard.scene_selection_policy import run_policy_on_storyboard

REPO_ROOT = Path(__file__).resolve().parents[2]

DAY6 = REPO_ROOT / "backend" / "storyboard" / "examples" / "day6_walmart_storyboard.json"
DAY7 = REPO_ROOT / "backend" / "day7_coffee_storyboard.json"


def try_run():
    outputs = {}
    for path, prefix in ((DAY6, "day6"), (DAY7, "day7")):
        if not path.exists():
            print("Missing storyboard:", path)
            continue
        plan_path, critic_path, provider_path, plan, critic, providers = run_policy_on_storyboard(path, prefix)
        outputs[prefix] = {"plan": str(plan_path), "critic": str(critic_path), "providers": str(provider_path)}
        # If day7 and critic passed, optionally render (here we only call visual director run if pass)
        if prefix == "day7" and critic.get("passed"):
            print("Day7 critic passed — invoking visual director render (draft)")
            # call existing visual director runner
            try:
                run(["python", "-m", "backend.storyboard.apply_reference_day7"], check=False)
            except Exception:
                pass
    summary = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "scene_selection_test_summary.json"
    summary.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print("Summary written:", summary)


if __name__ == "__main__":
    try_run()
