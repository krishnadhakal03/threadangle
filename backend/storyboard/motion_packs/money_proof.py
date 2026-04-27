"""
Money Proof Motion Pack

Reusable motion treatments for financial proof scenes.
"""

from typing import List


# Preset micro-beat sequences for money proofs
MONEY_PROOF_PRESETS = {
    "savings_reveal": [
        "proof_highlight",
        "value_tick",
        "zoom_punch"
    ],
    "before_after_split": [
        "split_reveal",
        "proof_highlight"
    ],
    "profit_pop": [
        "zoom_punch",
        "value_tick"
    ],
    "setup_transition": [
        "crop_shift",
        "documentary_drift"
    ]
}


def get_money_proof_sequence(preset: str) -> List[str]:
    """Get micro-beat sequence for a money proof preset."""
    return MONEY_PROOF_PRESETS.get(preset, [])