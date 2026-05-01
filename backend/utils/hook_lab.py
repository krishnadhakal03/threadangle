"""Deterministic Hook Lab generation, scoring, ranking, and selection."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


HOOK_SCORE_DIMENSIONS = (
    "curiosity",
    "specificity",
    "emotional_pull",
    "clarity",
    "speed_to_payoff",
    "first_2_seconds_strength",
)


@dataclass
class HookCandidate:
    id: str
    text: str
    archetype: str
    scores: dict[str, int]
    total_score: int
    rank: int
    why_it_works: str
    selected: bool = False
    override: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _topic_phrase(topic: str) -> str:
    cleaned = _clean_text(topic).strip(".")
    return cleaned[:1].lower() + cleaned[1:] if cleaned else "this"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:48] or "hook"


def generate_local_hook_variants(topic: str, *, category: str | None = None, count: int = 8) -> list[dict[str, str]]:
    """Generate local hook variants without paid APIs."""
    phrase = _topic_phrase(topic)
    category_label = _clean_text(category or "audience")
    templates = [
        ("curiosity_gap", f"The part nobody checks before {phrase}."),
        ("specific_number", f"I found a $27 leak hiding inside {phrase}."),
        ("mistake_reversal", f"Stop fixing {phrase} until you check this first."),
        ("personal_discovery", f"I almost missed the simplest way to improve {phrase}."),
        ("fast_payoff", f"Give me 10 seconds and I will show the payoff inside {phrase}."),
        ("emotional_pain", f"This is why {phrase} keeps feeling more expensive than it should."),
        ("clear_promise", f"Here is the 3-step check for {phrase}."),
        ("pattern_interrupt", f"Wait. {phrase.capitalize()} has a hidden first move."),
        ("review_challenge", f"Before you choose {phrase}, compare these two numbers."),
        ("category_callout", f"If you care about {category_label}, check {phrase} this way."),
    ]
    bounded_count = max(5, min(10, int(count or 8)))
    return [
        {"id": f"{idx + 1:02d}_{archetype}", "archetype": archetype, "text": text}
        for idx, (archetype, text) in enumerate(templates[:bounded_count])
    ]


def _score_curiosity(text: str) -> int:
    terms = ("nobody", "hidden", "missed", "before", "wait", "why", "first")
    return min(10, 4 + sum(2 for term in terms if term in text.lower()))


def _score_specificity(text: str) -> int:
    has_number = bool(re.search(r"(\$?\d+|\b(one|two|three|ten)\b)", text.lower()))
    concrete_words = len([word for word in re.findall(r"[a-zA-Z$0-9]+", text) if len(word) >= 5])
    return min(10, 4 + (3 if has_number else 0) + min(3, concrete_words // 2))


def _score_emotional_pull(text: str) -> int:
    terms = ("stop", "leak", "expensive", "missed", "wrong", "hidden", "payoff", "care")
    return min(10, 3 + sum(2 for term in terms if term in text.lower()))


def _score_clarity(text: str) -> int:
    word_count = len(text.split())
    if word_count <= 12:
        return 9
    if word_count <= 18:
        return 8
    if word_count <= 24:
        return 6
    return 4


def _score_speed_to_payoff(text: str) -> int:
    terms = ("10 seconds", "show", "payoff", "check", "here is", "first", "compare")
    return min(10, 4 + sum(2 for term in terms if term in text.lower()))


def _score_first_2_seconds_strength(text: str) -> int:
    first_words = " ".join(text.split()[:5]).lower()
    terms = ("wait", "stop", "i found", "the part", "give me", "before")
    return min(10, 4 + sum(2 for term in terms if term in first_words))


def score_hook(text: str) -> dict[str, int]:
    cleaned = _clean_text(text)
    scores = {
        "curiosity": _score_curiosity(cleaned),
        "specificity": _score_specificity(cleaned),
        "emotional_pull": _score_emotional_pull(cleaned),
        "clarity": _score_clarity(cleaned),
        "speed_to_payoff": _score_speed_to_payoff(cleaned),
        "first_2_seconds_strength": _score_first_2_seconds_strength(cleaned),
    }
    return {key: max(1, min(10, int(value))) for key, value in scores.items()}


def rank_hook_candidates(variants: list[dict[str, str]]) -> list[HookCandidate]:
    candidates: list[HookCandidate] = []
    for index, variant in enumerate(variants):
        text = _clean_text(variant.get("text", ""))
        scores = score_hook(text)
        total = sum(scores[dimension] for dimension in HOOK_SCORE_DIMENSIONS)
        candidates.append(
            HookCandidate(
                id=variant.get("id") or f"{index + 1:02d}_{_slug(text)}",
                text=text,
                archetype=variant.get("archetype") or "manual",
                scores=scores,
                total_score=total,
                rank=0,
                why_it_works=_why_it_works(scores),
            )
        )
    candidates.sort(key=lambda item: (item.total_score, item.scores["first_2_seconds_strength"]), reverse=True)
    for rank, candidate in enumerate(candidates, start=1):
        candidate.rank = rank
    return candidates


def _why_it_works(scores: dict[str, int]) -> str:
    top = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:2]
    labels = {
        "curiosity": "opens a curiosity gap",
        "specificity": "uses concrete detail",
        "emotional_pull": "creates emotional tension",
        "clarity": "stays easy to parse",
        "speed_to_payoff": "promises a fast payoff",
        "first_2_seconds_strength": "starts with a strong first beat",
    }
    return " and ".join(labels[key] for key, _ in top) + "."


def select_hook_candidate(
    candidates: list[HookCandidate],
    *,
    selected_hook_id: str | None = None,
    override_hook: str | None = None,
) -> HookCandidate:
    for candidate in candidates:
        candidate.selected = False
        candidate.override = False
    override_text = _clean_text(override_hook or "")
    if override_text:
        scores = score_hook(override_text)
        return HookCandidate(
            id="manual_override",
            text=override_text,
            archetype="manual_override",
            scores=scores,
            total_score=sum(scores.values()),
            rank=0,
            why_it_works="Manual review override selected by Krishna.",
            selected=True,
            override=True,
        )
    selected = next((candidate for candidate in candidates if candidate.id == selected_hook_id), None)
    selected = selected or (candidates[0] if candidates else None)
    if selected is None:
        raise ValueError("No hook candidates available for selection.")
    selected.selected = True
    return selected


def build_hook_lab(
    *,
    topic: str,
    category: str | None = None,
    candidate_count: int = 8,
    selected_hook_id: str | None = None,
    override_hook: str | None = None,
) -> dict[str, Any]:
    topic_text = _clean_text(topic)
    if not topic_text:
        raise ValueError("Topic cannot be empty.")
    variants = generate_local_hook_variants(topic_text, category=category, count=candidate_count)
    candidates = rank_hook_candidates(variants)
    selected = select_hook_candidate(candidates, selected_hook_id=selected_hook_id, override_hook=override_hook)
    if selected.override:
        ranked = candidates
    else:
        ranked = candidates
    return {
        "schema_version": 1,
        "topic": topic_text,
        "category": _clean_text(category or ""),
        "candidate_count": len(ranked),
        "score_dimensions": list(HOOK_SCORE_DIMENSIONS),
        "candidates": [candidate.to_dict() for candidate in ranked],
        "selected_hook": selected.to_dict(),
        "manifest_metadata": build_hook_lab_metadata(selected_hook=selected, candidates=ranked),
        "paid_providers_used": {
            "elevenlabs": False,
            "runwayml": False,
            "paid_llm": False,
        },
    }


def build_hook_lab_metadata(*, selected_hook: HookCandidate, candidates: list[HookCandidate]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "selected_hook_id": selected_hook.id,
        "selected_hook_text": selected_hook.text,
        "selected_hook_score": selected_hook.total_score,
        "selected_hook_scores": dict(selected_hook.scores),
        "selected_hook_archetype": selected_hook.archetype,
        "manual_override": selected_hook.override,
        "ranked_candidate_ids": [candidate.id for candidate in candidates],
        "score_dimensions": list(HOOK_SCORE_DIMENSIONS),
    }
