from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from storyboard.preview import generate_scene_previews
from storyboard.qa import run_qa
from storyboard.schema import VisualSource, load_storyboard, save_storyboard


router = APIRouter(prefix="/api/storyboard", tags=["Storyboard"])
REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "backend" / "storyboard" / "examples"
REVIEW_ROOT = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review"


class ReplaceRequest(BaseModel):
    asset_path: str
    visual_source: str | None = None


def _path(project_id: str) -> Path:
    path = EXAMPLES / f"{project_id}_storyboard.json"
    if not path.exists() and project_id == "day6_walmart":
        path = EXAMPLES / "day6_walmart_storyboard.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="storyboard not found")
    return path


@router.get("/{project_id}/review")
def review(project_id: str):
    storyboard = load_storyboard(_path(project_id))
    out = REVIEW_ROOT / storyboard.project_id / "review"
    manifest = generate_scene_previews(storyboard, REPO_ROOT, out)
    qa = run_qa(storyboard, REPO_ROOT, out / "qa_report.json", manifest)
    return {"manifest": manifest, "qa": qa}


@router.post("/{project_id}/scene/{scene_id}/replace")
def replace_scene(project_id: str, scene_id: str, request: ReplaceRequest):
    path = _path(project_id)
    storyboard = load_storyboard(path)
    for scene in storyboard.scenes:
        if scene.scene_id == scene_id:
            scene.asset_path = request.asset_path
            if request.visual_source:
                scene.visual_source = VisualSource(request.visual_source)
            save_storyboard(storyboard, path)
            return {"scene_id": scene_id, "asset_path": request.asset_path}
    raise HTTPException(status_code=404, detail="scene not found")


@router.post("/{project_id}/scene/{scene_id}/lock")
def lock_scene(project_id: str, scene_id: str):
    path = _path(project_id)
    storyboard = load_storyboard(path)
    for scene in storyboard.scenes:
        if scene.scene_id == scene_id:
            scene.lock_visual = True
            save_storyboard(storyboard, path)
            return {"scene_id": scene_id, "lock_visual": True}
    raise HTTPException(status_code=404, detail="scene not found")
