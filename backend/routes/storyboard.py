from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from storyboard.preview import generate_scene_previews
from storyboard.qa import run_qa
from storyboard.render import regenerate_audio_captions_and_restitch, render_draft_video
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


@router.post("/{project_id}/scene/{scene_id}/upload_manual_capture")
async def upload_manual_capture(project_id: str, scene_id: str, file: UploadFile = File(...)):
    path = _path(project_id)
    storyboard = load_storyboard(path)
    for scene in storyboard.scenes:
        if scene.scene_id == scene_id:
            # Save uploaded file
            upload_dir = REVIEW_ROOT / storyboard.project_id / "manual_captures"
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / f"{scene_id}_{file.filename}"
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Update scene
            scene.asset_path = str(file_path)
            scene.visual_source = VisualSource.user_manual_capture
            scene.privacy_reviewed = True
            scene.capture_notes = f"Manual upload: {file.filename}"
            save_storyboard(storyboard, path)
            return {"scene_id": scene_id, "asset_path": str(file_path)}
    raise HTTPException(status_code=404, detail="scene not found")


@router.post("/{project_id}/regenerate/audio")
def regenerate_audio(project_id: str):
    path = _path(project_id)
    storyboard = load_storyboard(path)
    # Need to implement audio regeneration
    # For now, placeholder
    return {"project_id": project_id, "action": "regenerate_audio"}


@router.post("/{project_id}/regenerate/captions")
def regenerate_captions(project_id: str):
    path = _path(project_id)
    storyboard = load_storyboard(path)
    # Placeholder
    return {"project_id": project_id, "action": "regenerate_captions"}


@router.post("/{project_id}/render/final")
def render_final(project_id: str):
    path = _path(project_id)
    storyboard = load_storyboard(path)
    out_dir = REVIEW_ROOT / storyboard.project_id / "final_render"
    result = render_draft_video(storyboard, REPO_ROOT, out_dir)
    return result
