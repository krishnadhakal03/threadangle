"""
Tutorial Followcam Motion Pack

Motion treatments for coding tutorials and demos.
"""

from typing import List


# Preset sequences for tutorial scenes
TUTORIAL_PRESETS = {
    "vscode_punch_in": [
        "punch_in",
        "focus_crop",
        "zoom_punch"
    ],
    "code_change_focus": [
        "focus_crop",
        "proof_highlight"
    ],
    "terminal_insert": [
        "crop_shift",
        "punch_in"
    ],
    "browser_reveal": [
        "split_reveal",
        "documentary_drift"
    ]
}


def get_tutorial_sequence(preset: str) -> List[str]:
    """Get micro-beat sequence for a tutorial preset."""
    return TUTORIAL_PRESETS.get(preset, [])