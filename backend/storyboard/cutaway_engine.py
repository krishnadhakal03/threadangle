"""
Cutaway / Micro B-Roll Support Engine

Complete local asset cutaway routing for editorial density.
Supports local stock clips, icon/diagram inserts, supporting micro b-roll, 1 second inserts.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from .schema import StoryboardScene


@dataclass
class CutawayAsset:
    """A cutaway asset for insertion."""
    asset_path: Path
    duration: float = 1.0  # Default 1 second
    category: str = "general"  # stock, icon, diagram, broll
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class CutawayLibrary:
    """Library of available cutaway assets."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.cutaways_dir = repo_root / "assets" / "cutaways"
        self.stock_dir = self.cutaways_dir / "stock"
        self.icons_dir = self.cutaways_dir / "icons"
        self.diagrams_dir = self.cutaways_dir / "diagrams"
        self.broll_dir = self.cutaways_dir / "broll"

        self._assets: List[CutawayAsset] = []
        self._load_assets()

    def _load_assets(self) -> None:
        """Load available cutaway assets."""
        # Stock clips
        if self.stock_dir.exists():
            for asset_path in self.stock_dir.glob("**/*"):
                if asset_path.is_file() and asset_path.suffix.lower() in ['.mp4', '.mov', '.jpg', '.png']:
                    self._assets.append(CutawayAsset(
                        asset_path=asset_path,
                        category="stock",
                        tags=self._extract_tags(asset_path)
                    ))

        # Icons
        if self.icons_dir.exists():
            for asset_path in self.icons_dir.glob("**/*"):
                if asset_path.is_file() and asset_path.suffix.lower() in ['.png', '.svg']:
                    self._assets.append(CutawayAsset(
                        asset_path=asset_path,
                        duration=0.5,  # Shorter for icons
                        category="icon",
                        tags=self._extract_tags(asset_path)
                    ))

        # Diagrams
        if self.diagrams_dir.exists():
            for asset_path in self.diagrams_dir.glob("**/*"):
                if asset_path.is_file() and asset_path.suffix.lower() in ['.png', '.jpg', '.svg']:
                    self._assets.append(CutawayAsset(
                        asset_path=asset_path,
                        duration=1.5,  # Longer for diagrams
                        category="diagram",
                        tags=self._extract_tags(asset_path)
                    ))

        # B-roll
        if self.broll_dir.exists():
            for asset_path in self.broll_dir.glob("**/*"):
                if asset_path.is_file() and asset_path.suffix.lower() in ['.mp4', '.mov']:
                    self._assets.append(CutawayAsset(
                        asset_path=asset_path,
                        duration=2.0,  # Longer for b-roll
                        category="broll",
                        tags=self._extract_tags(asset_path)
                    ))

    def _extract_tags(self, asset_path: Path) -> List[str]:
        """Extract tags from asset filename/path."""
        # Simple tag extraction from filename
        name = asset_path.stem.lower()
        tags = []

        # Common tag mappings
        tag_mappings = {
            "money": ["finance", "cash", "dollar"],
            "coffee": ["drink", "cafe", "beverage"],
            "computer": ["tech", "screen", "keyboard"],
            "phone": ["mobile", "device"],
            "chart": ["data", "graph", "analytics"],
            "arrow": ["direction", "point"],
            "check": ["yes", "confirm", "success"],
            "x": ["no", "cancel", "wrong"]
        }

        for keyword, asset_tags in tag_mappings.items():
            if keyword in name:
                tags.extend(asset_tags)

        # Add filename parts as tags
        parts = name.split('_')
        tags.extend(parts)

        return list(set(tags))  # Deduplicate

    def find_cutaways(self, tags: List[str], category: Optional[str] = None,
                      max_duration: float = 2.0) -> List[CutawayAsset]:
        """Find cutaway assets matching criteria."""
        matches = []

        for asset in self._assets:
            if asset.duration > max_duration:
                continue
            if category and asset.category != category:
                continue

            # Check if any requested tag matches asset tags
            if tags and not any(tag in asset.tags for tag in tags):
                continue

            matches.append(asset)

        return matches

    def get_semantic_cutaways(self, scene: StoryboardScene) -> List[CutawayAsset]:
        """Get semantically relevant cutaways for a scene."""
        narration = (scene.narration_text or "").lower()
        tags = []

        # Extract semantic tags from narration
        semantic_mappings = {
            "money": ["$", "dollar", "cost", "price", "save", "spend"],
            "coffee": ["coffee", "latte", "espresso", "brew"],
            "computer": ["computer", "screen", "code", "program"],
            "data": ["data", "chart", "graph", "analytics"],
            "time": ["clock", "watch", "hour", "minute"],
            "success": ["check", "yes", "success", "win"],
            "error": ["x", "no", "error", "wrong"]
        }

        for semantic_tag, keywords in semantic_mappings.items():
            if any(keyword in narration for keyword in keywords):
                tags.append(semantic_tag)

        if not tags:
            tags = ["general"]  # Fallback

        return self.find_cutaways(tags, max_duration=1.5)


class CutawayEngine:
    """Engine for managing cutaway insertions."""

    def __init__(self, repo_root: Path):
        self.library = CutawayLibrary(repo_root)

    def suggest_cutaways(self, scene: StoryboardScene) -> List[CutawayAsset]:
        """Suggest appropriate cutaways for a scene."""
        if scene.beat_role.value == "payoff":
            return []  # No cutaways for payoff

        # Get semantic cutaways
        semantic = self.library.get_semantic_cutaways(scene)

        # If not enough semantic, add general cutaways
        if len(semantic) < 2:
            general = self.library.find_cutaways(["general"], max_duration=1.0)
            semantic.extend(general[:2 - len(semantic)])

        return semantic[:3]  # Max 3 suggestions

    def apply_cutaway_routing(self, scene: StoryboardScene) -> None:
        """Apply cutaway routing to scene."""
        suggestions = self.suggest_cutaways(scene)

        # Add to supporting_cutaways (as asset paths)
        for cutaway in suggestions:
            relative_path = cutaway.asset_path.relative_to(self.library.repo_root)
            scene.supporting_cutaways.append(str(relative_path))

        # Ensure cutaways are unique
        scene.supporting_cutaways = list(set(scene.supporting_cutaways))

    def validate_cutaway_assets(self, scene: StoryboardScene, repo_root: Path) -> List[str]:
        """Validate that cutaway assets exist."""
        issues = []
        for cutaway_path in scene.supporting_cutaways:
            full_path = repo_root / cutaway_path
            if not full_path.exists():
                issues.append(f"Cutaway asset missing: {cutaway_path}")
        return issues