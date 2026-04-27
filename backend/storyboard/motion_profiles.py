"""
Motion Profile System for Editorial Motion Engine

Defines motion profiles that control overall scene behavior and motion intensity.
"""

from enum import Enum
from typing import Dict, Any


class MotionProfile(str, Enum):
    static_clean = "static_clean"
    documentary_dynamic = "documentary_dynamic"
    kinetic_explainer = "kinetic_explainer"
    tutorial_followcam = "tutorial_followcam"


class MotionIntensity(str, Enum):
    low = "low"
    med = "med"
    high = "high"


# Profile configurations
MOTION_PROFILE_CONFIGS: Dict[str, Dict[str, Any]] = {
    MotionProfile.static_clean: {
        "description": "Clean, minimal motion for professional content",
        "max_static_hold": 3.0,  # seconds
        "micro_beat_frequency": 0.1,  # low frequency
        "drift_enabled": False,
        "pan_enabled": False,
    },
    MotionProfile.documentary_dynamic: {
        "description": "Subtle documentary-style motion for engagement",
        "max_static_hold": 1.8,
        "micro_beat_frequency": 0.5,
        "drift_enabled": True,
        "pan_enabled": True,
    },
    MotionProfile.kinetic_explainer: {
        "description": "Dynamic motion for explanatory content",
        "max_static_hold": 1.2,
        "micro_beat_frequency": 0.8,
        "drift_enabled": True,
        "pan_enabled": True,
    },
    MotionProfile.tutorial_followcam: {
        "description": "Follow camera style for tutorials and demos",
        "max_static_hold": 1.5,
        "micro_beat_frequency": 0.6,
        "drift_enabled": False,
        "pan_enabled": True,
    },
}


def get_profile_config(profile: MotionProfile, intensity: MotionIntensity) -> Dict[str, Any]:
    """Get configuration for a motion profile adjusted by intensity."""
    config = MOTION_PROFILE_CONFIGS[profile].copy()

    # Adjust based on intensity
    intensity_multiplier = {"low": 0.7, "med": 1.0, "high": 1.3}[intensity]

    config["max_static_hold"] *= intensity_multiplier
    config["micro_beat_frequency"] *= intensity_multiplier

    return config