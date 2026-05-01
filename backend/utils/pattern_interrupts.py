"""Pattern-interrupt planning for short-form video scenes."""

from __future__ import annotations

from typing import Any, Dict, List


PATTERN_INTERRUPT_PRIMITIVES = (
    "punch_zoom",
    "number_flip",
    "red_circle",
    "highlight",
    "swipe_transition",
    "checklist_tick",
    "split_screen_before_after",
    "warning_label",
    "payoff_meter",
)


def _scene_value(scene: Any, key: str, default: Any = None) -> Any:
    if isinstance(scene, dict):
        return scene.get(key, default)
    return getattr(scene, key, default)


def _scene_text(scene: Any) -> str:
    fields = (
        "narration_text",
        "caption_text",
        "subtitle",
        "source_text",
        "on_screen_text",
        "visual_description",
    )
    return " ".join(str(_scene_value(scene, field, "") or "") for field in fields).lower()


def infer_scene_interrupt_role(scene: Any) -> str:
    template = str(_scene_value(scene, "template", "") or "").lower()
    part = str(_scene_value(scene, "part", "") or "").lower()
    scene_id = str(_scene_value(scene, "id", "") or _scene_value(scene, "scene_id", "") or "").lower()
    text = _scene_text(scene)
    combined = f"{template} {part} {scene_id} {text}"
    if "hook" in combined:
        return "hook"
    if any(term in combined for term in ("payoff", "savings", "save", "$", "number")):
        return "payoff"
    if any(term in combined for term in ("checklist", "step", "first", "second", "third")):
        return "checklist"
    if any(term in combined for term in ("compare", "before", "after", "split")):
        return "comparison"
    if any(term in combined for term in ("warning", "stop", "mistake", "risk")):
        return "warning"
    return "body"


def _primitive_sequence_for_role(role: str, text: str) -> list[str]:
    base = {
        "hook": ["punch_zoom", "warning_label", "red_circle"],
        "payoff": ["number_flip", "payoff_meter", "highlight"],
        "comparison": ["split_screen_before_after", "swipe_transition", "red_circle"],
        "checklist": ["checklist_tick", "highlight", "swipe_transition"],
        "warning": ["warning_label", "punch_zoom", "red_circle"],
        "body": ["highlight", "swipe_transition", "punch_zoom"],
    }[role]
    if role != "hook" and "$" in text and "number_flip" not in base:
        return ["number_flip", *base]
    return base


def _instruction_for_primitive(primitive: str, role: str) -> str:
    instructions = {
        "punch_zoom": "Fast push-in on the main proof object or claim text.",
        "number_flip": "Flip or count into the key number without covering captions.",
        "red_circle": "Circle the exact object or line item being discussed.",
        "highlight": "Highlight the active word, object, or receipt row.",
        "swipe_transition": "Swipe into the next proof angle or visual state.",
        "checklist_tick": "Tick one checklist item as the narration advances.",
        "split_screen_before_after": "Show before/after states side by side.",
        "warning_label": "Flash a short warning label near the top safe area.",
        "payoff_meter": "Fill a small payoff meter toward the revealed result.",
    }
    return f"{instructions[primitive]} Role: {role}."


def build_scene_interrupt_schedule(
    scene: Any,
    *,
    scene_index: int = 0,
    scene_start: float = 0.0,
    cadence_seconds: float = 1.35,
    max_interrupts_per_scene: int = 3,
) -> list[dict[str, Any]]:
    duration = max(0.0, float(_scene_value(scene, "duration", 0) or 0))
    if duration < 1.2:
        return []
    text = _scene_text(scene)
    role = infer_scene_interrupt_role(scene)
    sequence = _primitive_sequence_for_role(role, text)
    caption_words = len(str(_scene_value(scene, "caption_text", "") or _scene_value(scene, "subtitle", "") or "").split())
    readable_limit = 1 if caption_words >= 14 else max_interrupts_per_scene
    limit = max(1, min(max_interrupts_per_scene, readable_limit))
    first_time = 0.75 if role == "hook" else min(1.1, duration * 0.45)
    interrupts: list[dict[str, Any]] = []
    local_time = first_time
    index = 0
    while local_time < duration - 0.25 and len(interrupts) < limit:
        primitive = sequence[index % len(sequence)]
        interrupts.append(
            {
                "scene_index": scene_index,
                "scene_id": _scene_value(scene, "id", None) or _scene_value(scene, "scene_id", None) or scene_index + 1,
                "scene_role": role,
                "time": round(scene_start + local_time, 2),
                "local_time": round(local_time, 2),
                "type": primitive,
                "instruction": _instruction_for_primitive(primitive, role),
                "readability_guard": {
                    "avoid_caption_overlap": True,
                    "max_interrupts_per_scene": limit,
                    "min_gap_seconds": cadence_seconds,
                },
            }
        )
        index += 1
        local_time += cadence_seconds
    return interrupts


def build_pattern_interrupt_plan(
    scenes: list[Any],
    *,
    cadence_seconds: float = 1.35,
    max_interrupts_per_scene: int = 3,
) -> dict[str, Any]:
    elapsed = 0.0
    scene_rows = []
    all_interrupts: list[dict[str, Any]] = []
    for index, scene in enumerate(scenes):
        duration = max(0.0, float(_scene_value(scene, "duration", 0) or 0))
        role = infer_scene_interrupt_role(scene)
        interrupts = build_scene_interrupt_schedule(
            scene,
            scene_index=index,
            scene_start=elapsed,
            cadence_seconds=cadence_seconds,
            max_interrupts_per_scene=max_interrupts_per_scene,
        )
        scene_rows.append(
            {
                "scene_index": index,
                "scene_id": _scene_value(scene, "id", None) or _scene_value(scene, "scene_id", None) or index + 1,
                "duration": round(duration, 2),
                "scene_role": role,
                "interrupt_count": len(interrupts),
                "interrupts": interrupts,
            }
        )
        all_interrupts.extend(interrupts)
        elapsed += duration
    return {
        "schema_version": 1,
        "primitives": list(PATTERN_INTERRUPT_PRIMITIVES),
        "cadence_seconds": cadence_seconds,
        "clutter_guard": {
            "avoid_caption_overlap": True,
            "max_interrupts_per_scene": max_interrupts_per_scene,
            "skip_scenes_shorter_than_seconds": 1.2,
        },
        "scenes": scene_rows,
        "interrupts": all_interrupts,
        "debug": {
            "scene_count": len(scenes),
            "interrupt_count": len(all_interrupts),
            "render_required": False,
        },
    }


def attach_pattern_interrupts_to_report(report: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    updated = dict(report or {})
    updated["pattern_interrupt_plan"] = plan
    scene_by_id = {str(row["scene_id"]): row for row in plan.get("scenes", [])}
    scene_reports = []
    for row in updated.get("scene_reports") or []:
        scene_report = dict(row)
        scene_id = str(scene_report.get("scene_id"))
        scene_report["planned_pattern_interrupts"] = (scene_by_id.get(scene_id) or {}).get("interrupts", [])
        scene_reports.append(scene_report)
    if scene_reports:
        updated["scene_reports"] = scene_reports
    return updated


def build_interrupt_schedule(duration_seconds: float, min_gap: float = 3.0, max_gap: float = 5.0) -> List[Dict[str, object]]:
    """Backward-compatible simple endpoint schedule."""
    total = max(1.0, float(duration_seconds or 1))
    interrupts = []
    t = min_gap
    index = 0
    types = ["punch_zoom", "highlight", "warning_label", "swipe_transition"]

    while t < total:
        interrupts.append({
            "time": round(t, 2),
            "type": types[index % len(types)],
        })
        index += 1
        gap = min_gap if index % 2 == 0 else max_gap
        t += gap

    return interrupts
