"""Pure scene asset strategy planning for Hybrid Motion Renderer.

This module intentionally keeps a small, dependency-free slice of the legacy
MoviePy/stock pipeline's domain and query intelligence. It does not import
``video_pipeline.py`` because that module pulls MoviePy and paid-provider
branches at import time.
"""

from __future__ import annotations

import re
from typing import Any


VISUAL_MEDIUMS = {
    "stock_footage",
    "stock_image",
    "playwright_capture",
    "local_asset",
    "motion_template",
}

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "for",
    "from",
    "in",
    "into",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "with",
    "you",
    "your",
}

_VISUAL_KEYWORD_MAP: dict[str, str] = {
    "ai": "AI chat screen laptop",
    "bill": "bill statement payment close up",
    "budget": "budget calculator receipt",
    "cart": "grocery cart supermarket aisle",
    "checkout": "grocery checkout receipt",
    "coffee": "coffee cup cafe counter",
    "comparison": "before after comparison screen",
    "dollar": "cash receipt payment close up",
    "expense": "expenses receipt calculator",
    "expenses": "expenses receipt calculator",
    "grocery": "grocery shopping cart supermarket",
    "groceries": "grocery shopping cart supermarket",
    "inflation": "grocery prices supermarket receipt",
    "leak": "money leak receipt spending",
    "phone": "smartphone hand app close up",
    "prompt": "AI chat prompt laptop screen",
    "receipt": "grocery receipt close up",
    "saving": "savings money receipt phone",
    "savings": "savings money receipt phone",
    "scan": "phone scanning receipt",
    "scanned": "phone scanning receipt",
    "swap": "grocery brand comparison",
    "swaps": "grocery brand comparison",
}

_DOMAIN_PACKS: dict[str, dict[str, object]] = {
    "grocery_savings": {
        "keyword_triggers": [
            "grocery",
            "groceries",
            "receipt",
            "cart",
            "supermarket",
            "inflation",
            "brand swap",
            "brand swaps",
            "checkout extras",
        ],
        "preferred_hook_visual_query_seeds": [
            "grocery receipt close up supermarket checkout",
            "person holding grocery receipt shopping bag",
            "grocery cart receipt phone close up",
        ],
        "proof_visual_query_seeds": [
            "phone scanning grocery receipt close up",
            "grocery receipt on kitchen counter phone",
            "supermarket receipt prices close up",
        ],
        "cta_visual_query_seeds": [
            "person typing comment on phone close up",
            "grocery shopping phone app close up",
        ],
        "fallback_stock_query_seeds": [
            "grocery cart supermarket aisle vertical",
            "grocery bag receipt kitchen counter",
        ],
    },
    "coffee_savings": {
        "keyword_triggers": ["coffee", "cafe", "latte", "espresso", "home brew"],
        "preferred_hook_visual_query_seeds": [
            "person holding coffee receipt cafe counter",
            "coffee cup payment receipt close up",
            "person reacting to coffee shop receipt",
        ],
        "proof_visual_query_seeds": [
            "home coffee brewing kitchen vertical",
            "coffee cup receipt calculator close up",
        ],
        "cta_visual_query_seeds": [
            "person typing comment on phone cafe",
            "creator holding coffee phone vertical",
        ],
        "fallback_stock_query_seeds": [
            "coffee cup cafe counter vertical",
            "home coffee kitchen vertical",
        ],
    },
    "generic_money_problem": {
        "keyword_triggers": ["save money", "saving money", "overpay", "bill", "bills", "monthly cost", "wasting money", "expenses"],
        "preferred_hook_visual_query_seeds": [
            "person shocked at bill statement",
            "person reviewing expenses on phone",
            "frustrated person looking at payment amount",
        ],
        "proof_visual_query_seeds": [
            "receipt calculator expenses close up",
            "phone banking app savings close up",
        ],
        "cta_visual_query_seeds": [
            "person typing comment on phone close up",
            "creator posting short video on phone",
        ],
        "fallback_stock_query_seeds": [
            "monthly bill close up payment screen",
            "person reacting to expensive invoice",
        ],
    },
    "creator_tools": {
        "keyword_triggers": ["prompt", "chatgpt", "ai tool", "ai tools", "creator", "script", "write me"],
        "preferred_hook_visual_query_seeds": [
            "creator reacting to AI workflow laptop",
            "person comparing AI results on screen",
        ],
        "proof_visual_query_seeds": [
            "AI chat prompt laptop screen close up",
            "computer screen AI response typing",
        ],
        "cta_visual_query_seeds": [
            "creator posting short video on phone",
            "person tapping follow button on phone screen",
        ],
        "fallback_stock_query_seeds": [
            "AI chat laptop screen",
            "creator working on laptop screen",
        ],
    },
}

_TEMPLATE_MEDIUM_HINTS = {
    "ai_prompt_mock": "playwright_capture",
    "grocery_ai_comparison": "playwright_capture",
    "comparison_split": "playwright_capture",
    "grocery_receipt_hook": "stock_footage",
    "grocery_reveal_scene": "stock_footage",
    "grocery_savings_payoff": "playwright_capture",
    "hook_footage_overlay": "stock_footage",
    "cta_callback": "stock_footage",
}

_PLAYWRIGHT_HINTS = {
    "ai_prompt_mock": "ai_chat_typing",
    "grocery_ai_comparison": "receipt_audit_comparison",
    "grocery_savings_payoff": "savings_dashboard",
    "comparison_split": "comparison_panel",
}


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _scene_value(scene: Any, key: str, default: Any = None) -> Any:
    if isinstance(scene, dict):
        return scene.get(key, default)
    return getattr(scene, key, default)


def _scene_id(scene: Any, idx: int) -> Any:
    return _scene_value(scene, "id", None) or _scene_value(scene, "scene", None) or _scene_value(scene, "scene_index", idx + 1)


def _scene_template(scene: Any) -> str:
    return _clean_text(_scene_value(scene, "template", "") or _scene_value(scene, "hybrid_template", ""))


def _scene_blob(scene: Any) -> str:
    parts = [
        _scene_value(scene, "id", ""),
        _scene_value(scene, "template", ""),
        _scene_value(scene, "part", ""),
        _scene_value(scene, "scene_type", ""),
        _scene_value(scene, "headline", ""),
        _scene_value(scene, "caption_text", ""),
        _scene_value(scene, "narration_text", ""),
        _scene_value(scene, "visual_description", ""),
        _scene_value(scene, "description", ""),
        _scene_value(scene, "prompt", ""),
        _scene_value(scene, "response", ""),
        _scene_value(scene, "subline", ""),
    ]
    return _clean_text(" ".join(str(part or "") for part in parts)).lower()


def _detect_domain(blob: str) -> str:
    best_domain = ""
    best_score = 0
    for domain, pack in _DOMAIN_PACKS.items():
        triggers = [str(trigger).lower() for trigger in pack.get("keyword_triggers", [])]
        score = sum(1 for trigger in triggers if trigger and trigger in blob)
        if score > best_score:
            best_domain = domain
            best_score = score
    if not best_domain and any(token in blob for token in ("ai", "prompt", "chatgpt")):
        return "creator_tools"
    return best_domain


def _scene_stage(scene: Any, idx: int, blob: str) -> str:
    raw = " ".join(
        str(_scene_value(scene, key, "") or "").lower()
        for key in ("id", "part", "scene_type", "template")
    )
    if idx == 0 or "hook" in raw:
        return "hook"
    if "cta" in raw or "comment" in blob:
        return "cta"
    if any(token in blob for token in ("ai", "prompt", "scan", "compare", "comparison", "swap")):
        return "proof"
    if any(token in blob for token in ("payoff", "saving", "savings", "yearly", "year")):
        return "payoff"
    return "context"


def _meaningful_words(blob: str, limit: int = 4) -> list[str]:
    words = []
    for word in re.findall(r"[a-zA-Z][a-zA-Z']+", blob.lower()):
        if len(word) < 3 or word in _STOPWORDS:
            continue
        phrase = _VISUAL_KEYWORD_MAP.get(word, word)
        if phrase not in words:
            words.append(phrase)
        if len(words) >= limit:
            break
    return words


def _pack_queries(domain: str, stage: str) -> list[str]:
    pack = _DOMAIN_PACKS.get(domain, {})
    if stage == "hook":
        return [str(query) for query in pack.get("preferred_hook_visual_query_seeds", [])]
    if stage == "cta":
        return [str(query) for query in pack.get("cta_visual_query_seeds", [])]
    if stage in {"proof", "payoff"}:
        return [str(query) for query in pack.get("proof_visual_query_seeds", [])]
    return [str(query) for query in pack.get("fallback_stock_query_seeds", [])]


def _query_candidates(scene: Any, idx: int, domain: str, stage: str, blob: str) -> list[str]:
    candidates = list(_pack_queries(domain, stage))
    context = _meaningful_words(blob)
    if context:
        context_phrase = " ".join(context[:3])
        if stage == "hook":
            candidates.append(f"person reacting to {context_phrase} close up vertical")
        elif stage == "cta":
            candidates.append(f"person typing comment about {context_phrase} on phone")
        elif stage in {"proof", "payoff"}:
            candidates.append(f"{context_phrase} phone screen close up")
        else:
            candidates.append(f"{context_phrase} vertical")

    visual_description = _clean_text(_scene_value(scene, "visual_description", ""))
    if visual_description:
        candidates.append(visual_description)

    template = _scene_template(scene)
    if template == "grocery_ai_comparison":
        candidates.append("phone scanning grocery receipt AI comparison")
    elif template == "grocery_savings_payoff":
        candidates.append("phone savings estimate grocery receipt")
    elif template == "cta_callback":
        candidates.append("person typing comment on phone close up")

    deduped: list[str] = []
    for query in candidates:
        cleaned = _clean_text(query)
        if cleaned and cleaned not in deduped:
            deduped.append(cleaned)
    return deduped[:5]


def _visual_medium(scene: Any, stage: str, blob: str) -> str:
    template = _scene_template(scene)
    hinted = _TEMPLATE_MEDIUM_HINTS.get(template)
    if hinted:
        return hinted
    if any(token in blob for token in ("ai", "prompt", "dashboard", "spreadsheet", "screen capture")):
        return "playwright_capture"
    if stage in {"hook", "context", "cta"}:
        return "stock_footage"
    if stage == "payoff":
        return "stock_image"
    return "motion_template"


def _asset_role(stage: str, medium: str) -> str:
    if stage == "hook":
        return "thumb_stop_real_world_context"
    if stage == "proof" and medium == "playwright_capture":
        return "screen_proof_or_ai_comparison"
    if stage == "payoff":
        return "savings_payoff_visual"
    if stage == "cta":
        return "comment_action_visual"
    return "story_context_visual"


def _fallback_order(medium: str) -> list[str]:
    if medium == "playwright_capture":
        return ["playwright_capture", "local_asset", "stock_image", "motion_template"]
    if medium == "stock_footage":
        return ["stock_footage", "stock_image", "local_asset", "motion_template"]
    if medium == "stock_image":
        return ["stock_image", "stock_footage", "local_asset", "motion_template"]
    if medium == "local_asset":
        return ["local_asset", "stock_image", "motion_template"]
    return ["motion_template"]


def plan_hmr_scene_assets(scenes: list[dict]) -> list[dict]:
    """Return deterministic HMR asset strategy rows for scene dictionaries.

    The planner is pure and performs no network, filesystem, or provider calls.
    """
    plans: list[dict] = []
    for idx, scene in enumerate(scenes or []):
        blob = _scene_blob(scene)
        stage = _scene_stage(scene, idx, blob)
        domain = _detect_domain(blob)
        medium = _visual_medium(scene, stage, blob)
        template = _scene_template(scene)
        capture_hint = _PLAYWRIGHT_HINTS.get(template) if medium == "playwright_capture" else None
        query_candidates = _query_candidates(scene, idx, domain, stage, blob)
        plans.append(
            {
                "scene_id": _scene_id(scene, idx),
                "visual_medium": medium if medium in VISUAL_MEDIUMS else "motion_template",
                "asset_role": _asset_role(stage, medium),
                "query_candidates": query_candidates,
                "template_hint": template or None,
                "capture_hint": capture_hint,
                "fallback_order": _fallback_order(medium),
                "reason": (
                    f"{stage} scene mapped to {medium}"
                    + (f" using {domain} domain pack" if domain else " using visual keyword fallback")
                ),
            }
        )
    return plans
