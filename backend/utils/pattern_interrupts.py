from typing import List, Dict


def build_interrupt_schedule(duration_seconds: float, min_gap: float = 3.0, max_gap: float = 5.0) -> List[Dict[str, object]]:
    total = max(1.0, float(duration_seconds or 1))
    interrupts = []
    t = min_gap
    index = 0
    types = ["zoom", "popup", "sfx", "scene_change"]

    while t < total:
        interrupts.append({
            "time": round(t, 2),
            "type": types[index % len(types)],
        })
        index += 1
        gap = min_gap if index % 2 == 0 else max_gap
        t += gap

    return interrupts
