"""Check HMR local/free asset readiness for grocery scene intelligence slices."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from .hmr_scene_asset_strategy import detect_hmr_asset_domain_from_text, local_asset_domain_folders
except ImportError:  # pragma: no cover - direct script execution fallback
    from hmr_scene_asset_strategy import detect_hmr_asset_domain_from_text, local_asset_domain_folders


VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v", ".webm")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
REQUIRED_SCENE_ROLES = ("hook", "reveal")
OPTIONAL_SCENE_ROLES = ("payoff", "cta")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def local_asset_root(domain: str | None = None) -> Path:
    return local_asset_roots(domain)[0]


def local_asset_roots(domain: str | None = None) -> list[Path]:
    root = repo_root() / "assets" / "hmr_local"
    return [root / folder for folder in local_asset_domain_folders(domain)]


def load_local_env(keys: tuple[str, ...] = ("PEXELS_API_KEY", "PIXABAY_API_KEY")) -> dict[str, Any]:
    """Load selected keys from local .env files without exposing values."""
    loaded_from: list[str] = []
    env_files = [repo_root() / ".env", repo_root() / "backend" / ".env"]
    for path in env_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        file_loaded = False
        for key in keys:
            if os.getenv(key):
                continue
            match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
            if not match:
                continue
            value = match.group(1).strip().strip('"').strip("'")
            if value:
                os.environ[key] = value
                file_loaded = True
        if file_loaded:
            loaded_from.append(str(path))
    return {
        "env_files_checked": [str(path) for path in env_files],
        "loaded_from": loaded_from,
    }


def _configured_env(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def _candidate_names(role: str) -> list[str]:
    return [f"{role}{ext}" for ext in (*VIDEO_EXTENSIONS, *IMAGE_EXTENSIONS)]


def _existing_role_files(root: Path, role: str) -> list[str]:
    return [
        str(root / name)
        for name in _candidate_names(role)
        if (root / name).exists() and (root / name).is_file()
    ]


def _existing_role_files_in_roots(roots: list[Path], role: str) -> list[str]:
    files: list[str] = []
    for root in roots:
        files.extend(_existing_role_files(root, role))
    return files


def check_hmr_asset_readiness(
    asset_dir: str | Path | None = None,
    load_env: bool = True,
    *,
    domain: str | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    env_load = load_local_env() if load_env else {"env_files_checked": [], "loaded_from": []}
    resolved_domain = domain or detect_hmr_asset_domain_from_text(topic or "")
    roots = [Path(asset_dir).expanduser().resolve()] if asset_dir else local_asset_roots(resolved_domain)
    root = roots[0]
    provider_keys = {
        "PEXELS_API_KEY": _configured_env("PEXELS_API_KEY"),
        "PIXABAY_API_KEY": _configured_env("PIXABAY_API_KEY"),
    }
    provider_ready = any(provider_keys.values())
    local_assets = {
        role: {
            "exists": bool(_existing_role_files_in_roots(roots, role)),
            "files": _existing_role_files_in_roots(roots, role),
            "accepted_filenames": _candidate_names(role),
        }
        for role in (*REQUIRED_SCENE_ROLES, *OPTIONAL_SCENE_ROLES)
    }
    hook_reveal_ready = all(local_assets[role]["exists"] for role in REQUIRED_SCENE_ROLES)
    ready = provider_ready or hook_reveal_ready
    missing_required = [
        f"{role}.mp4 or {role}.jpg"
        for role in REQUIRED_SCENE_ROLES
        if not local_assets[role]["exists"]
    ]
    return {
        "status": "PASS" if ready else "BLOCKED",
        "ready_for_slice_c_real_render": ready,
        "provider_ready": provider_ready,
        "provider_keys": provider_keys,
        "env_loaded": bool(env_load["loaded_from"]),
        "env_files_checked": env_load["env_files_checked"],
        "env_loaded_from": env_load["loaded_from"],
        "asset_dir": str(root),
        "asset_dirs_checked": [str(path) for path in roots],
        "domain": resolved_domain or "grocery_savings",
        "local_hook_reveal_ready": hook_reveal_ready,
        "local_assets": local_assets,
        "missing_required": missing_required,
        "required_setup": [
            "Set PEXELS_API_KEY or PIXABAY_API_KEY for free stock lookup.",
            f"Or add local files under one of {', '.join(str(path) for path in roots)}: hook.mp4 or hook.jpg, and reveal.mp4 or reveal.jpg.",
        ],
    }


def _format_report(report: dict[str, Any]) -> str:
    lines = [
        f"HMR asset readiness: {report['status']}",
        f"Provider ready: {report['provider_ready']}",
        f"PEXELS_API_KEY configured: {report['provider_keys']['PEXELS_API_KEY']}",
        f"PIXABAY_API_KEY configured: {report['provider_keys']['PIXABAY_API_KEY']}",
        f".env loaded: {report['env_loaded']}",
        f"Local asset dir: {report['asset_dir']}",
        f"Local asset dirs checked: {', '.join(report.get('asset_dirs_checked') or [report['asset_dir']])}",
        f"Domain: {report.get('domain', 'grocery_savings')}",
        f"Local hook/reveal ready: {report['local_hook_reveal_ready']}",
    ]
    for role, meta in report["local_assets"].items():
        files = ", ".join(meta["files"]) if meta["files"] else "missing"
        lines.append(f"{role}: {files}")
    if report["status"] == "BLOCKED":
        lines.append("Missing first-four-second assets:")
        lines.extend(f"- {item}" for item in report["missing_required"])
        lines.append("Setup:")
        lines.extend(f"- {item}" for item in report["required_setup"])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check HMR local/free asset readiness.")
    parser.add_argument("--asset-dir", default=None, help="Override local asset directory.")
    parser.add_argument("--domain", default=None, help="Optional HMR local asset domain, e.g. bill_leak.")
    parser.add_argument("--topic", default=None, help="Optional topic text used to infer the HMR asset domain.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = check_hmr_asset_readiness(args.asset_dir, domain=args.domain, topic=args.topic)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format_report(report))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
