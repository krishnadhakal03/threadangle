from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _patch_materialization_dependencies(monkeypatch):
    from utils import hmr_ui_productization

    def fake_qa(_render_result):
        return {
            "technical_status": "PASS",
            "postability_status": "NEEDS_REVIEW",
            "postability_score": {"average_score": 7},
            "human_posting_gate": "MANUAL_REVIEW_REQUIRED",
        }

    def fake_create_review_package(output_dir, video=None, review_root=None):
        source = Path(review_root) / "source_review_package"
        source.mkdir(parents=True, exist_ok=True)
        (source / "manifest.json").write_text(json.dumps({"frozen": False}) + "\n", encoding="utf-8")
        (source / "review_summary.md").write_text("# New package\n", encoding="utf-8")
        (source / "contact_sheet.jpg").write_bytes(b"jpg")
        (source / "new.txt").write_text(f"video={video}\noutput={output_dir}\n", encoding="utf-8")
        return {
            "review_dir": str(source),
            "manifest": str(source / "manifest.json"),
            "summary": str(source / "review_summary.md"),
            "contact_sheet": str(source / "contact_sheet.jpg"),
        }

    monkeypatch.setattr(hmr_ui_productization, "run_hybrid_motion_qa", fake_qa)
    monkeypatch.setattr(hmr_ui_productization, "create_review_package", fake_create_review_package)
    return hmr_ui_productization


def _materialize(monkeypatch, tmp_path, *, run_id="retry-run"):
    hmr_ui_productization = _patch_materialization_dependencies(monkeypatch)
    generated_root = tmp_path / "generated_videos"
    video = tmp_path / "input.mp4"
    video.write_bytes(b"fake video")
    metadata = hmr_ui_productization.materialize_hmr_ui_review_workflow(
        generated_root=generated_root,
        run_id=run_id,
        video_path=video,
        render_result={
            "topic": "retry policy",
            "scene_reports": [{"headline": "Keep the old package safe"}],
        },
        script_text="Keep the old package safe.",
        scenes=[{"scene_id": "hook"}],
    )
    return metadata, generated_root / "hmr_ui_runs" / run_id


def test_materialize_archives_existing_non_frozen_review_package(monkeypatch, tmp_path):
    run_dir = tmp_path / "generated_videos" / "hmr_ui_runs" / "retry-run"
    review_dir = run_dir / "review_package"
    review_dir.mkdir(parents=True)
    (review_dir / "old.txt").write_text("do not delete\n", encoding="utf-8")
    (review_dir / "manifest.json").write_text(json.dumps({"frozen": False}) + "\n", encoding="utf-8")

    metadata, run_dir = _materialize(monkeypatch, tmp_path)

    archive_path = Path(metadata["previous_review_package_archive"])
    assert metadata["previous_review_package_status"] == "archived"
    assert archive_path.parent == run_dir / "_archived_review_packages"
    assert (archive_path / "old.txt").read_text(encoding="utf-8") == "do not delete\n"
    assert (run_dir / "review_package" / "new.txt").exists()
    assert not (run_dir / "review_package" / "old.txt").exists()


def test_materialize_refuses_existing_frozen_review_package(monkeypatch, tmp_path):
    from utils.hmr_artifact_manifest import FrozenArtifactError

    hmr_ui_productization = _patch_materialization_dependencies(monkeypatch)
    monkeypatch.setattr(
        hmr_ui_productization,
        "create_review_package",
        lambda *args, **kwargs: pytest.fail("frozen review package should block before package creation"),
    )
    generated_root = tmp_path / "generated_videos"
    run_dir = generated_root / "hmr_ui_runs" / "frozen-run"
    review_dir = run_dir / "review_package"
    review_dir.mkdir(parents=True)
    (review_dir / "old.txt").write_text("protected\n", encoding="utf-8")
    (review_dir / "manifest.json").write_text(
        json.dumps({"frozen": True, "human_posting_gate": "READY_FOR_HUMAN_POST_REVIEW"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(FrozenArtifactError):
        hmr_ui_productization.materialize_hmr_ui_review_workflow(
            generated_root=generated_root,
            run_id="frozen-run",
            video_path=tmp_path / "input.mp4",
            render_result={"topic": "frozen"},
            script_text="Frozen package.",
            scenes=[],
        )

    assert (review_dir / "old.txt").read_text(encoding="utf-8") == "protected\n"


def test_materialize_preserves_unrelated_run_files_on_retry(monkeypatch, tmp_path):
    run_dir = tmp_path / "generated_videos" / "hmr_ui_runs" / "retry-run"
    review_dir = run_dir / "review_package"
    review_dir.mkdir(parents=True)
    (review_dir / "old.txt").write_text("archive me\n", encoding="utf-8")
    (run_dir / "operator_notes.txt").write_text("keep this beside the package\n", encoding="utf-8")

    _metadata, run_dir = _materialize(monkeypatch, tmp_path)

    assert (run_dir / "operator_notes.txt").read_text(encoding="utf-8") == "keep this beside the package\n"
    assert (run_dir / "review_package" / "new.txt").exists()
