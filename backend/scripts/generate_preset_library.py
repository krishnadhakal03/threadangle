"""Generate preset character library using Gemini or fallback placeholders.

Run from backend folder:
    python scripts/generate_preset_library.py
"""

import asyncio
import json
from pathlib import Path

from integrations.gemini_images import GeminiImageGenerator


PROFILES = [
    {"age": "20s", "gender": "female", "ethnicity": "asian", "style": "professional", "expression": "friendly"},
    {"age": "30s", "gender": "male", "ethnicity": "caucasian", "style": "professional", "expression": "neutral"},
    {"age": "40s", "gender": "female", "ethnicity": "african", "style": "professional", "expression": "serious"},
    {"age": "20s", "gender": "non-binary", "ethnicity": "mixed", "style": "casual", "expression": "excited"},
    {"age": "30s", "gender": "male", "ethnicity": "hispanic", "style": "creative", "expression": "thoughtful"},
    {"age": "50s", "gender": "female", "ethnicity": "middle-eastern", "style": "professional", "expression": "friendly"},
    {"age": "20s", "gender": "male", "ethnicity": "asian", "style": "casual", "expression": "neutral"},
    {"age": "40s", "gender": "female", "ethnicity": "caucasian", "style": "creative", "expression": "excited"},
    {"age": "30s", "gender": "non-binary", "ethnicity": "african", "style": "sporty", "expression": "serious"},
    {"age": "50s", "gender": "male", "ethnicity": "mixed", "style": "casual", "expression": "friendly"},
] * 5


async def main() -> None:
    output_dir = Path(__file__).resolve().parents[1] / "characters" / "presets"
    output_dir.mkdir(parents=True, exist_ok=True)

    gemini = GeminiImageGenerator()
    library = []

    for idx, profile in enumerate(PROFILES[:50], start=1):
        result = await gemini.generate_character_image(
            scene_description=f"{profile['expression']} presenter portrait",
            character_type=f"{profile['style']} person",
            style="photorealistic",
            consistent_features=profile,
        )

        preset_id = f"{profile['style']}_{profile['gender']}_{profile['age']}_{profile['expression']}_{profile['ethnicity']}_{idx}"
        rel_path = Path("characters") / "presets" / f"{preset_id}.png"
        abs_path = Path(__file__).resolve().parents[1] / rel_path
        result["image"].save(abs_path)

        library.append(
            {
                "id": preset_id,
                "name": f"{profile['style'].title()} {profile['gender'].title()} - {profile['age']} - {profile['expression'].title()}",
                "image_path": str(rel_path).replace("\\", "/"),
                "thumbnail": f"/api/characters/presets/{preset_id}.png",
                "profile": profile,
            }
        )
        print(f"Generated {idx}/50: {preset_id}")
        await asyncio.sleep(0.2)

    manifest = output_dir / "library.json"
    manifest.write_text(json.dumps(library, indent=2), encoding="utf-8")
    print(f"Saved preset manifest: {manifest}")


if __name__ == "__main__":
    asyncio.run(main())
