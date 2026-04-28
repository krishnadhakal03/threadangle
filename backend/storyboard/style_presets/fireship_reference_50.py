"""Style preset: fireship_reference_50

Extracted editing grammar (generic) — not copying creator assets.
This preset provides targets/rules the Creative Director and Edit planner
can use to steer visual choices.
"""
preset = {
    "name": "fireship_reference_50",
    "default_shot_duration_target": 1.2,  # seconds
    "interrupt_cadence_sec": [0.8, 1.0, 1.4],
    "micro_beat_density": 0.9,  # high micro beats per second
    "text_overlay": {
        "font_size_ratio": 0.08,
        "placement": "bottom_right",
        "max_words": 4,
        "style": "bold,short-phrases",
    },
    "cutaway_rules": {
        "broll_max_len": 1.8,
        "broll_min_len": 0.6,
        "insert_freq_per_10s": 3,
    },
    "zoom_rules": {
        "punch_prob_per_cut": 0.25,
        "max_zoom_in_sec": 0.5,
    },
    "progressive_reveal": {
        "stagger_text": True,
        "reveal_layers": ["base_image", "highlight", "numbers"]
    },
    "sound_accents": ["hit", "whoosh"],
    "forbidden_patterns": [
        "long_static_text_cards",
        "single_background_repeated",
    ],
}
