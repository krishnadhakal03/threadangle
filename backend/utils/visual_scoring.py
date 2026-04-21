"""
Visual Importance Scoring — heuristic-only, zero API credits consumed.

Claude-powered scoring is available behind ENABLE_VISUAL_AI_SCORING=true env flag.
During development the default heuristic path runs entirely offline.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Tuple

# ── Credit rates per 5-second bucket ─────────────────────────────────────────
MODEL_CREDITS: dict = {
    "gen4.5":      12,   # 2.4 cr/s — hero quality
    "gen4_turbo":  10,   # 2.0 cr/s — balanced
}

# ── Trigger-word banks ────────────────────────────────────────────────────────
_HIGH_TRIGGERS = {
    "reveal", "secret", "shock", "shocking", "discover", "discovered",
    "transform", "transformation", "hack", "confess", "confession",
    "finally", "truth", "never told", "nobody knows", "life-changing",
    "change everything", "changed everything", "hidden", "banned",
    "exposed", "unbelievable", "insane", "incredible", "mindblowing",
    "wake up", "pay attention", "game changer", "gamechanger",
}

_MEDIUM_TRIGGERS = {
    "strategy", "workflow", "system", "step", "steps", "method",
    "framework", "process", "proven", "powerful", "effective",
    "tool", "tools", "app", "automate", "automation", "build",
    "boost", "increase", "triple", "double", "grow", "scale",
    "faster", "smarter", "better", "improve", "upgrade",
}


@dataclass
class SceneScore:
    score: int                   # 1–10
    reasoning: str
    use_runway: bool
    recommended_model: str       # "gen4.5" | "gen4_turbo" | "stock"
    credits_per_5s: int          # 0 for stock
    visual_prompt: str = ""


def select_runway_model(
    scene_type: str,
    visual_score: int,
    budget_remaining: float,
) -> Tuple[str | None, int]:
    """
    Return (model_name, credits_per_5s).
    Returns (None, 0) when stock footage should be used.

    Strategy:
      hook              → always gen4.5 (first impression is everything)
      score ≥ 8         → gen4.5  (12 cr/5s)
      score 5–7         → gen4_turbo  (10 cr/5s)
      score < 5         → stock footage (0 credits)

    Budget guardrail: if remaining credits cannot cover the cheapest model,
    fall back to stock regardless of score.
    """
    cheapest = min(MODEL_CREDITS.values())

    if scene_type == "hook":
        model, rate = "gen4.5", MODEL_CREDITS["gen4.5"]
    elif visual_score >= 8:
        model, rate = "gen4.5", MODEL_CREDITS["gen4.5"]
    elif visual_score >= 5:
        model, rate = "gen4_turbo", MODEL_CREDITS["gen4_turbo"]
    else:
        return None, 0

    # Budget guardrail
    if budget_remaining < cheapest:
        return None, 0
    if budget_remaining < rate:
        # Downgrade to cheaper model
        model, rate = "gen4_turbo", MODEL_CREDITS["gen4_turbo"]
        if budget_remaining < rate:
            return None, 0

    return model, rate


def score_scene_heuristic(
    scene_text: str,
    scene_type: str,
    scene_index: int = 0,
) -> SceneScore:
    """
    Fast keyword/position-based visual importance scoring.
    No API calls — safe to run in every request.
    """
    text_lower = (scene_text or "").lower()

    # ── Position score ──────────────────────────────────────────────────────
    if scene_type == "hook" or scene_index == 0:
        position_score = 10         # Hook is always 10
    elif scene_type == "cta":
        position_score = 7          # CTA matters for retention
    else:
        position_score = 5          # Body default

    # ── Trigger-word score ──────────────────────────────────────────────────
    tokens = set(re.findall(r"[a-z']+", text_lower))
    high_hits = sum(1 for t in _HIGH_TRIGGERS if t in text_lower)
    medium_hits = sum(1 for t in _MEDIUM_TRIGGERS if any(tt in tokens for tt in t.split()))

    trigger_bonus = min(3, high_hits * 2 + medium_hits)

    # ── Length score (longer scene = more visual need) ──────────────────────
    word_count = len(text_lower.split())
    length_bonus = 1 if word_count > 20 else 0

    # ── Final score (capped 1–10) ────────────────────────────────────────────
    raw = position_score + trigger_bonus + length_bonus
    score = max(1, min(10, raw))

    # ── Build reasoning ──────────────────────────────────────────────────────
    reasons = []
    if scene_type == "hook" or scene_index == 0:
        reasons.append("hook scene")
    if high_hits:
        reasons.append(f"{high_hits} high-impact trigger word(s)")
    if medium_hits:
        reasons.append(f"{medium_hits} medium trigger word(s)")
    reasoning = ", ".join(reasons) if reasons else "standard body scene"

    # ── Model selection ──────────────────────────────────────────────────────
    if score >= 8:
        model = "gen4.5"
    elif score >= 5:
        model = "gen4_turbo"
    else:
        model = "stock"

    use_runway = model != "stock"
    credits = MODEL_CREDITS.get(model, 0)

    # ── Visual prompt enhancement ─────────────────────────────────────────────
    vp = _build_visual_prompt(scene_text, scene_type, score)

    return SceneScore(
        score=score,
        reasoning=reasoning,
        use_runway=use_runway,
        recommended_model=model,
        credits_per_5s=credits,
        visual_prompt=vp,
    )


# ── Optional Claude-powered scoring (gated behind env flag) ────────────────
async def score_scene_visual_importance(
    scene_text: str,
    scene_type: str,
    full_script: str = "",
    scene_index: int = 0,
) -> SceneScore:
    """
    Entry point for visual scoring.
    - ENABLE_VISUAL_AI_SCORING=true → calls Claude (uses API credits)
    - Default → fast heuristic (zero cost)
    """
    if os.getenv("ENABLE_VISUAL_AI_SCORING", "").lower() == "true":
        return await _score_with_claude(scene_text, scene_type, full_script, scene_index)
    return score_scene_heuristic(scene_text, scene_type, scene_index)


async def _score_with_claude(
    scene_text: str,
    scene_type: str,
    full_script: str,
    scene_index: int,
) -> SceneScore:
    """Claude-powered scoring — only runs when ENABLE_VISUAL_AI_SCORING=true."""
    import json
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""You are a viral video producer. Rate the visual importance of this scene (1-10).

SCENE TYPE: {scene_type}
SCENE INDEX: {scene_index}
SCENE TEXT: "{scene_text}"
FULL SCRIPT (first 400 chars): "{(full_script or '')[:400]}"

Scale:
10 = Hook / dramatic reveal / transformation moment
8-9 = Emotional peak / high-impact moment
5-7 = Supporting body scene
3-4 = Narration-heavy, stock footage works
1-2 = Stats / text-focused

Output ONLY valid JSON:
{{"score": 8, "reasoning": "...", "use_runway": true, "recommended_model": "gen4.5"}}"""

    try:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        data = json.loads(raw)
        score = int(data.get("score", 5))
        model = data.get("recommended_model", "gen4_turbo")
        if model not in MODEL_CREDITS:
            model = "gen4_turbo"
        return SceneScore(
            score=score,
            reasoning=data.get("reasoning", ""),
            use_runway=bool(data.get("use_runway", score >= 5)),
            recommended_model=model,
            credits_per_5s=MODEL_CREDITS.get(model, 0),
            visual_prompt=_build_visual_prompt(scene_text, scene_type, score),
        )
    except Exception as exc:
        print(f"[VISUAL_SCORE] Claude call failed, using heuristic: {exc}")
        return score_scene_heuristic(scene_text, scene_type, scene_index)


def _build_visual_prompt(text: str, scene_type: str, score: int) -> str:
    """Convert script text into a Runway-ready visual prompt."""
    text = (text or "").strip()
    style_prefix = {
        "hook": "Ultra-dramatic cinematic opening, extreme close-up",
        "cta":  "Satisfying success moment, clean composition",
        "body": "Documentary-style explanatory visual",
    }.get(scene_type, "Cinematic")

    quality = "4K, sharp focus, professional lighting" if score >= 8 else "clean composition, natural lighting"
    return f"{style_prefix} — {text[:80].rstrip('.')}. Vertical 9:16, {quality}, no text."
