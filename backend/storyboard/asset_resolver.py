from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .provider_router import ProviderDecision, route_scene_provider
from .schema import Storyboard, StoryboardScene


@dataclass
class ResolvedSceneAsset:
    scene: StoryboardScene
    decision: ProviderDecision

    @property
    def exists(self) -> bool:
        return self.decision.asset_path is not None and self.decision.asset_path.exists()


def resolve_scene_asset(storyboard: Storyboard, scene: StoryboardScene, repo_root: Path) -> ResolvedSceneAsset:
    return ResolvedSceneAsset(scene=scene, decision=route_scene_provider(scene, repo_root))


def resolve_assets(storyboard: Storyboard, repo_root: Path) -> list[ResolvedSceneAsset]:
    return [resolve_scene_asset(storyboard, scene, repo_root) for scene in storyboard.scenes]
