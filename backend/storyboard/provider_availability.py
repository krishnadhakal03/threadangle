"""Provider availability checks for Scene Selection Policy

Detect configured providers (Pexels, Pixabay), Playwright sandbox profile,
local asset folders, and presence of user proof assets.
"""
import os
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[2]


def check_providers() -> Dict[str, bool]:
    res = {}
    res["pexels_configured"] = bool(os.getenv("PEXELS_API_KEY") or os.getenv("PEXELS_KEY"))
    res["pixabay_configured"] = bool(os.getenv("PIXABAY_API_KEY") or os.getenv("PIXABAY_KEY"))
    res["anthropic_available"] = bool(os.getenv("ANTHROPIC_API_KEY"))
    res["enable_anthropic_planner"] = os.getenv("ENABLE_ANTHROPIC_PLANNER") == "1"
    # Playwright sandbox profile path
    res["playwright_sandbox_profile"] = bool(os.getenv("PLAYWRIGHT_SANDBOX_PROFILE"))
    # local stock folder
    res["local_stock_exists"] = (REPO_ROOT / "assets" / "stock").exists()
    # user proof assets folder
    res["user_proof_exists"] = (REPO_ROOT / "assets" / "proofs").exists()
    # local AI capture capability (heuristic)
    res["local_ai_available"] = (REPO_ROOT / "backend" / "local_ai") .exists()
    return res


if __name__ == "__main__":
    import json
    print(json.dumps(check_providers(), indent=2))
