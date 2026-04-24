
import os
import re
import uuid
import asyncio
import math
import hashlib
import shutil
import time as _time_mod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Tuple

import httpx
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
from dotenv import load_dotenv

try:
    from PIL import Image
    if not hasattr(Image, "ANTIALIAS") and hasattr(Image, "Resampling"):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
except Exception:
    pass

# --- AI video import ---
from .ai_video import fetch_runwayml_clip
from .runwayml_client import RunwayMLQuotaError


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
ASSETS_DIR = BASE_DIR / "generated_videos"
RAW_DIR = ASSETS_DIR / "raw"
TEMP_DIR = ASSETS_DIR / "temp"
CACHE_DIR = ASSETS_DIR / "cache"

FAST_TARGET_W = int(os.getenv("VIDEO_TARGET_W", "1080"))
FAST_TARGET_H = int(os.getenv("VIDEO_TARGET_H", "1920"))
FAST_DISABLE_EFFECTS = os.getenv("VIDEO_DISABLE_EFFECTS", "0") == "1"

STOPWORDS = {
    "this", "that", "with", "from", "your", "have", "will", "just", "into", "when", "what",
    "where", "about", "more", "than", "then", "they", "them", "their", "were", "while", "only",
    "and", "for", "the", "are", "you", "our", "out", "can", "how", "why", "has", "had",
    "get", "got", "its", "it", "his", "her", "she", "him", "who", "which", "also", "very",
    # Common script filler that makes poor stock-search keywords
    "every", "each", "some", "most", "many", "much", "such", "both", "even", "same",
    "here", "there", "over", "under", "make", "made", "take", "need", "want", "know",
    "call", "like", "look", "tell", "give", "come", "think", "back", "down", "year",
    "visual", "scene", "video", "content", "watch", "find", "follow", "next", "last",
}

_PLANNING_TEXT_MARKERS = (
    "showing",
    "animation",
    "montage",
    "screen recording",
    "text appears",
)


def looks_like_planning_text(text: str) -> bool:
    sample = _clean_text(text).lower()
    if not sample:
        return False
    return any(marker in sample for marker in _PLANNING_TEXT_MARKERS)

# Maps common script words → stock-footage search phrases.
# When a raw keyword matches, its phrase replaces it in the search query,
# giving Pexels / Pixabay far better context than the literal script word.
_VISUAL_KEYWORD_MAP: dict = {
    # ── Finance ────────────────────────────────────────────────────────────
    "money":        "cash money wallet dollar",
    "saving":       "savings piggy bank coins",
    "savings":      "savings coins bank jar",
    "save":         "savings bank coins",
    "spend":        "shopping payment checkout",
    "spending":     "shopping credit card payment",
    "waste":        "money trash overspending",
    "wasting":      "money waste overspending",
    "budget":       "budget finance calculator expenses",
    "finance":      "finance wallet money planning",
    "financial":    "financial planning documents",
    "invest":       "investment growth chart profit",
    "investing":    "investment stock market growth",
    "wealth":       "luxury wealth success affluent",
    "rich":         "luxury lifestyle wealthy success",
    "income":       "salary income money earning",
    "salary":       "office professional paycheck salary",
    "debt":         "credit card bills debt papers",
    "bank":         "bank finance money vault",
    "credit":       "credit card payment checkout",
    "dollar":       "dollar bills cash money pile",
    "dollars":      "dollar bills cash money",
    "thousand":     "cash bills money stack",
    "bills":        "bills invoice money payment",
    "payment":      "payment card checkout transaction",
    "subscription": "phone app subscription service",
    "subscriptions":"phone apps payment monthly",
    "tax":          "tax documents paperwork calculator",
    "taxes":        "tax documents filing calculator",
    "profit":       "profit growth chart success",
    "expense":      "expenses receipt calculator finance",
    "expenses":     "expenses receipt finance budget",
    # ── Action / hook ──────────────────────────────────────────────────────
    "hack":         "productivity life hack solution",
    "hacks":        "life hacks tips solution",
    "simple":       "simple steps clean minimal",
    "stop":         "stop pause decision moment",
    "discover":     "discovery reveal insight moment",
    "secret":       "secret hidden reveal dramatic",
    "mistake":      "mistake failure problem stress",
    "mistakes":     "mistakes wrong problem failure",
    "change":       "transformation change success journey",
    "transform":    "transformation before after progress",
    "improve":      "improvement growth progress upward",
    "never":        "dramatic warning person",
    "reveal":       "dramatic reveal cinematic",
    "trick":        "tips tricks solution idea",
    "tricks":       "tips tricks smart idea",
    "strategy":     "strategy planning whiteboard charts",
    "system":       "system process workflow organised",
    "method":       "method process steps explained",
    # ── Productivity / work ────────────────────────────────────────────────
    "work":         "office desk laptop working",
    "working":      "person working computer desk",
    "productivity": "desk workspace focused laptop",
    "productive":   "focused work desk minimal",
    "workflow":     "workflow computer office professional",
    "business":     "business professional office meeting",
    "time":         "clock time management calendar",
    "schedule":     "calendar planning schedule agenda",
    "focus":        "focus concentration study person",
    "goal":         "goal achievement success writing",
    "goals":        "goal writing planning achievement",
    "plan":         "planning notebook calendar strategy",
    "habit":        "habit routine morning person",
    "habits":       "habits routine daily person",
    "morning":      "morning routine sunrise person",
    # ── Tech / AI ──────────────────────────────────────────────────────────
    "tool":         "computer software digital tool",
    "tools":        "digital tools software computer",
    "automate":     "automation computer technology",
    "automation":   "automation robot computer technology",
    "software":     "software coding computer screen",
    "phone":        "smartphone phone person using",
    "laptop":       "laptop computer workspace desk",
    "digital":      "digital product online store creator",
    "product":      "digital product mockup ecommerce",
    "products":     "digital products online storefront",
    "prompt":       "chatgpt prompt writing laptop",
    "prompts":      "digital prompt product storefront",
    "explainer":    "video editing timeline laptop",
    "editing":      "video editing timeline screen",
    "editor":       "video editor computer workstation",
    "timeline":     "editing timeline video software",
    "newsletter":   "newsletter dashboard subscriber growth",
    "subscriber":   "subscriber growth analytics dashboard",
    "subscribers":  "subscriber count growth analytics",
    "sponsor":      "brand partnership marketing meeting",
    "sponsors":     "creator sponsorship deal laptop",
    "sponsorship":  "brand sponsorship marketing workspace",
    "growth":       "growth chart analytics dashboard",
    "analytics":    "analytics dashboard metrics growth",
    "dashboard":    "dashboard metrics screen analytics",
    # ── Health / lifestyle ─────────────────────────────────────────────────
    "health":       "healthy lifestyle wellness person",
    "fitness":      "gym workout exercise fitness",
    "food":         "healthy food meal cooking",
    "people":       "people crowd lifestyle urban",
    "year":         "calendar year planning journal",
    "life":         "lifestyle person living city",
}

# ── Hook-specific query templates (Batch 2A) ────────────────────────────────
# For hook scenes: prioritize high-impact, emotional visuals that stop scrolling
_HOOK_QUERY_TEMPLATES = [
    "frustrated person laptop stressed work",
    "shocked surprised person reaction close up",
    "person overwhelmed bills money stress",
    "fast typing computer deadline pressure",
]

_HOOK_FILLER_WORDS = {
    "A", "AN", "THE", "THAT", "THIS", "THESE", "THOSE", "REALLY", "VERY", "JUST",
    "ACTUALLY", "LITERALLY", "SIMPLY", "BASICALLY", "KIND", "SORT", "RIGHT", "NOW",
    "WATCHING", "WATCH", "USING", "USE", "WAYS", "WAY", "METHOD", "METHODS",
    "IDEA", "IDEAS", "TUTORIAL", "TUTORIALS"  # removed only when tension phrase already carries topic
}
_HOOK_ACTION_WORDS = {
    "SELL", "BUILD", "CREATE", "START", "EDIT", "GROW", "MAKE", "LAUNCH", "WRITE",
    "UPLOAD", "DESIGN", "MONETIZE", "EARN", "MARKET", "SCALE",
}
_HOOK_RESULT_WORDS = {
    "RESULTS", "RESULT", "GROWTH", "REVENUE", "SALES", "SUBSCRIBERS", "METRICS",
    "DASHBOARD", "PROFIT", "MONEY", "EARNED", "EARNING", "INCOME",
}
_HOOK_CONTROL_WORDS = {
    "STOP", "DON'T", "WRONG", "MISTAKE", "FAIL", "FAILS", "MOST", "PEOPLE",
    "YOU'RE", "DOING", "YOUR", "WHY", "START",
}
_HOOK_OBJECT_FALLBACKS = {
    "digital_products": "digital product storefront",
    "prompt_products": "prompt product laptop",
    "explainer_videos": "video timeline editor",
    "small_business": "small business owner",
    "email_list": "email marketing dashboard",
    "sponsors": "sponsorship deal laptop",
    "growth_analytics": "analytics dashboard growth",
}

for d in (ASSETS_DIR, RAW_DIR, TEMP_DIR, CACHE_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── In-memory search-result cache (1-hour TTL) ────────────────────────────
# Keyed by query string; value is (expires_timestamp, download_url_or_None)
_pexels_search_cache: dict[str, tuple[float, str | None]] = {}
_pixabay_search_cache: dict[str, tuple[float, str | None]] = {}
_SEARCH_CACHE_TTL = 3600.0  # seconds


@dataclass
class ScriptParts:
    hook: str
    body: str
    cta: str


@dataclass
class ScenePlan:
    idx: int
    start: float
    end: float
    part: str
    source_text: str
    subtitle: str
    visual_description: str
    keywords: List[str]
    energy: str
    clip_url: Optional[str] = None
    clip_path: Optional[str] = None
    use_runway: bool = False
    credits_cost: float = 0.0
    allocation_reason: str = ""
    visual_score: int = 5           # 1-10 from visual_scoring.py
    runway_model: Optional[str] = None  # per-scene model override


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _timestamp_to_seconds(value: str) -> Optional[float]:
    raw = _clean_text(value)
    if not raw:
        return None
    parts = raw.split(":")
    try:
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return float(minutes * 60 + seconds)
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return float(hours * 3600 + minutes * 60 + seconds)
    except Exception:
        return None
    return None


def _extract_clip_url(text: str) -> Optional[str]:
    match = re.search(r"https?://\S+", text or "", re.I)
    if not match:
        return None
    return match.group(0).rstrip(").,;!?")


def _normalize_source_url(url: str) -> str:
    cleaned = _clean_text(url)
    pexels_match = re.search(r"pexels\.com/video/[^/]*-(\d+)", cleaned, re.I)
    if pexels_match:
        return f"https://www.pexels.com/video/{pexels_match.group(1)}/download/"
    return cleaned


def _subtitle_from_description(description: str) -> str:
    quoted = re.findall(r'"([^"\n]{2,})"', description or "")
    if quoted:
        joined = " → ".join([_clean_text(q) for q in quoted[:2]])
        return joined[:180]

    compact = _clean_text(re.sub(r"https?://\S+", "", description or ""))
    if len(compact) <= 180:
        return compact
    return compact[:177].rstrip() + "..."


def parse_clip_to_clip_structure(raw_script: str) -> List[ScenePlan]:
    text = (raw_script or "").strip()
    if not text:
        return []

    header_pattern = re.compile(
        r"^\s*Clip\s*(\d+)\s*[·\-–]\s*([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?)\s*[\-–]\s*([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?)\s*(?:\(([^)]*)\))?\s*$",
        re.I | re.M,
    )
    matches = list(header_pattern.finditer(text))
    if len(matches) < 2:
        return []

    scenes: List[ScenePlan] = []
    for i, match in enumerate(matches):
        idx = int(match.group(1))
        start_s = _timestamp_to_seconds(match.group(2))
        end_s = _timestamp_to_seconds(match.group(3))
        if start_s is None or end_s is None or end_s <= start_s:
            continue

        block_start = match.end()
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = _clean_text(text[block_start:block_end])

        part = "body"
        if i == 0:
            part = "hook"
        elif i == len(matches) - 1:
            part = "cta"

        subtitle = _subtitle_from_description(block)
        source_url = _extract_clip_url(block or "")
        visual = _clean_text(re.sub(r"https?://\S+", "", block or ""))
        if not visual:
            visual = "stock b-roll matching the scene context"

        scenes.append(
            ScenePlan(
                idx=idx,
                start=round(start_s, 2),
                end=round(end_s, 2),
                part=part,
                source_text=subtitle,
                subtitle=subtitle,
                visual_description=visual,
                keywords=_extract_keywords(visual, ["stadium", "crowd", "sports", "highlight"]),
                energy="urgency" if part == "hook" else ("confidence" if part == "cta" else "curiosity"),
                clip_url=_normalize_source_url(source_url) if source_url else None,
            )
        )

    scenes.sort(key=lambda item: (item.start, item.idx))
    return scenes


def scenes_from_rows(rows: List[Dict]) -> List[ScenePlan]:
    if not isinstance(rows, list):
        return []

    parsed: List[ScenePlan] = []
    for i, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        try:
            start = float(row.get("start", 0))
            end = float(row.get("end", 0))
        except Exception:
            continue
        if end <= start:
            continue

        # Guardrail: subtitle must represent spoken/narration text.
        # Never fall back to on_screen_text, which is display-only.
        #
        # Some legacy/alternate scene schemas (e.g. image-first) store spoken text as
        # `caption_text`/`description`. Accept those as subtitle sources, but still
        # never use `on_screen_text` as a subtitle fallback.
        caption_text_fallback = _clean_text(row.get("caption_text") or "")
        if caption_text_fallback and looks_like_planning_text(caption_text_fallback):
            print(
                f"[SCENE_TEXT_CHECK] scene={row.get('scene') or row.get('idx') or i} "
                "caption_text_rejected_as_planning=true"
            )
            caption_text_fallback = ""
        subtitle = _clean_text(
            row.get("subtitle")
            or row.get("source_text")
            or caption_text_fallback
            or ""
        )
        on_screen_text = _clean_text(row.get("on_screen_text") or subtitle)
        visual = _clean_text(row.get("visual_description") or subtitle or "stock b-roll matching scene")
        keywords = row.get("keywords") if isinstance(row.get("keywords"), list) else _extract_keywords(visual, ["sports", "stadium"])
        part = _clean_text(row.get("part") or "body").lower() or "body"
        clip_url = row.get("clip_url") or row.get("source_url")

        scene_obj = ScenePlan(
            idx=int(row.get("scene") or row.get("idx") or i),
            start=round(start, 2),
            end=round(end, 2),
            part=part if part in {"hook", "body", "cta"} else "body",
            source_text=subtitle,
            subtitle=subtitle,
            visual_description=visual,
            keywords=[str(k) for k in keywords][:6],
            energy=_clean_text(row.get("energy") or ("confidence" if part == "cta" else ("urgency" if part == "hook" else "curiosity"))),
            clip_url=_normalize_source_url(str(clip_url)) if clip_url else None,
        )
        # Sidecar field for display-only text.
        setattr(scene_obj, "on_screen_text", on_screen_text)
        # Verification log: ensure narration (subtitle) is not contaminated by planning (visual_description).
        sub_preview = (subtitle or "")[:220].replace('"', '\\"')
        on_screen_preview = (on_screen_text or "")[:220].replace('"', '\\"')
        vis_preview = (visual or "")[:260].replace('"', '\\"')
        print(
            f"[SCENE_TEXT_CHECK] scene={scene_obj.idx} "
            f"subtitle=\"{sub_preview}\" "
            f"on_screen_text=\"{on_screen_preview}\" "
            f"visual_description=\"{vis_preview}\""
        )

        parsed.append(scene_obj)

    parsed.sort(key=lambda item: (item.start, item.idx))

    # Role propagation fix: assign role_label deterministically for caption/retention layers.
    # hook -> hook, cta -> cta
    # body beats: 1 => payoff_2, 2 => payoff_1/payoff_3, else first/middle/last
    body_indices = [i for i, s in enumerate(parsed) if (s.part or "") == "body"]
    n = len(body_indices)
    body_roles: list[str] = []
    if n == 1:
        body_roles = ["payoff_2"]
    elif n == 2:
        body_roles = ["payoff_1", "payoff_3"]
    elif n > 2:
        body_roles = ["payoff_1"] + ["payoff_2"] * (n - 2) + ["payoff_3"]

    bi = 0
    for s in parsed:
        role = "hook" if s.part == "hook" else "cta" if s.part == "cta" else ""
        if s.part == "body" and bi < len(body_roles):
            role = body_roles[bi]
            bi += 1
        setattr(s, "role_label", role or "payoff_2")
        try:
            d = float(s.end) - float(s.start)
        except Exception:
            d = 0.0
        print(f"[RETENTION] scene={s.idx} role={getattr(s, 'role_label', '')} start={s.start:.2f} end={s.end:.2f} duration={d:.2f}")

    return parsed


def parse_script(full_script: str, hook: Optional[str] = None, body: Optional[str] = None, cta: Optional[str] = None) -> ScriptParts:
    if hook and body and cta:
        return ScriptParts(_clean_text(hook), _clean_text(body), _clean_text(cta))

    script = (full_script or "").strip()
    marker = re.search(r"\[HOOK\](.*?)\[BODY\](.*?)\[CTA\](.*)", script, re.S | re.I)
    if marker:
        return ScriptParts(
            hook=_clean_text(marker.group(1)),
            body=_clean_text(marker.group(2)),
            cta=_clean_text(marker.group(3)),
        )

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
    if len(sentences) <= 2:
        return ScriptParts(
            hook=_clean_text(sentences[0] if sentences else script),
            body=_clean_text(" ".join(sentences[1:]) if len(sentences) > 1 else ""),
            cta=_clean_text(cta or "Follow for more."),
        )

    return ScriptParts(
        hook=_clean_text(sentences[0]),
        body=_clean_text(" ".join(sentences[1:-1])),
        cta=_clean_text(sentences[-1]),
    )


def _extract_keywords(text: str, fallback: List[str]) -> List[str]:
    tokens = re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
    unique = []
    for token in tokens:
        if token in STOPWORDS:
            continue
        if token not in unique:
            unique.append(token)
    return (unique[:5] or fallback)


def _semantic_tokens(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
        if t not in STOPWORDS
    }


def _extract_meaningful_words(text: str, max_words: int = 5) -> List[str]:
    """Extract meaningful keywords from text (skip stopwords) - Batch 2A"""
    if not text:
        return []
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return [w for w in words if w not in STOPWORDS][:max_words]


def _classify_hook_pattern(text: str) -> str:
    raw = _clean_text(text).lower()
    if not raw:
        return "generic"

    if re.search(r"\b(stop|don't|dont|avoid|never|before you)\b", raw):
        return "warning"
    if re.search(r"\b(mistake|mistakes|wasting|waste|killing|ruining|fail|fails)\b", raw):
        return "mistake"
    if re.search(r"\b(\d+|method|methods|ways|tips|steps)\b", raw):
        return "list"
    if re.search(r"\b(most people|everyone thinks|you think|wrong)\b", raw):
        return "myth"
    if re.search(r"\b(instead|vs|versus|rather than|actually|not this)\b", raw):
        return "contrast"
    return "generic"


def _hook_tokens_upper(text: str) -> List[str]:
    return re.findall(r"[A-Z0-9']+", (text or "").upper())


def _extract_hook_objects(text: str, max_words: int = 3) -> List[str]:
    tokens = _hook_tokens_upper(text)
    objects: List[str] = []
    for token in tokens:
        if token in _HOOK_FILLER_WORDS or token in _HOOK_CONTROL_WORDS:
            continue
        if token not in objects:
            objects.append(token)
        if len(objects) >= max_words:
            break
    return objects


def _preferred_paid_ai_hook(hook: str) -> Optional[str]:
    """Deterministic broad-audience hook treatment for free-vs-paid AI/tool scripts."""
    tokens = set(_hook_tokens_upper(hook))
    if not tokens:
        return None

    has_ai = "AI" in tokens
    has_tools = any(tok in tokens for tok in {"TOOL", "TOOLS"})
    has_free = "FREE" in tokens
    has_paid = "PAID" in tokens
    has_stop = "STOP" in tokens
    has_pay = any(tok in tokens for tok in {"PAY", "PAYING"})
    has_replace = any(tok in tokens for tok in {"REPLACE", "REPLACES", "REPLACING", "INSTEAD"})
    count_five = any(tok in tokens for tok in {"5", "FIVE"})

    if not (has_ai or has_tools):
        return None
    if not (has_free or has_paid or has_stop or has_pay or has_replace):
        return None

    if has_stop and has_pay and has_ai:
        return "STOP PAYING FOR AI"
    if count_five and has_free and has_ai and has_tools:
        return "5 FREE AI TOOLS"
    if has_paid and has_ai:
        return "PAID AI? USE THESE"
    return "FREE TOOLS > PAID AI"


def _stock_hook_text(hook: str, pattern: str) -> str:
    preferred_paid_ai_hook = _preferred_paid_ai_hook(hook)
    if preferred_paid_ai_hook:
        return preferred_paid_ai_hook

    raw_tokens = _hook_tokens_upper(hook)
    content_tokens = [tok for tok in raw_tokens if tok not in _HOOK_FILLER_WORDS]
    object_tokens = [tok for tok in _extract_hook_objects(hook, max_words=3) if tok not in _HOOK_ACTION_WORDS]
    action_tokens = [tok for tok in content_tokens if tok in _HOOK_ACTION_WORDS]
    has_wrong = "WRONG" in content_tokens
    has_mistake = "MISTAKE" in content_tokens or "MISTAKES" in content_tokens

    # Filter out tutorial/long-form educational patterns
    tutorial_words = {"GUIDE", "BEGINNER", "TUTORIAL", "LEARN", "LEARNING", "MASTER", "COURSE", "STEP", "STEPS"}
    content_tokens = [tok for tok in content_tokens if tok not in tutorial_words]
    object_tokens = [tok for tok in object_tokens if tok not in tutorial_words]

    result_tokens: List[str]
    if pattern == "warning":
        # Prefer punchy warning patterns
        if object_tokens:
            result_tokens = ["STOP"] + object_tokens[:3]
        else:
            result_tokens = ["STOP", "AI", "TUTORIALS"]  # Default punchy pattern
    elif pattern == "mistake":
        core = object_tokens[:3] or content_tokens[:3]
        if core:
            result_tokens = ["YOUR"] + core + ["MISTAKE"]
        else:
            result_tokens = ["THE", "MISTAKE"]
    elif pattern == "list":
        # Prefer numbered punchy patterns
        if action_tokens and object_tokens:
            verb = action_tokens[0]
            obj = object_tokens[0]
            result_tokens = ["3", verb, obj, "THAT", "PAY"]
        elif object_tokens:
            result_tokens = ["3", "REAL"] + object_tokens[:2]
        else:
            result_tokens = ["3", "AI", "METHODS", "THAT", "PAY"]
    elif pattern == "myth":
        core = object_tokens[:3] or content_tokens[:3]
        if core:
            result_tokens = ["MOST", "PEOPLE", "DO"] + core + (["WRONG"] if has_wrong else [])
        else:
            result_tokens = ["MOST", "PEOPLE", "DO", "THIS", "WRONG"]
    elif pattern == "contrast":
        core = object_tokens[:3] or content_tokens[:3]
        if core:
            result_tokens = core + ["INSTEAD"]
        else:
            result_tokens = ["DO", "THIS", "INSTEAD"]
    else:
        core = object_tokens[:3] or content_tokens[:3]
        if any(tok in _HOOK_RESULT_WORDS for tok in content_tokens):
            result_tokens = (action_tokens[:1] or ["SHOW"]) + core[:2]
        else:
            # Default to punchy patterns
            if "AI" in content_tokens:
                result_tokens = ["REAL", "AI", "SIDE", "HUSTLES"]
            else:
                result_tokens = ["START"] + core[:2] if core else ["START", "HERE"]

    result_tokens = [tok for tok in result_tokens if tok]
    if not result_tokens:
        result_tokens = ["3", "AI", "METHODS", "THAT", "PAY"]  # Fallback to punchy pattern

    if len(result_tokens) > 6:
        result_tokens = result_tokens[:6]

    helper_words = {"DO", "THIS", "YOUR", "WHY", "START", "MOST", "PEOPLE", "YOU'RE", "DOING", "THE"}
    if len(result_tokens) <= 3 and all(tok not in helper_words for tok in result_tokens):
        if pattern == "myth" and has_wrong:
            result_tokens = ["YOU'RE", "DOING"] + result_tokens + ["WRONG"]
        elif pattern == "mistake":
            result_tokens = ["YOUR"] + result_tokens + (["MISTAKE"] if not has_mistake else [])
        elif pattern == "generic":
            result_tokens = ["START"] + result_tokens

    compact = []
    for tok in result_tokens:
        if tok not in compact:
            compact.append(tok)
    result_tokens = compact[:6]

    return " ".join(result_tokens[:6]).strip().upper()


def _stock_hook_visual_intent(pattern: str, hook: str = "") -> str:
    hook_upper = " ".join(_hook_tokens_upper(hook))
    has_explicit_results = any(word in hook_upper for word in _HOOK_RESULT_WORDS)
    if has_explicit_results and pattern not in {"warning", "mistake"}:
        return "proof"
    if pattern == "warning":
        return "interrupt"
    if pattern == "mistake":
        return "frustration"
    if pattern == "list":
        return "action"
    if pattern == "myth":
        return "contrast"
    if pattern == "contrast":
        return "contrast"
    return "action"


def _stock_hook_visual_description(intent: str, object_phrase: str = "") -> str:
    object_phrase = _clean_text(object_phrase)
    base = {
        "interrupt": "creator stopping a screen action abruptly, high-contrast opening, urgent motion",
        "frustration": "frustrated creator with laptop problem, overwhelmed work pressure, emotional opening",
        "proof": "clear results visual with dashboard or metrics, strong proof-first opening",
        "contrast": "wrong-versus-right contrast visual, clear comparison framing, attention-grabbing opening",
        "action": "creator taking fast purposeful action, energetic movement, decisive opening",
    }.get(intent, "creator taking fast purposeful action, energetic movement, decisive opening")
    if object_phrase:
        return f"{base}, focused on {object_phrase}"
    return base


def _stock_cta_display_text(cta: str) -> str:
    """
    Display-only CTA strengthening (spoken subtitle remains immutable).

    Conservative defaults:
    - Use CTA text first
    - If weak/empty, use neutral safe fallback
    - Uppercase, 2–6 words preferred, remove filler but keep readability
    """
    raw = _clean_text(cta).upper()
    if not raw or len(raw) < 3:
        return "FOLLOW FOR MORE"

    tokens = re.findall(r"[A-Z0-9']+", raw)
    if not tokens:
        return "FOLLOW FOR MORE"

    filler = {
        "PLEASE", "JUST", "NOW", "TODAY", "GUYS", "HEY", "ALRIGHT",
        "AND", "OR", "THE", "A", "AN", "TO", "FOR", "OF", "IN", "ON",
        "LIKE", "COMMENT", "SUBSCRIBE", "SHARE",
        "STACK", "STACKS", "REAL",
    }
    keep = [t for t in tokens if t not in filler]
    keep = keep or tokens[:]

    # Prefer short imperative patterns.
    if "FOLLOW" in keep:
        if "AI" in keep and "TOOLS" in keep:
            return "FOLLOW FOR AI TOOLS"
        if "AI" in keep and "WORKFLOWS" in keep:
            return "FOLLOW FOR AI WORKFLOWS"
        # Keep one helper word for readability if we'd get too robotic.
        base = ["FOLLOW"]
        tail = [t for t in keep if t != "FOLLOW"]
        if not tail:
            return "FOLLOW FOR MORE"
        out = (base + (["FOR"] if len(tail) == 1 else []) + tail)[:6]
    else:
        out = keep[:6]

    helper_words = {"FOR", "MORE", "REAL", "AI", "IDEAS", "NOW"}
    if len(out) <= 2 and not any(t in helper_words for t in out):
        out = ["FOLLOW", "FOR"] + out

    out = out[:6]
    if len(out) < 2:
        return "FOLLOW FOR MORE"
    return " ".join(out).strip().upper()


def _stock_hook_object_phrase(scene: "ScenePlan", matched_families: Optional[List[dict]] = None) -> str:
    for family in matched_families or []:
        phrase = _HOOK_OBJECT_FALLBACKS.get(family.get("label"))
        if phrase:
            return phrase
    objects = _extract_hook_objects(" ".join([scene.source_text or "", scene.subtitle or ""]), max_words=3)
    if objects:
        phrase = " ".join(tok.lower() for tok in objects[:3]).strip()
        # Avoid overly-generic/non-visual hook objects ("ai") that lead to dead stock searches.
        if "ai" in phrase.split() and not any(w in phrase for w in ["laptop", "phone", "screen", "dashboard", "email"]):
            return "laptop screen"
        if phrase in {"tutorial", "tutorials"}:
            return "laptop screen"
        return phrase
    return "creator workflow"


def _hook_query_templates(intent: str, object_phrase: str) -> List[str]:
    obj = _clean_text(object_phrase) or "creator workflow"
    templates = {
        "interrupt": [
            f"person stop gesture reacting to {obj} screen",
            f"creator stopping {obj} on laptop screen",
            f"person reacting to {obj} on computer screen",
            # Generic scroll-stoppers (kept deterministic) in case the object phrase is too niche.
            "person shocked at laptop screen close up",
            "frustrated person stopping work on laptop",
        ],
        "frustration": [
            f"creator frustrated with {obj} on laptop",
            f"overwhelmed creator looking at {obj} screen",
            f"stressed person reacting to {obj} on computer",
        ],
        "proof": [
            f"{obj} showing strong growth",
            f"creator checking {obj} metrics",
            f"{obj} results dashboard rising",
        ],
        "contrast": [
            f"creator comparing wrong right {obj}",
            f"confused creator choosing {obj}",
            f"{obj} wrong way versus right way",
        ],
        "action": [
            f"creator building {obj} on laptop",
            f"creator editing {obj} quickly on screen",
            f"person taking fast action on {obj} screen",
        ],
    }
    return templates.get(intent, templates["action"])


def _hook_fallback_queries() -> list[str]:
    """Deterministic strong hook-only queries (reaction/stop/surprise/face)."""
    return [
        "person stop gesture reacting to laptop screen",
        "person shocked at laptop screen close up",
        "frustrated person stopping work on laptop",
        "person shocked looking at phone close up",
        "person stopping scrolling phone reaction",
    ]


def apply_stock_hook_framework_to_scene_rows(rows: List[Dict], hook_text: str) -> List[Dict]:
    if not isinstance(rows, list) or not rows or not hook_text:
        return rows
    first = rows[0]
    if not isinstance(first, dict):
        return rows

    pattern = _classify_hook_pattern(hook_text)
    display_text = _stock_hook_text(hook_text, pattern)
    intent = _stock_hook_visual_intent(pattern, hook_text)
    object_tokens = _extract_hook_objects(hook_text, max_words=3)
    object_phrase = " ".join(tok.lower() for tok in object_tokens[:3]) if object_tokens else "creator workflow"
    visual_description = _stock_hook_visual_description(intent, object_phrase)

    updated = dict(first)
    updated["part"] = updated.get("part") or "hook"
    updated["on_screen_text"] = display_text or updated.get("on_screen_text") or updated.get("subtitle")
    updated["visual_description"] = visual_description
    updated["hook_pattern"] = pattern
    updated["hook_intent"] = intent
    rows = list(rows)
    rows[0] = updated
    return rows


def _classify_scene_intent(scene: "ScenePlan") -> str:
    if not scene:
        return "info_emphasis"
    part = (scene.part or "").lower().strip()
    if part == "hook":
        return "hook_emotion"
    if part == "cta":
        return "cta"

    blob = " ".join(
        [
            scene.source_text or "",
            scene.subtitle or "",
            scene.visual_description or "",
            " ".join(scene.keywords or []),
        ]
    ).lower()

    method_markers = {"method", "methods", "step", "steps", "ways", "tips", "tip", "how to"}
    action_markers = {
        "do", "start", "build", "create", "sell", "launch", "post", "write", "send", "edit", "ship",
        "publish", "upload", "design",
    }
    # Strict business/dashboard tokens only (avoid generic triggers like growth/revenue).
    business_visual_markers = {
        "dashboard", "analytics", "metrics", "graph", "chart", "ctr", "open rate", "kpi",
    }
    # Strong info phrases only (info_card is rare and must be justified).
    info_markers = {"why", "because", "rule"}

    if any(marker in blob for marker in method_markers) or re.search(r"\b\d+\b", blob):
        return "method_action"
    if any(marker in blob for marker in business_visual_markers):
        return "business_visual"
    if any(marker in blob for marker in info_markers):
        return "info_emphasis"
    if any(re.search(rf"\b{re.escape(token)}\b", blob) for token in action_markers):
        return "method_action"
    return "info_emphasis"


def _classify_proof_scene_type(scene: "ScenePlan") -> str:
    if not scene:
        return "stock_video"

    part = (getattr(scene, "part", "") or "").lower().strip()
    if part in {"hook", "cta"}:
        return "stock_video"

    blob = _proof_scene_blob(scene).lower()
    if not blob:
        return "stock_video"

    prompt_markers = ["prompt", "chatgpt", "paste", "script", "write me"]
    bill_markers = ["phone bill", "carrier", "monthly bill", "plan"]
    savings_markers = ["$", "per month", "per year", "360", "savings"]

    if any(marker in blob for marker in prompt_markers):
        return "prompt_demo"
    if any(marker in blob for marker in bill_markers):
        return "bill_demo"
    if any(marker in blob for marker in savings_markers):
        return "savings_math"
    return "stock_video"


def _choose_scene_asset_type(scene: "ScenePlan", intent: str) -> str:
    intent = (intent or "").strip()
    # Controlled rollback default: stock_video unless explicitly allowed by strategy gating.
    if intent in {"hook_emotion", "method_action", "business_visual", "info_emphasis", "cta"}:
        return "stock_video"
    return "stock_video"


def _apply_scene_asset_strategy(scenes: List["ScenePlan"]) -> dict[int, dict]:
    """
    Controlled rollback strategy (stock mode):
    - stock_video is the default
    - strict, capped non-stock usage for clarity only
    """
    scenes = list(scenes or [])
    strategy: dict[int, dict] = {}

    max_non_stock_scenes = 2
    max_info_cards = 1
    non_stock_used = 0
    info_used = 0

    strict_dashboard_tokens = {
        "dashboard", "analytics", "metrics", "graph", "chart", "ctr", "open rate", "kpi",
    }
    loose_dashboard_tokens = {
        "growth", "revenue", "sales", "reach", "subscribers", "subscriber", "newsletter", "email",
    }
    strong_info_phrases = {"why", "because", "rule"}

    def _scene_blob(s: "ScenePlan") -> str:
        return " ".join(
            [
                s.source_text or "",
                s.subtitle or "",
                str(getattr(s, "on_screen_text", "") or ""),
                s.visual_description or "",
                " ".join(s.keywords or []),
            ]
        ).lower()

    last_scene_idx = max((int(s.idx) for s in scenes), default=0)

    for scene in scenes:
        idx = int(scene.idx)
        part = (scene.part or "").lower().strip()
        intent = _classify_scene_intent(scene)
        blob = _scene_blob(scene)

        # Coherence override: narration/action scenes should stay stock_video.
        if part == "hook":
            asset_type = "stock_video"
            reason = "FORCED_STOCK_HOOK"
        elif intent == "method_action":
            asset_type = "stock_video"
            reason = "FORCED_STOCK_METHOD_ACTION"
        else:
            # Priority selection with caps.
            if part == "cta" and idx == last_scene_idx:
                if non_stock_used >= max_non_stock_scenes:
                    asset_type = "stock_video"
                    reason = "NON_STOCK_CAP_REACHED"
                else:
                    asset_type = "cta_card"
                    reason = "CTA_LAST_SCENE"
                    non_stock_used += 1
            elif any(tok in blob for tok in strict_dashboard_tokens):
                if non_stock_used >= max_non_stock_scenes:
                    asset_type = "stock_video"
                    reason = "NON_STOCK_CAP_REACHED"
                else:
                    asset_type = "dashboard_mockup"
                    reason = "DASHBOARD_STRICT_TOKEN_MATCH"
                    non_stock_used += 1
            elif any(tok in blob for tok in loose_dashboard_tokens) and not any(tok in blob for tok in strict_dashboard_tokens):
                asset_type = "stock_video"
                reason = "DASHBOARD_TOKEN_NOT_STRICT_ENOUGH"
            elif any(tok in blob for tok in strong_info_phrases):
                if info_used >= max_info_cards:
                    asset_type = "stock_video"
                    reason = "INFO_CARD_CAP_REACHED"
                elif non_stock_used >= max_non_stock_scenes:
                    asset_type = "stock_video"
                    reason = "NON_STOCK_CAP_REACHED"
                else:
                    asset_type = "info_card"
                    reason = "INFO_CARD_STRONG_PHRASE"
                    info_used += 1
                    non_stock_used += 1
            else:
                asset_type = "stock_video"
                reason = "DEFAULT_STOCK"

        strategy[idx] = {"intent": intent, "asset_type": asset_type, "reason": reason}
        print(
            "[ASSET_STRATEGY] "
            f"scene={idx} part={part} intent={intent} asset_type={asset_type} reason={reason}"
        )

    return strategy


def _apply_stock_scene_pacing_clamps(scenes: List["ScenePlan"]) -> List["ScenePlan"]:
    """
    Tight pacing for stock-mode retention.
    Reflows start/end sequentially so captions, renders, and assembly stay consistent.
    """
    cursor = 0.0
    for scene in scenes or []:
        part = (scene.part or "").lower().strip()
        raw_d = float(max(0.0, (scene.end - scene.start)))
        if part in {"hook", "cta"}:
            dur = min(2.5, max(1.6, raw_d))
        else:
            dur = max(2.0, min(3.5, max(1.6, raw_d)))
        scene.start = round(cursor, 2)
        cursor += dur
        scene.end = round(cursor, 2)
    return scenes


_CARD_W = 1080
_CARD_H = 1920


def _stable_seed(*parts: str) -> int:
    blob = "|".join([str(p or "") for p in parts]).encode("utf-8")
    return int(hashlib.md5(blob).hexdigest()[:8], 16)


def _try_load_font(size: int, bold: bool = False):
    from PIL import ImageFont
    candidates = []
    if os.name == "nt":
        base = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
        candidates.extend(
            [
                base / ("arialbd.ttf" if bold else "arial.ttf"),
                base / ("calibrib.ttf" if bold else "calibri.ttf"),
                base / ("segoeuib.ttf" if bold else "segoeui.ttf"),
            ]
        )
    candidates.extend(
        [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]
    )
    for path in candidates:
        try:
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        except Exception:
            continue
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(draw, text: str, font, max_width: int, max_lines: int) -> list[str]:
    words = [w for w in re.split(r"\s+", _clean_text(text)) if w]
    if not words:
        return [""]
    lines: list[str] = []
    current: list[str] = []

    def _fits(candidate: str) -> bool:
        try:
            bbox = draw.textbbox((0, 0), candidate, font=font)
            width = bbox[2] - bbox[0]
            return width <= max_width
        except Exception:
            return len(candidate) <= max(10, int(max_width / 20))

    for word in words:
        cand = " ".join(current + [word])
        if not current:
            # If a single token is too long (no spaces), hard-truncate so we never overflow.
            if not _fits(word):
                trimmed = word
                while trimmed and not _fits(trimmed + "…"):
                    trimmed = trimmed[:-1]
                current.append((trimmed + "…") if trimmed else "…")
            else:
                current.append(word)
            continue
        if _fits(cand):
            current.append(word)
            continue
        lines.append(" ".join(current))
        current = [word]
        if len(lines) >= max_lines:
            break

    if len(lines) < max_lines and current:
        lines.append(" ".join(current))

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if len(lines) == max_lines and len(words) > sum(len(l.split()) for l in lines):
        lines[-1] = lines[-1].rstrip(" .") + "…"
    return lines


def _ffmpeg_image_to_mp4(
    image_path: Path,
    out_path: Path,
    duration: float,
    fps: int = 30,
    *,
    zoom_start: float = 1.0,
    zoom_end: float = 1.03,
    pan_px: int = 0,
) -> bool:
    import subprocess

    duration = float(max(1.2, duration))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    render_fps = int(max(24, min(60, fps)))
    frames = max(2, int(round(duration * render_fps)))
    frames_minus_1 = max(1, frames - 1)
    z0 = float(max(1.0, zoom_start))
    z1 = float(max(z0, zoom_end))
    pan = int(max(-60, min(60, int(pan_px or 0))))

    # Deterministic, lightweight micro-motion:
    # - scale+crop to fill vertical frame
    # - zoompan from z0->z1 across frames
    # - optional tiny vertical drift in pixels (pan)
    pan_expr = f"+({pan})*((on/{frames_minus_1})-0.5)" if pan else ""
    vf = (
        f"scale={FAST_TARGET_W}:{FAST_TARGET_H}:force_original_aspect_ratio=increase,"
        f"crop={FAST_TARGET_W}:{FAST_TARGET_H},"
        "zoompan="
        f"z='{z0:.4f}+({(z1 - z0):.4f})*(on/{frames_minus_1})'"
        ":x='iw/2-(iw/zoom/2)'"
        f":y='ih/2-(ih/zoom/2){pan_expr}'"
        f":d=1:s={FAST_TARGET_W}x{FAST_TARGET_H}:fps={render_fps},"
        "format=yuv420p"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-t",
        f"{duration:.2f}",
        "-r",
        str(render_fps),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _image_to_mp4(
    image_path: Path,
    out_path: Path,
    duration: float,
    fps: int = 30,
    *,
    zoom_start: float = 1.0,
    zoom_end: float = 1.03,
    pan_px: int = 0,
) -> dict:
    ffmpeg_success = _ffmpeg_image_to_mp4(
        image_path=image_path,
        out_path=out_path,
        duration=duration,
        fps=fps,
        zoom_start=zoom_start,
        zoom_end=zoom_end,
        pan_px=pan_px,
    )
    if ffmpeg_success:
        return {"ffmpeg_success": True, "fallback_used": False}

    # Fallback to MoviePy if ffmpeg invocation fails (MoviePy is already a stable dependency here).
    from moviepy.editor import ImageClip

    duration = float(max(1.2, duration))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    render_fps = int(max(24, min(60, fps)))
    clip = ImageClip(str(image_path)).set_duration(duration).set_fps(render_fps)
    clip.write_videofile(
        str(out_path),
        codec="libx264",
        audio=False,
        fps=render_fps,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )
    clip.close()
    return {"ffmpeg_success": False, "fallback_used": True}


def _render_info_card(scene: "ScenePlan", run_id: str) -> tuple[str, dict]:
    from PIL import Image, ImageDraw

    duration = float(max(1.6, (scene.end - scene.start)))
    png_path = TEMP_DIR / f"{run_id}_scene_{scene.idx}_info.png"
    out_path = RAW_DIR / f"{run_id}_scene_{scene.idx}_info.mp4"

    img = Image.new("RGB", (_CARD_W, _CARD_H), (10, 12, 18))
    draw = ImageDraw.Draw(img)
    # High-contrast gradient background.
    top = (18, 20, 32)
    bottom = (6, 8, 14)
    for yy in range(_CARD_H):
        t = yy / float(max(1, _CARD_H - 1))
        col = (
            int(top[0] * (1 - t) + bottom[0] * t),
            int(top[1] * (1 - t) + bottom[1] * t),
            int(top[2] * (1 - t) + bottom[2] * t),
        )
        draw.line([(0, yy), (_CARD_W, yy)], fill=col)

    # Subtle dark overlays to enforce hierarchy (headline band + footer band).
    try:
        from PIL import Image as _PILImage

        overlay = _PILImage.new("RGBA", (_CARD_W, _CARD_H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rectangle([0, 0, _CARD_W, int(_CARD_H * 0.44)], fill=(0, 0, 0, 86))
        od.rectangle([0, int(_CARD_H * 0.70), _CARD_W, _CARD_H], fill=(0, 0, 0, 68))
        img = _PILImage.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
    except Exception:
        pass
    draw.rectangle([0, 0, _CARD_W, 170], fill=(18, 24, 40))
    draw.rectangle([0, 168, _CARD_W, 178], fill=(255, 210, 64))

    display = _clean_text(getattr(scene, "on_screen_text", "") or scene.subtitle or scene.source_text or "")
    title = display.strip().upper()
    title = re.sub(r"[^A-Z0-9\\s'’-]", "", title)
    if not title:
        title = "KEY IDEA"

    body = _clean_text(scene.subtitle or scene.source_text or "")
    body = re.sub(r"\s+", " ", body)

    title_font = _try_load_font(104, bold=True)
    body_font = _try_load_font(56, bold=False)

    title_lines = _wrap_text(draw, title, title_font, max_width=980, max_lines=2)
    y = 250
    for line in title_lines:
        draw.text((60, y), line, font=title_font, fill=(255, 255, 255))
        y += 118

    if body and body.strip().upper() != title:
        body_lines = _wrap_text(draw, body, body_font, max_width=960, max_lines=3)
        y2 = max(int(_CARD_H * 0.70), y + 60)
        for line in body_lines:
            draw.text((60, y2), line, font=body_font, fill=(220, 232, 255))
            y2 += 72

    img.save(png_path, "PNG")
    zoom_start = 1.0
    zoom_end = 1.04  # allowed slightly stronger for info scenes
    pan_px = 0
    meta = _image_to_mp4(
        image_path=png_path,
        out_path=out_path,
        duration=duration,
        fps=30,
        zoom_start=zoom_start,
        zoom_end=zoom_end,
        pan_px=pan_px,
    )
    return str(out_path), {
        "duration": duration,
        "zoom_start": zoom_start,
        "zoom_end": zoom_end,
        "pan_px": pan_px,
        **meta,
    }


def _dashboard_labels_for_scene(scene: "ScenePlan", matched_families: Optional[List[dict]] = None) -> list[str]:
    labels: list[str] = []
    families = [f.get("label") for f in (matched_families or []) if isinstance(f, dict)]
    blob = " ".join([scene.source_text or "", scene.subtitle or "", " ".join(scene.keywords or [])]).lower()

    if "email_list" in families or any(tok in blob for tok in ["email", "newsletter", "subscriber", "subscribers", "open rate"]):
        labels = ["SUBSCRIBERS", "OPEN RATE", "SPONSORS"]
    elif any(f in families for f in ["digital_products", "prompt_products"]) or any(tok in blob for tok in ["template", "templates", "download", "downloads", "listing", "listings"]):
        labels = ["SALES", "DOWNLOADS", "LISTINGS"]
    elif "growth_analytics" in families or any(tok in blob for tok in ["analytics", "dashboard", "growth", "ctr", "reach", "views"]):
        labels = ["CTR", "REACH", "GROWTH"]
    elif "sponsors" in families or "sponsor" in blob:
        labels = ["SPONSORS", "DEALS", "CPM"]
    else:
        labels = ["CTR", "REACH", "GROWTH"]

    return labels[:3]


def _dashboard_values_for_labels(labels: list[str], seed: int) -> list[str]:
    import random

    rng = random.Random(seed)
    values: list[str] = []
    for label in labels:
        key = (label or "").upper().strip()
        if key in {"SUBSCRIBERS", "REACH"}:
            base = rng.randint(8_000, 180_000)
            values.append(f"{base/1000:.1f}K")
        elif key in {"SALES", "DOWNLOADS", "LISTINGS", "DEALS", "SPONSORS"}:
            base = rng.randint(18, 420)
            values.append(str(base))
        elif key in {"OPEN RATE", "CTR"}:
            pct = rng.uniform(1.8, 58.0)
            values.append(f"{pct:.1f}%")
        elif key == "GROWTH":
            pct = rng.uniform(6.0, 120.0)
            values.append(f"+{pct:.0f}%")
        elif key == "CPM":
            dollars = rng.uniform(6.0, 48.0)
            values.append(f"${dollars:.0f}")
        else:
            values.append(str(rng.randint(10, 99)))
    return values


def _render_dashboard_mockup(scene: "ScenePlan", run_id: str) -> tuple[str, dict]:
    from PIL import Image, ImageDraw

    duration = float(max(1.6, (scene.end - scene.start)))
    png_path = TEMP_DIR / f"{run_id}_scene_{scene.idx}_dash.png"
    out_path = RAW_DIR / f"{run_id}_scene_{scene.idx}_dash.mp4"

    matched_families = _match_concept_families(scene)
    labels = _dashboard_labels_for_scene(scene, matched_families=matched_families)
    values = _dashboard_values_for_labels(labels, seed=_stable_seed(run_id, str(scene.idx), "dash"))

    img = Image.new("RGB", (_CARD_W, _CARD_H), (12, 14, 20))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([50, 180, _CARD_W - 50, _CARD_H - 180], radius=32, fill=(22, 28, 42))
    draw.rounded_rectangle([70, 210, _CARD_W - 70, 320], radius=24, fill=(18, 24, 38))
    head_font = _try_load_font(54, bold=True)
    draw.text((95, 240), "DASHBOARD", font=head_font, fill=(245, 245, 245))

    tile_font = _try_load_font(40, bold=True)
    value_font = _try_load_font(62, bold=True)

    tile_w = int((_CARD_W - 140 - 40) / 2)
    x0 = 90
    y0 = 380
    gap = 40

    tiles = [
        (x0, y0, x0 + tile_w, y0 + 280),
        (x0 + tile_w + gap, y0, x0 + 2 * tile_w + gap, y0 + 280),
        (x0, y0 + 320, x0 + tile_w, y0 + 600),
    ]
    for idx, rect in enumerate(tiles[:3]):
        draw.rounded_rectangle(rect, radius=28, fill=(16, 20, 32))
        label = labels[idx] if idx < len(labels) else "METRIC"
        value = values[idx] if idx < len(values) else "0"
        draw.text((rect[0] + 28, rect[1] + 26), label, font=tile_font, fill=(210, 220, 240))
        draw.text((rect[0] + 28, rect[1] + 110), value, font=value_font, fill=(255, 210, 64))

    chart_left = 90
    chart_top = y0 + 980
    chart_right = _CARD_W - 90
    chart_bottom = _CARD_H - 260
    draw.rounded_rectangle([chart_left, chart_top, chart_right, chart_bottom], radius=28, fill=(16, 20, 32))

    points = []
    import random
    rng = random.Random(_stable_seed(run_id, str(scene.idx), "spark"))
    n = 10

    # Gridlines for realism.
    grid_col = (38, 46, 64)
    for i in range(1, 5):
        yy = chart_top + int((chart_bottom - chart_top) * (i / 5.0))
        draw.line([(chart_left + 24, yy), (chart_right - 24, yy)], fill=grid_col, width=3)

    # Bar shapes behind the line for a "dashboard" feel.
    bar_w = int((chart_right - chart_left - 120) / n)
    bar_base = chart_bottom - 46
    for i in range(n):
        xx = chart_left + 60 + i * bar_w
        h = rng.randint(40, int((chart_bottom - chart_top) * 0.45))
        draw.rounded_rectangle([xx, bar_base - h, xx + int(bar_w * 0.7), bar_base], radius=10, fill=(26, 32, 50))

    for i in range(n):
        x = chart_left + 40 + int((chart_right - chart_left - 80) * (i / (n - 1)))
        y = chart_bottom - 56 - rng.randint(20, int((chart_bottom - chart_top) * 0.65))
        points.append((x, y))
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=(255, 210, 64), width=8)

    img.save(png_path, "PNG")
    zoom_start = 1.0
    zoom_end = 1.03
    pan_px = 10
    meta = _image_to_mp4(
        image_path=png_path,
        out_path=out_path,
        duration=duration,
        fps=30,
        zoom_start=zoom_start,
        zoom_end=zoom_end,
        pan_px=pan_px,
    )
    return str(out_path), {
        "duration": duration,
        "zoom_start": zoom_start,
        "zoom_end": zoom_end,
        "pan_px": pan_px,
        **meta,
    }


def _render_cta_card(scene: "ScenePlan", run_id: str) -> tuple[str, dict]:
    from PIL import Image, ImageDraw

    duration = float(max(1.6, (scene.end - scene.start)))
    png_path = TEMP_DIR / f"{run_id}_scene_{scene.idx}_cta.png"
    out_path = RAW_DIR / f"{run_id}_scene_{scene.idx}_cta.mp4"

    # CTA must be conservative and script-aligned: prefer spoken subtitle/source_text.
    raw = _clean_text(scene.subtitle or scene.source_text or "")
    words = re.findall(r"[A-Za-z0-9']+", raw)
    if len(words) < 2:
        blob = " ".join([scene.source_text or "", scene.subtitle or "", " ".join(scene.keywords or [])]).lower()
        if any(tok in blob for tok in ["ai", "prompt", "chatgpt"]):
            raw = "FOLLOW FOR REAL AI IDEAS"
        else:
            raw = "FOLLOW FOR MORE"

    title = raw.strip().upper()
    title = re.sub(r"[^A-Z0-9\\s'’-]", "", title)

    # Enhanced color scheme for higher contrast and visual impact
    bg_color = (8, 8, 12)  # Deeper background
    card_bg = (28, 32, 48)  # Slightly lighter card background
    accent_color = (255, 193, 7)  # More vibrant gold accent
    text_color = (255, 255, 255)  # Pure white for maximum contrast

    img = Image.new("RGB", (_CARD_W, _CARD_H), bg_color)
    draw = ImageDraw.Draw(img)

    # Main card with enhanced styling
    card_x1, card_y1 = 60, 480
    card_x2, card_y2 = _CARD_W - 60, 1450
    draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=52, fill=card_bg)

    # Enhanced accent bar with gradient effect
    accent_height = 80
    draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y1 + accent_height], radius=0, fill=accent_color)

    # Add subtle inner shadow/highlight for depth
    highlight_color = (48, 52, 68)
    draw.rounded_rectangle([card_x1 + 8, card_y1 + 8, card_x2 - 8, card_y1 + accent_height - 8], radius=44, fill=highlight_color)

    # Improved typography with better spacing and hierarchy
    title_font = _try_load_font(96, bold=True)  # Slightly larger
    lines = _wrap_text(draw, title, title_font, max_width=880, max_lines=3)

    # Better vertical spacing and positioning
    line_height = 124  # Increased spacing
    total_text_height = len(lines) * line_height
    start_y = card_y1 + accent_height + 80  # More space from accent bar

    for i, line in enumerate(lines):
        y = start_y + i * line_height
        # Add subtle text shadow for depth
        draw.text((card_x1 + 52, y + 2), line, font=title_font, fill=(0, 0, 0))
        draw.text((card_x1 + 50, y), line, font=title_font, fill=text_color)

    img.save(png_path, "PNG")
    zoom_start = 1.0
    zoom_end = 1.04  # allowed slightly stronger for CTA, keep readable
    pan_px = 0
    meta = _image_to_mp4(
        image_path=png_path,
        out_path=out_path,
        duration=duration,
        fps=30,
        zoom_start=zoom_start,
        zoom_end=zoom_end,
        pan_px=pan_px,
    )
    return str(out_path), {
        "duration": duration,
        "zoom_start": zoom_start,
        "zoom_end": zoom_end,
        "pan_px": pan_px,
        **meta,
    }


def _proof_scene_blob(scene: "ScenePlan") -> str:
    return _clean_text(
        " ".join(
            [
                getattr(scene, "subtitle", "") or "",
                getattr(scene, "source_text", "") or "",
                getattr(scene, "on_screen_text", "") or "",
            ]
        )
    )


def _extract_currency_values(text: str) -> list[float]:
    values: list[float] = []
    for raw in re.findall(r"\$\s*([0-9]+(?:\.[0-9]{1,2})?)", text or ""):
        try:
            values.append(float(raw))
        except Exception:
            continue
    return values


def _format_money(value: float) -> str:
    if abs(value - round(value)) < 0.01:
        return f"${int(round(value))}"
    return f"${value:.2f}".rstrip("0").rstrip(".")


def _extract_monthly_and_yearly_values(scene: "ScenePlan") -> tuple[str, str]:
    blob = _proof_scene_blob(scene)
    monthly_value: Optional[float] = None
    yearly_value: Optional[float] = None

    month_match = re.search(r"\$\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:/|per\s+)?month", blob, re.IGNORECASE)
    year_match = re.search(r"\$\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:/|per\s+)?year", blob, re.IGNORECASE)

    if month_match:
        monthly_value = float(month_match.group(1))
    if year_match:
        yearly_value = float(year_match.group(1))

    if monthly_value is None:
        values = _extract_currency_values(blob)
        if values:
            monthly_value = values[0]

    if yearly_value is None and monthly_value is not None:
        yearly_value = monthly_value * 12.0

    if yearly_value is None:
        values = _extract_currency_values(blob)
        if len(values) >= 2:
            yearly_value = values[1]

    monthly_label = _format_money(monthly_value) + "/month" if monthly_value is not None else "$30/month"
    yearly_label = _format_money(yearly_value) + "/year" if yearly_value is not None else "$360/year"
    return monthly_label, yearly_label


def _render_prompt_demo_clip(scene: "ScenePlan", run_id: str) -> str:
    from PIL import Image, ImageDraw

    duration = float(max(1.6, (scene.end - scene.start)))
    png_path = TEMP_DIR / f"{run_id}_scene_{scene.idx}_proof_prompt.png"
    out_path = RAW_DIR / f"{run_id}_scene_{scene.idx}_proof_prompt.mp4"

    display = _clean_text(getattr(scene, "on_screen_text", "") or scene.subtitle or scene.source_text or "")
    prompt_text = display or _clean_text(scene.subtitle or scene.source_text or "") or "Write me a better script for this topic."

    img = Image.new("RGB", (_CARD_W, _CARD_H), (8, 10, 16))
    draw = ImageDraw.Draw(img)

    top = (14, 18, 30)
    bottom = (4, 6, 12)
    for yy in range(_CARD_H):
        t = yy / float(max(1, _CARD_H - 1))
        col = (
            int(top[0] * (1 - t) + bottom[0] * t),
            int(top[1] * (1 - t) + bottom[1] * t),
            int(top[2] * (1 - t) + bottom[2] * t),
        )
        draw.line([(0, yy), (_CARD_W, yy)], fill=col)

    card = [56, 180, _CARD_W - 56, _CARD_H - 220]
    draw.rounded_rectangle(card, radius=54, fill=(17, 23, 36), outline=(46, 66, 104), width=4)
    draw.rounded_rectangle([card[0], card[1], card[2], card[1] + 138], radius=54, fill=(23, 31, 49))
    draw.rectangle([card[0], card[1] + 76, card[2], card[1] + 138], fill=(23, 31, 49))

    for idx, dot_color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        x = card[0] + 42 + idx * 34
        draw.ellipse([x, card[1] + 44, x + 20, card[1] + 64], fill=dot_color)

    label_font = _try_load_font(44, bold=True)
    title_font = _try_load_font(86, bold=True)
    body_font = _try_load_font(56, bold=False)
    chip_font = _try_load_font(34, bold=True)

    draw.text((card[0] + 150, card[1] + 34), "AI PROMPT", font=label_font, fill=(135, 168, 255))
    draw.text((card[0] + 70, card[1] + 188), "Prompt to paste into ChatGPT", font=title_font, fill=(255, 255, 255))

    prompt_box = [card[0] + 56, card[1] + 360, card[2] - 56, card[3] - 220]
    draw.rounded_rectangle(prompt_box, radius=34, fill=(10, 14, 24), outline=(52, 72, 110), width=3)
    prompt_lines = _wrap_text(draw, prompt_text, body_font, max_width=prompt_box[2] - prompt_box[0] - 72, max_lines=8)
    yy = prompt_box[1] + 46
    for line in prompt_lines:
        draw.text((prompt_box[0] + 36, yy), line, font=body_font, fill=(231, 237, 250))
        yy += 72

    chip_w = 320
    chip_h = 72
    chip_x = prompt_box[2] - chip_w - 28
    chip_y = prompt_box[3] + 74
    draw.rounded_rectangle([chip_x, chip_y, chip_x + chip_w, chip_y + chip_h], radius=30, fill=(37, 145, 255))
    draw.text((chip_x + 28, chip_y + 18), "Copy this prompt", font=chip_font, fill=(255, 255, 255))

    img.save(png_path, "PNG")
    _image_to_mp4(
        image_path=png_path,
        out_path=out_path,
        duration=duration,
        fps=30,
        zoom_start=1.0,
        zoom_end=1.05,
        pan_px=12,
    )
    return str(out_path)


def _render_bill_demo_clip(scene: "ScenePlan", run_id: str) -> str:
    from PIL import Image, ImageDraw

    duration = float(max(1.6, (scene.end - scene.start)))
    png_path = TEMP_DIR / f"{run_id}_scene_{scene.idx}_proof_bill.png"
    out_path = RAW_DIR / f"{run_id}_scene_{scene.idx}_proof_bill.mp4"
    monthly_label, yearly_label = _extract_monthly_and_yearly_values(scene)

    raw_text = _clean_text(scene.subtitle or scene.source_text or "")
    savings_match = re.search(r"\b(save|saving|savings)\b.*?(\$\s*[0-9]+(?:\.[0-9]{1,2})?)", raw_text, re.IGNORECASE)
    savings_label = savings_match.group(2).replace(" ", "") if savings_match else yearly_label

    img = Image.new("RGB", (_CARD_W, _CARD_H), (238, 241, 246))
    draw = ImageDraw.Draw(img)

    for yy in range(_CARD_H):
        shade = 246 - int(yy * 0.018)
        draw.line([(0, yy), (_CARD_W, yy)], fill=(shade, shade, min(255, shade + 4)))

    sheet = [88, 120, _CARD_W - 88, _CARD_H - 140]
    draw.rounded_rectangle(sheet, radius=42, fill=(255, 255, 255), outline=(214, 220, 230), width=4)
    draw.rectangle([sheet[0], sheet[1], sheet[2], sheet[1] + 126], fill=(28, 36, 58))

    heading_font = _try_load_font(54, bold=True)
    meta_font = _try_load_font(34, bold=False)
    value_font = _try_load_font(70, bold=True)
    small_font = _try_load_font(42, bold=True)

    draw.text((sheet[0] + 42, sheet[1] + 30), "CARRIER BILL", font=heading_font, fill=(255, 255, 255))
    draw.text((sheet[2] - 260, sheet[1] + 42), "AUTO PAY", font=meta_font, fill=(170, 186, 220))

    rows = [
        ("Monthly charge", monthly_label),
        ("Projected annual", yearly_label),
        ("Potential savings", savings_label),
    ]
    y = sheet[1] + 220
    for idx, (label, value) in enumerate(rows):
        row_bottom = y + 220
        if idx < len(rows) - 1:
            draw.line([(sheet[0] + 42, row_bottom), (sheet[2] - 42, row_bottom)], fill=(228, 232, 238), width=3)
        draw.text((sheet[0] + 42, y), label.upper(), font=small_font, fill=(92, 102, 120))
        draw.text((sheet[0] + 42, y + 70), value, font=value_font, fill=(19, 28, 46))
        y += 250

    footer = [sheet[0] + 42, sheet[3] - 270, sheet[2] - 42, sheet[3] - 72]
    draw.rounded_rectangle(footer, radius=28, fill=(235, 248, 240))
    draw.text((footer[0] + 28, footer[1] + 30), "Savings line item", font=small_font, fill=(45, 122, 74))
    draw.text((footer[0] + 28, footer[1] + 94), "Switch plan and keep the same coverage.", font=meta_font, fill=(66, 86, 94))

    img.save(png_path, "PNG")
    _image_to_mp4(
        image_path=png_path,
        out_path=out_path,
        duration=duration,
        fps=30,
        zoom_start=1.0,
        zoom_end=1.04,
        pan_px=8,
    )
    return str(out_path)


def _render_savings_math_clip(scene: "ScenePlan", run_id: str) -> str:
    from PIL import Image, ImageDraw

    duration = float(max(1.6, (scene.end - scene.start)))
    png_path = TEMP_DIR / f"{run_id}_scene_{scene.idx}_proof_math.png"
    out_path = RAW_DIR / f"{run_id}_scene_{scene.idx}_proof_math.mp4"
    monthly_label, yearly_label = _extract_monthly_and_yearly_values(scene)

    img = Image.new("RGB", (_CARD_W, _CARD_H), (10, 14, 18))
    draw = ImageDraw.Draw(img)
    for yy in range(_CARD_H):
        t = yy / float(max(1, _CARD_H - 1))
        col = (
            int(12 * (1 - t) + 2 * t),
            int(18 * (1 - t) + 10 * t),
            int(24 * (1 - t) + 18 * t),
        )
        draw.line([(0, yy), (_CARD_W, yy)], fill=col)

    panel = [74, 210, _CARD_W - 74, _CARD_H - 230]
    draw.rounded_rectangle(panel, radius=48, fill=(16, 22, 28), outline=(38, 50, 60), width=3)

    label_font = _try_load_font(48, bold=True)
    hero_font = _try_load_font(128, bold=True)
    equals_font = _try_load_font(112, bold=True)
    sub_font = _try_load_font(44, bold=False)

    draw.text((panel[0] + 54, panel[1] + 62), "SAVINGS MATH", font=label_font, fill=(116, 221, 168))
    draw.text((panel[0] + 54, panel[1] + 230), monthly_label.replace("/month", "/mo"), font=hero_font, fill=(255, 255, 255))
    draw.text((panel[0] + 54, panel[1] + 398), "every month", font=sub_font, fill=(173, 188, 198))
    draw.text((panel[0] + 54, panel[1] + 650), "=", font=equals_font, fill=(116, 221, 168))
    draw.text((panel[0] + 54, panel[1] + 860), yearly_label.replace("/year", "/year"), font=hero_font, fill=(255, 255, 255))
    draw.text((panel[0] + 54, panel[1] + 1028), "per year", font=sub_font, fill=(173, 188, 198))

    note_box = [panel[0] + 54, panel[3] - 230, panel[2] - 54, panel[3] - 82]
    draw.rounded_rectangle(note_box, radius=28, fill=(22, 34, 41))
    draw.text((note_box[0] + 30, note_box[1] + 38), "Simple payoff proof. No stock footage needed.", font=sub_font, fill=(215, 226, 232))

    img.save(png_path, "PNG")
    _image_to_mp4(
        image_path=png_path,
        out_path=out_path,
        duration=duration,
        fps=30,
        zoom_start=1.0,
        zoom_end=1.05,
        pan_px=6,
    )
    return str(out_path)


def _visual_description_tokens(visual_desc: str) -> str:
    """Extract meaningful tokens from visual description - Batch 2A"""
    if not visual_desc:
        return ""
    _TEMPLATE_NOISE = {
        "high", "contrast", "opening", "motion", "symbolic", "matching",
        "concept", "relevant", "explanatory", "metaphor", "tied",
        "result", "oriented", "clean", "style", "ending", "action",
        "broll", "b-roll", "vertical", "cinematic",
    }
    _LOW_SIGNAL = {
        "dark", "black", "night", "shadow", "silhouette", "background", "gradient",
        "animation", "graphics", "symbol", "symbols", "neon", "overlay", "text",
    }
    vd_tokens = [
        w for w in re.findall(r"[a-zA-Z]{4,}", visual_desc.lower())
        if w not in STOPWORDS and w not in _TEMPLATE_NOISE and w not in _LOW_SIGNAL
    ]
    return " ".join(vd_tokens[:4]) if vd_tokens else ""


_CONCEPT_FAMILY_MAP: List[dict] = [
    {
        "label": "digital_products",
        "phrases": ["digital product", "digital products", "digital downloads", "template marketplace"],
        "queries": [
            "digital product mockup online store",
            "selling digital downloads ecommerce",
            "tablet product listing creator business",
            "template marketplace digital files",
        ],
    },
    {
        "label": "prompt_products",
        "phrases": ["ai prompts", "sell prompts", "digital prompts", "prompt product"],
        "queries": [
            "chatgpt prompt writing laptop",
            "digital prompt product storefront",
            "creator selling digital prompts",
        ],
    },
    {
        "label": "explainer_videos",
        "phrases": ["explainer video", "explainer videos", "video editing", "editing timeline"],
        "queries": [
            "video editing timeline laptop",
            "editor creating marketing video",
            "small business promo video editing",
            "camera production editing workspace",
        ],
    },
    {
        "label": "small_business",
        "phrases": ["small business", "small businesses", "business owner", "local business"],
        "queries": [
            "small business owner shop laptop",
            "local business marketing workspace",
            "entrepreneur packaging orders storefront",
        ],
    },
    {
        "label": "email_list",
        "phrases": ["email list", "newsletter", "subscriber", "subscribers", "email campaign"],
        "queries": [
            "email marketing dashboard analytics",
            "newsletter subscriber growth screen",
            "email campaign metrics laptop",
        ],
    },
    {
        "label": "sponsors",
        "phrases": ["sponsor", "sponsors", "sponsorship", "brand deal", "brand partnership"],
        "queries": [
            "brand partnership marketing meeting",
            "creator sponsorship deal laptop",
            "advertising partnership analytics",
        ],
    },
    {
        "label": "growth_analytics",
        "phrases": ["growth", "analytics", "dashboard", "subscriber growth", "audience growth"],
        "queries": [
            "growth chart analytics dashboard",
            "subscriber count social analytics",
            "business metrics upward graph",
        ],
    },
]


def _match_concept_families(scene: ScenePlan) -> List[dict]:
    haystack = " ".join(
        [
            scene.source_text or "",
            scene.subtitle or "",
            scene.visual_description or "",
            " ".join(scene.keywords or []),
        ]
    ).lower()
    return [family for family in _CONCEPT_FAMILY_MAP if any(phrase in haystack for phrase in family["phrases"])]


def _infer_stock_archetype(query: str, clip_title: str, scene_part: str) -> str:
    tokens = set(re.findall(r"[a-z0-9']+", f"{query} {clip_title}".lower()))
    if {"desk", "typing"}.issubset(tokens) or (
        ("laptop" in tokens or "computer" in tokens) and ("desk" in tokens or "workspace" in tokens)
    ):
        return "desk_typing"
    if "meeting" in tokens or "conference" in tokens:
        return "meeting_room"
    if "phone" in tokens or "smartphone" in tokens or "mobile" in tokens or "scroll" in tokens:
        return "phone_scroll"
    if "money" in tokens or "cash" in tokens or "wallet" in tokens or "dollar" in tokens:
        return "money_closeup"
    if "editing" in tokens or "editor" in tokens or "timeline" in tokens:
        return "editing_timeline"
    if "camera" in tokens or "production" in tokens or "filming" in tokens:
        return "camera_production"
    if "email" in tokens or "newsletter" in tokens or "subscriber" in tokens or "inbox" in tokens:
        return "email_dashboard"
    if "growth" in tokens or "chart" in tokens or "analytics" in tokens or "dashboard" in tokens or "graph" in tokens:
        return "growth_chart"
    if "creator" in tokens or "talking" in tokens or "speaking" in tokens or "reaction" in tokens:
        return "creator_talking"
    if "abstract" in tokens or "graphic" in tokens or "graphics" in tokens or "animation" in tokens:
        return "abstract_graphics"
    if "office" in tokens or "business" in tokens or "professional" in tokens or "workspace" in tokens:
        return "generic_office"
    return "other"


def _infer_environment_family(query: str, clip_title: str) -> str:
    tokens = set(re.findall(r"[a-z0-9']+", f"{query} {clip_title}".lower()))
    if any(token in tokens for token in {"reaction", "shocked", "surprised", "frustrated", "overwhelmed", "face"}):
        return "person_reaction"
    if "timeline" in tokens or "editing" in tokens or "editor" in tokens:
        return "editing_timeline"
    if any(token in tokens for token in {"dashboard", "analytics", "metrics", "graph", "chart", "subscriber", "ctr"}):
        return "dashboard_screen"
    if any(token in tokens for token in {"phone", "mobile", "smartphone", "scroll", "scrolling", "tap", "tapping"}):
        return "phone_hand"
    if any(token in tokens for token in {"monitor", "screen", "ui", "interface", "website", "inbox"}) and not any(
        token in tokens for token in {"dashboard", "analytics", "metrics", "graph", "chart"}
    ):
        return "monitor_ui"
    if ("laptop" in tokens or "computer" in tokens) and any(
        token in tokens for token in {"close", "closeup", "typing", "hands", "keyboard"}
    ):
        return "laptop_closeup"
    if any(token in tokens for token in {"desk", "workspace", "office", "keyboard", "mouse"}):
        return "desk_setup"
    return "other"


def _token_overlap_ratio(left_tokens: set[str], right_tokens: set[str]) -> float:
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens.intersection(right_tokens))
    return overlap / float(max(1, min(len(left_tokens), len(right_tokens))))


def _build_visual_profile(
    scene: ScenePlan,
    query: str,
    clip_title: str,
    clip_source: str,
    matched_concepts: Optional[List[dict]] = None,
) -> dict:
    tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9']+", f"{query} {clip_title}".lower())
        if token not in STOPWORDS
    }
    archetype = _infer_stock_archetype(query, clip_title, scene.part)
    if "tablet" in str(clip_title or "").lower() or "tablet" in str(query or "").lower():
        archetype = "tablet"
    environment_family = _infer_environment_family(query, clip_title)
    return {
        "scene_idx": scene.idx,
        "scene_part": scene.part,
        "query": query,
        "clip_title": clip_title,
        "clip_source": clip_source,
        "archetype": archetype,
        "environment_family": environment_family,
        "tokens": tokens,
        "matched_concepts": [family["label"] for family in (matched_concepts or [])],
    }


def _scene_query_candidates(scene: ScenePlan) -> List[str]:
    """
    Build a prioritised list (3-4 only) of stock-footage search queries for a scene.
    
    Hook scenes: use high-impact emotional templates
    Other scenes: base + contextual + fallback (3 queries max)
    
    Batch 2A: Minimal, well-logged approach.
    """
    candidates: List[str] = []
    matched_families = _match_concept_families(scene)

    if scene.part == "hook":
        hook_seed = " ".join(
            [
                scene.source_text or "",
                scene.subtitle or "",
                scene.visual_description or "",
            ]
        ).strip()
        pattern = _classify_hook_pattern(hook_seed)
        intent = _stock_hook_visual_intent(pattern, hook_seed)
        object_phrase = _stock_hook_object_phrase(scene, matched_families)

        candidates.extend(
            [
                "person stop gesture reacting to laptop screen",
                "person shocked at laptop screen close up",
                "person clicking laptop frustrated reaction",
                "person stopping scrolling phone reaction",
            ]
        )
        candidates.extend(_hook_query_templates(intent, object_phrase))

        for family in matched_families[:2]:
            for family_query in family["queries"][:2]:
                family_clean = _clean_text(family_query)
                if family_clean and family_clean not in candidates:
                    candidates.append(family_clean)

        context_words = _extract_meaningful_words(hook_seed, max_words=3)
        if context_words:
            context_phrase = " ".join(context_words[:3]).lower()
            context_query = f"person reacting to {context_phrase} on computer screen"
            if context_query not in candidates:
                candidates.append(context_query)
        candidates = candidates[:4]
    elif scene.part == "cta":
        # CTA must be action-oriented and explicitly "follow/phone" driven.
        # Keep deterministic and avoid weak generic success/nature clips.
        base = [
            "creator posting short video on phone",
            "person tapping follow button on phone screen",
            "creator pointing to follow button on phone",
            "hand scrolling social media feed on phone",
            "finger tapping follow on phone close up",
        ]
        # If we have meaningful CTA words, include them, but enforce phone/follow token presence.
        cta_seed = _clean_text(" ".join([scene.source_text or "", scene.subtitle or "", getattr(scene, "on_screen_text", "") or ""]))
        seed_words = [
            w for w in _extract_meaningful_words(cta_seed, max_words=4)
            if w not in {"real", "stack", "stacks", "ideas"}
        ]
        if seed_words:
            # Dedup common words to avoid "phone phone ... phone" style queries.
            dedup = []
            for w in seed_words:
                if w not in dedup:
                    dedup.append(w)
            base.insert(0, f"creator posting on phone for {(' '.join(dedup)).lower()}")

        must_have = {"phone", "scroll", "scrolling", "tap", "tapping", "follow", "creator"}
        filtered: list[str] = []
        for q in base:
            ql = q.lower()
            if any(tok in ql for tok in must_have):
                filtered.append(q)
        candidates = filtered[:4]
    else:
        # Role-aware query scaffolds to satisfy strict progression gates and improve stock availability.
        role = str(getattr(scene, "role_label", "") or "").strip().lower()
        scene_blob = " ".join([scene.source_text or "", scene.subtitle or "", scene.visual_description or ""]).lower()
        scene_specific_prepended = False

        # Scene-specific overrides come first so tool/action beats do not collapse into repeated dashboards.
        if any(tok in scene_blob for tok in ["capcut", "editing", "edit", "timeline", "captions", "auto-captions", "video"]):
            candidates.extend(
                [
                    "video editor working on timeline close up",
                    "editing captions on video timeline screen",
                    "creator editing short form video on computer",
                ]
            )
            scene_specific_prepended = True
        elif any(tok in scene_blob for tok in ["canva", "thumbnail", "thumbnails", "design", "mockup", "template", "product mockup"]):
            candidates.extend(
                [
                    "designer creating thumbnail on laptop screen",
                    "graphic designer editing layout on laptop screen",
                    "creator making product mockup on laptop screen",
                ]
            )
            scene_specific_prepended = True
        elif any(tok in scene_blob for tok in ["chatgpt", "perplexity", "research", "writing", "outline", "outlines"]):
            candidates.extend(
                [
                    "person typing in document on laptop close up",
                    "searching information on computer screen close up",
                    "comparing research results on laptop screen",
                    "research workflow on laptop browser",
                ]
            )
            scene_specific_prepended = True
        elif any(tok in scene_blob for tok in ["compare", "comparison", "compare tools", "results", "search results"]):
            candidates.extend(
                [
                    "search results comparison on computer screen",
                    "person comparing tool results on laptop screen",
                    "dashboard comparison on computer screen close up",
                ]
            )
            scene_specific_prepended = True

        if role == "payoff_1" and not scene_specific_prepended:
            candidates.extend(
                [
                    "person typing on laptop writing email",
                    "creator working on laptop desk typing fast",
                    "writing email on computer screen close up",
                ]
            )
        elif role == "payoff_2" and not scene_specific_prepended:
            candidates.extend(
                [
                    "email marketing dashboard analytics screen",
                    "open rate ctr dashboard screen",
                    "website analytics dashboard on laptop",
                ]
            )
        elif role == "payoff_3" and not scene_specific_prepended:
            candidates.extend(
                [
                    "sending invoice payment on laptop screen",
                    "online payment confirmation on phone",
                    "freelancer invoice paid notification",
                ]
            )

        # Keep concept-family queries but leave space for scene-specific tokens so body scenes
        # don't collapse into identical dashboard queries across multiple beats.
        for family in matched_families[:2]:
            candidates.extend(family["queries"][:1])

        scene_specific_words = _extract_meaningful_words(
            f"{scene.source_text or ''} {scene.visual_description or ''}",
            max_words=5,
        )
        if scene_specific_words:
            candidates.append(" ".join(scene_specific_words))

        raw_keywords = _extract_keywords(scene.source_text or "", fallback=scene.keywords or [])
        for kw in raw_keywords:
            phrase = _VISUAL_KEYWORD_MAP.get(kw.lower())
            if phrase:
                candidates.append(phrase)

        part_fallbacks = {
            "body": "specific concept b roll business action",
            "cta": "person success growth achievement",
        }
        candidates.append(part_fallbacks.get(scene.part, "specific concept footage"))
        candidates = candidates[:6]
    
    # ──────────────────────────────────────────────────────────────────────────
    # Dedup and normalize
    # ──────────────────────────────────────────────────────────────────────────
    seen: set = set()
    result: List[str] = []
    for c in candidates:
        cleaned = re.sub(r"\s+", " ", str(c)).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    
    return result


def _score_clip_quality_for_scene(
    clip_title: str,
    clip_source: str,
    scene_part: str,
    used_clips: set = None,
) -> Tuple[float, str]:
    """
    Simple clip quality scorer for stock footage (Batch 2A).
    
    Returns: (score: 0-100, rejection_reason: "" if accepted)
    
    - Penalize duplicates (same source/title)
    - For hooks: penalize weak/generic clips strongly
    - For body/cta: allow office/professional visuals
    - Always reject dark/abstract/animation
    """
    score = 50.0  # baseline
    rejection = ""
    
    if used_clips is None:
        used_clips = set()
    
    clip_id = f"{clip_source}:{clip_title}"
    
    # ── REJECT: Already used in this video ────────────────────────────────
    if clip_id in used_clips:
        return 0.0, "DUPLICATE_CLIP"
    
    title_lower = clip_title.lower()
    
    # ── HOOK SCENES: Stricter quality rules ─────────────────────────────
    if scene_part == "hook":
        # REJECT: Generic neutral clips (strict for hooks)
        weak_keywords = {
            "office", "professional", "calm", "peaceful", "serene",
            "meeting", "desk job", "workspace", "business casual"
        }
        if any(weak in title_lower for weak in weak_keywords):
            # Exception: allow if ALSO has emotional hint
            if "person" in title_lower or "reaction" in title_lower:
                score += 10  # boost if it has emotional hint
            else:
                return 0.0, "GENERIC_NEUTRAL_FOR_HOOK"
        
        # BOOST: Emotional/reaction clips (strongly)
        emotional = ["shocked", "surprised", "frustrated", "stressed", "reaction", 
                    "emotion", "dramatic", "urgent", "overwhelmed", "confused"]
        emotion_hits = sum(1 for e in emotional if e in title_lower)
        if emotion_hits > 0:
            score += 20 * min(emotion_hits, 2)
        
        # BOOST: Person visible
        if "person" in title_lower:
            score += 15
        
        # PENALIZE: Too slow/calm for hook
        if any(calm in title_lower for calm in ["calm", "peaceful", "serene", "slow"]):
            score -= 30
    
    # ── GENERAL RULES: All scenes ───────────────────────────────────────
    # BOOST: People, action, emotion
    positive = ["person", "people", "action", "movement", "dynamic", "emotion"]
    positive_hits = sum(1 for p in positive if p in title_lower)
    score += 5 * min(positive_hits, 2)
    
    # PENALIZE: Too dark for stock mode
    if "dark" in title_lower or "night" in title_lower:
        score -= 20
    
    # PENALIZE: Abstract/graphics
    if any(abstract in title_lower for abstract in ["abstract", "graphic", "animation", "motion graphics"]):
        score -= 25
    
    # Cap score
    score = max(0.0, min(100.0, score))
    
    return score, rejection


def _log_scene_query_process(
    scene_idx: int,
    scene_part: str,
    candidates: List[str],
    winning_query: str,
    winning_clip_source: str,
    winning_clip_title: str,
    rejected_clips: List[Tuple[str, str]] = None,
) -> None:
    """Log the query selection process for debugging (Batch 2A)"""
    print(f"\n[SCENE {scene_idx}] ({scene_part.upper()})")
    print(f"  Candidates: {candidates}")
    print(f"  Winning query: '{winning_query}'")
    print(f"  Selected clip: {winning_clip_source}/{winning_clip_title}")
    if rejected_clips:
        for rejected_title, reason in rejected_clips[:2]:
            print(f"    Rejected: {rejected_title} ({reason})")


def _split_text_evenly(text: str, chunks: int) -> List[str]:
    chunks = max(1, int(chunks or 1))
    cleaned = _clean_text(text)
    if not cleaned:
        return [""] * chunks

    # Subtitle segmentation fix: split deterministically on explicit step/payoff markers,
    # ensuring each resulting chunk contains ONE idea and doesn't include the next label.
    marker_pattern = re.compile(
        r"\b(?:(?:STEP\s+(?:ONE|TWO|THREE|FOUR|[1-4]))|(?:PAYOFF\s*[1-4]))\b\s*:?\s*",
        re.IGNORECASE,
    )
    markers = list(marker_pattern.finditer(cleaned))
    if markers:
        spans: list[str] = []
        for idx, m in enumerate(markers):
            start = m.start()
            end = markers[idx + 1].start() if idx + 1 < len(markers) else len(cleaned)
            chunk_text = cleaned[start:end].strip()
            if chunk_text:
                spans.append(chunk_text)
        if spans:
            # Ensure punctuation ending for better Whisper alignment.
            norm: list[str] = []
            for s in spans:
                s = s.strip()
                if s and s[-1] not in ".!?":
                    s = s + "."
                norm.append(s)
            # If requested chunks differs, pad/truncate deterministically.
            if len(norm) >= chunks:
                return norm[:chunks]
            return norm + [""] * (chunks - len(norm))

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
    if len(sentences) >= chunks:
        out = []
        step = len(sentences) / chunks
        for index in range(chunks):
            start = int(round(index * step))
            end = int(round((index + 1) * step))
            piece = " ".join(sentences[start:end]).strip()
            out.append(piece or sentences[min(start, len(sentences) - 1)])
        return out

    words = cleaned.split()
    if not words:
        return [cleaned] + [""] * (chunks - 1)

    out = []
    step = len(words) / chunks
    for index in range(chunks):
        start = int(round(index * step))
        end = int(round((index + 1) * step))
        piece = " ".join(words[start:end]).strip()
        out.append(piece)
    return [item if item else cleaned for item in out]


def _score_clip_quality_for_scene(
    clip_title: str,
    clip_source: str,
    scene_part: str,
    query: str = "",
    role_label: str = "",
    used_clips: set = None,
    recent_visual_profiles: Optional[List[dict]] = None,
    matched_concepts: Optional[List[dict]] = None,
) -> Tuple[float, str]:
    """Score stock-footage candidates with concept fit and light diversity checks."""
    score = 50.0

    if used_clips is None:
        used_clips = set()
    if recent_visual_profiles is None:
        recent_visual_profiles = []

    clip_id = f"{clip_source}:{clip_title}"
    if clip_id in used_clips:
        return 0.0, "DUPLICATE_CLIP"

    title_lower = clip_title.lower()
    role = (role_label or "").strip().lower()
    archetype = _infer_stock_archetype(query, clip_title, scene_part)
    archetype_key = "tablet" if ("tablet" in str(query or "").lower() or "tablet" in title_lower) else archetype
    environment_family = _infer_environment_family(query, clip_title)
    # Token sets used for deterministic relevance checks.
    query_tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9']+", str(query or "").lower())
        if token and token not in STOPWORDS
    }
    clip_tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9']+", str(clip_title or "").lower())
        if token and token not in STOPWORDS
    }
    title_tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9']+", f"{query} {clip_title}".lower())
        if token not in STOPWORDS
    }
    expected_tokens = {
        token
        for family in (matched_concepts or [])
        for token in re.findall(r"[a-zA-Z0-9']+", f"{family['label']} {' '.join(family['phrases'])}".lower())
        if token not in STOPWORDS
    }
    concept_overlap = _token_overlap_ratio(title_tokens, expected_tokens)

    # Unified token view for scoring when clip titles are numeric IDs (common for stock URLs).
    all_tokens = set(title_tokens) | set(expected_tokens) | set(query_tokens) | set(clip_tokens)

    # Hard reject absurd/off-topic categories unless script/query explicitly implies them.
    # This is a deterministic guardrail to prevent "dinosaur/greenscreen novelty" clips.
    animal_tokens = {
        "dinosaur", "trex", "t-rex", "reptile",
        "cat", "dog", "monkey", "wildlife", "zoo", "pet", "puppy", "kitten",
    }
    novelty_tokens = {"costume", "mascot", "meme", "prank"}
    scenic_tokens = {"sunset", "beach", "ocean", "palm", "nature", "scenic"}
    greenscreen_hits = any(t in title_lower for t in ["green screen", "greenscreen", "chroma key", "chromakey"])
    animal_hits = bool(clip_tokens.intersection(animal_tokens)) or any(tok in title_lower for tok in ["t-rex", "trex"])
    novelty_hits = bool(clip_tokens.intersection(novelty_tokens))
    scenic_hits = bool(clip_tokens.intersection(scenic_tokens)) or any(tok in title_lower for tok in scenic_tokens)

    # Allow if the query or expected concepts explicitly contain the same topic tokens.
    allow_absurd = bool((query_tokens | expected_tokens).intersection(animal_tokens | novelty_tokens)) or any(
        t in str(query or "").lower() for t in ["green screen", "greenscreen", "chroma key", "chromakey"]
    )
    # NOTE: clip_title often contains only numeric IDs; primary scenic rejection happens at search-time
    # using API metadata/tags. Still keep this as a backstop if keywords appear.
    if scenic_hits and not bool((query_tokens | expected_tokens).intersection(scenic_tokens)):
        return 0.0, "OFFTOPIC_SCENIC"
    if (greenscreen_hits or animal_hits or novelty_hits) and not allow_absurd:
        if greenscreen_hits:
            return 0.0, "GREENSCREEN_MISMATCH"
        if animal_hits:
            return 0.0, "OFFTOPIC_ANIMAL"
        return 0.0, "OFFTOPIC_NOVELTY"

    # Business/info coherence: if the scene expects business visuals and overlap is weak,
    # require at least one concrete business object token in the clip title/query.
    business_signal = {
        "creator", "workflow", "editing", "edit", "editor", "timeline", "video",
        "laptop", "computer", "screen", "phone", "website", "template",
        "dashboard", "analytics", "metrics", "graph", "chart", "spreadsheet",
        "email", "newsletter", "subscribers", "subscriber", "open", "rate", "ctr", "reach",
        "marketing", "product", "listing", "listings", "sales", "downloads", "promo",
    }
    business_objects = {
        "laptop", "computer", "screen", "dashboard", "analytics", "phone",
        "editing", "editor", "timeline", "spreadsheet", "email", "website", "template",
        "typing", "invoice",
    }
    business_expected = bool((expected_tokens | query_tokens).intersection(business_signal))
    has_business_object = bool((clip_tokens | query_tokens).intersection(business_objects))
    tool_workflow_expected = bool(
        (query_tokens | expected_tokens).intersection(
            {
                "chatgpt", "perplexity", "research", "writing", "writer", "outline", "outlines",
                "canva", "design", "designer", "thumbnail", "thumbnails", "template", "mockup",
                "editing", "edit", "editor", "timeline", "video", "captions", "capcut",
                "dashboard", "analytics", "screen", "website", "interface", "ui",
            }
        )
    )
    # Strict business object rule (approved): if overlap is zero and no business object, reject.
    if business_expected and concept_overlap <= 0.0 and not has_business_object:
        return 0.0, "NO_CONCEPT_AND_NO_BUSINESS_OBJECT"

    if scene_part == "hook":
        # Hook progression guardrail: hook must be reaction/person/interrupt, not charts/tablets.
        hook_reaction_tokens = ["reaction", "shocked", "surprised", "frustrated", "stressed", "overwhelmed", "confused", "face", "person"]
        # IMPORTANT: clip titles are often numeric IDs (especially on Pexels), so use combined tokens
        # (query + expected concepts + any title tokens) instead of only `clip_title` text.
        all_tokens = set(title_tokens) | set(expected_tokens) | set(query_tokens) | set(clip_tokens)
        if archetype_key in {"growth_chart", "email_dashboard", "tablet"} and not any(t in all_tokens for t in hook_reaction_tokens):
            return 0.0, "HOOK_NOT_REACTION"
        pattern = _classify_hook_pattern(query or clip_title)
        intent = _stock_hook_visual_intent(pattern, query or clip_title)
        generic_neutral = {
            "office", "professional", "calm", "peaceful", "serene",
            "meeting", "desk", "workspace", "business casual",
        }
        if any(weak in title_lower for weak in generic_neutral) and not any(
            token in all_tokens
            for token in ["reaction", "frustrated", "shocked", "overwhelmed", "growth", "editing", "dashboard"]
        ):
            return 0.0, "GENERIC_NEUTRAL_FOR_HOOK"
        if environment_family in {"desk_setup", "laptop_closeup", "monitor_ui"}:
            return 0.0, "GENERIC_NEUTRAL_FOR_HOOK"
        if environment_family == "person_reaction":
            score += 18
        if environment_family == "phone_hand" and any(token in query_tokens for token in {"follow", "scrolling", "phone", "tap", "tapping"}):
            score += 8

        intent_keywords = {
            "interrupt": ["stop", "stopping", "rejecting", "closing", "warning", "shocked", "surprised", "reaction"],
            "frustration": ["frustrated", "stressed", "overwhelmed", "confused", "problem", "error", "failing"],
            "proof": ["growth", "metrics", "results", "dashboard", "analytics", "revenue", "subscribers", "sales"],
            "contrast": ["compare", "comparison", "versus", "choice", "wrong", "right", "before", "after"],
            "action": ["editing", "building", "launching", "creating", "typing", "uploading", "working", "fast"],
        }
        hits = sum(1 for token in intent_keywords.get(intent, []) if token in all_tokens)
        if hits:
            score += 14 * min(hits, 2)
        else:
            # If the query explicitly asks for reaction/face, don't penalize for missing title tokens.
            if any(t in all_tokens for t in ["reaction", "shocked", "surprised", "frustrated", "overwhelmed", "stressed"]):
                score += 24
            else:
                score -= 12

        if intent in {"interrupt", "frustration"} and any(calm in title_lower for calm in ["calm", "peaceful", "serene", "slow"]):
            score -= 35

        if intent == "proof" and not any(token in all_tokens for token in ["dashboard", "analytics", "growth", "metrics", "chart"]):
            score -= 15

        if intent == "action" and not any(token in all_tokens for token in ["editing", "building", "creating", "typing", "launching", "working"]):
            score -= 10
        if not any(token in query_tokens for token in {"screen", "laptop", "phone", "computer", "clicking", "scrolling", "gesture"}):
            score -= 10

    positive = ["person", "people", "action", "movement", "dynamic", "emotion"]
    score += 5 * min(sum(1 for token in positive if token in all_tokens), 2)

    if "dark" in title_lower or "night" in title_lower:
        score -= 20

    if archetype == "abstract_graphics":
        if scene_part == "hook":
            return 0.0, "ABSTRACT_GRAPHICS"
        if scene_part == "body":
            score -= 28
            if concept_overlap <= 0.0:
                return 0.0, "ABSTRACT_GRAPHICS"
        else:
            score -= 8

    if tool_workflow_expected:
        abstract_filler_tokens = {"waveform", "ambient", "background", "glow", "abstract", "graphic", "animation", "monitor"}
        abstract_hits = len(all_tokens.intersection(abstract_filler_tokens))
        if environment_family == "monitor_ui" and not has_business_object:
            score -= 20
        if environment_family == "other" and abstract_hits:
            score -= 10
        if environment_family == "editing_timeline":
            score += 14
        elif environment_family in {"monitor_ui", "dashboard_screen"}:
            score += 10
        elif environment_family == "other" and any(tok in query_tokens for tok in {"research", "search", "results", "comparison", "browser", "perplexity", "writing", "document", "writer"}):
            score += 8

        if any(tok in query_tokens for tok in {"editing", "edit", "editor", "timeline", "captions", "capcut", "video"}):
            score += 10
        if any(tok in query_tokens for tok in {"research", "search", "results", "comparison", "browser", "perplexity"}):
            score += 10
        if any(tok in query_tokens for tok in {"design", "designer", "thumbnail", "thumbnails", "mockup", "template", "layout", "canva"}):
            score += 10
        if any(tok in query_tokens for tok in {"writing", "writer", "document", "outline", "outlines", "typing"}):
            score += 8
        if abstract_hits:
            score -= 12 * min(abstract_hits, 2)
        if archetype == "abstract_graphics":
            return 0.0, "ABSTRACT_GRAPHICS"

    if matched_concepts:
        if concept_overlap <= 0.0:
            if scene_part == "hook":
                # Hook exception: if the query itself is explicitly reaction/interrupt oriented,
                # don't hard-reject due to concept mismatch (clip titles are often numeric IDs).
                hook_ok = bool(set(query_tokens).intersection({"reaction", "shocked", "surprised", "frustrated", "stressed", "overwhelmed", "stop"}))
                if not hook_ok:
                    return 0.0, "WEAK_CONCEPT_MATCH"
                score -= 10
            if scene_part == "body":
                if archetype in {"generic_office", "desk_typing", "meeting_room"}:
                    return 0.0, "WEAK_CONCEPT_MATCH"
                score -= 18
            else:
                score -= 6
        elif concept_overlap < 0.2:
            if scene_part == "hook":
                score -= 18
            elif scene_part == "body":
                score -= 8
            else:
                score -= 3

    for index, previous in enumerate(recent_visual_profiles[:2]):
        overlap_ratio = _token_overlap_ratio(title_tokens, previous.get("tokens", set()))
        same_archetype = archetype_key == previous.get("archetype")
        same_environment = environment_family == previous.get("environment_family")
        is_adjacent = index == 0

        hard_environment_reject = {"desk_setup", "laptop_closeup", "monitor_ui"}
        if same_environment and is_adjacent and environment_family in hard_environment_reject:
            return 0.0, "REPEATED_ENVIRONMENT_ADJACENT"

        # Hard reject consecutive repeats for high-risk archetypes.
        repeat_reject = {"growth_chart", "tablet", "email_dashboard", "generic_office", "desk_typing"}
        if same_archetype and is_adjacent and archetype_key in repeat_reject:
            return 0.0, "REPEATED_ARCHETYPE_ADJACENT"

        if same_archetype and archetype == "desk_typing" and scene_part in {"hook", "body"}:
            return 0.0, "REPEATED_DESK_TYPING"
        if same_archetype and archetype == "generic_office" and scene_part in {"hook", "body"}:
            return 0.0, "REPEATED_GENERIC_OFFICE"
        if same_archetype and is_adjacent and scene_part == "hook":
            return 0.0, "SIMILAR_ARCHETYPE_ADJACENT"
        if same_archetype and is_adjacent and scene_part == "body" and archetype in {"meeting_room", "desk_typing", "generic_office"}:
            return 0.0, "SIMILAR_ARCHETYPE_ADJACENT"
        if same_archetype:
            score -= 18 if is_adjacent else 10
        if same_environment:
            score -= 14 if is_adjacent else 6
        if overlap_ratio >= 0.7 and scene_part in {"hook", "body"}:
            return 0.0, "HIGH_TOKEN_OVERLAP_WITH_PREV"
        if overlap_ratio >= 0.45:
            score -= 12 if is_adjacent else 6

    # Role-based progression enforcement (deterministic).
    # These are "must include" token families; if not present, reject to force searching the next candidate.
    all_tokens = set(title_tokens) | set(expected_tokens) | set(query_tokens) | set(clip_tokens)
    def _has_any(tokens: list[str]) -> bool:
        return any(t in all_tokens for t in tokens)

    tool_action_override_tokens = {
        "chatgpt", "perplexity", "research", "writing", "writer", "outline", "outlines",
        "canva", "design", "designer", "thumbnail", "thumbnails", "template", "mockup",
        "editing", "edit", "editor", "timeline", "video", "captions", "capcut",
    }
    role_override = bool((query_tokens | expected_tokens).intersection(tool_action_override_tokens))

    if role in {"payoff_1"}:
        if not (has_business_object and _has_any(["typing", "write", "writing", "edit", "editing", "working", "laptop", "computer"])):
            return 0.0, "ROLE_EXPECT_ACTION_WORK"
    elif role in {"payoff_2"}:
        if not role_override and not _has_any(["dashboard", "analytics", "email", "website", "spreadsheet", "screen", "interface", "ui"]):
            return 0.0, "ROLE_EXPECT_INTERFACE"
    elif role in {"payoff_3"}:
        if not role_override and not _has_any(["invoice", "payment", "paid", "money", "cash", "revenue", "sales", "subscribers", "clicks", "ctr", "results", "growth", "upfront"]):
            return 0.0, "ROLE_EXPECT_RESULT_PAYMENT"
    elif role in {"cta"}:
        if not _has_any(["phone", "mobile", "scroll", "scrolling", "tap", "tapping", "follow", "creator", "posting", "post"]):
            return 0.0, "ROLE_EXPECT_CTA_ACTION"
        if environment_family not in {"phone_hand", "person_reaction", "other"}:
            score -= 8

    score = max(0.0, min(100.0, score))

    # Minimum score rule (approved): MIN_SCORE = 45 across scenes.
    MIN_SCORE = 45.0
    if role_override and has_business_object and scene_part == "body":
        MIN_SCORE = 38.0
    if tool_workflow_expected and scene_part == "body":
        MIN_SCORE = min(MIN_SCORE, 34.0)
    if score < MIN_SCORE:
        return score, f"LOW_SCORE_{int(MIN_SCORE)}"

    return score, ""


def _log_scene_query_process(
    scene_idx: int,
    scene_part: str,
    candidates: List[str],
    winning_query: str,
    winning_clip_source: str,
    winning_clip_title: str,
    winning_profile: Optional[dict] = None,
    rejected_clips: List[Tuple[str, str]] = None,
) -> None:
    """Log the query selection process for debugging."""
    print(f"\n[SCENE {scene_idx}] ({scene_part.upper()})")
    print(f"  Candidates: {candidates}")
    print(f"  Winning query: '{winning_query}'")
    print(f"  Selected clip: {winning_clip_source}/{winning_clip_title}")
    if winning_profile:
        print(
            "  Profile: "
            f"archetype={winning_profile.get('archetype')} "
            f"environment_family={winning_profile.get('environment_family')} "
            f"concepts={winning_profile.get('matched_concepts')} "
            f"tokens={sorted(list(winning_profile.get('tokens', set())))[:6]}"
        )
    if rejected_clips:
        for rejected_title, reason in rejected_clips[:3]:
            print(f"    Rejected: {rejected_title} ({reason})")


def resolve_duration_seconds(parts: ScriptParts, requested_seconds: Optional[int] = None) -> int:
    requested = int(requested_seconds or 0)

    full_text = " ".join([parts.hook or "", parts.body or "", parts.cta or ""]).strip()
    word_count = len(re.findall(r"\b\w+\b", full_text))

    estimated = int(math.ceil(word_count / 2.2)) + 2 if word_count > 0 else 10
    baseline = max(10, requested if requested > 0 else 12)
    resolved = max(baseline, estimated)

    return max(10, min(45, resolved))


def build_scene_plan(parts: ScriptParts, duration_seconds: int = 12, stock_mode: bool = False) -> List[ScenePlan]:
    total = float(max(10, min(45, int(duration_seconds or 12))))

    # Role-aware pacing: deterministic beat structure for retention.
    # NOTE: timing is decided here (planning layer) and must not be rewritten later.
    hook_d = min(2.4, max(2.0, total * 0.18))
    cta_d = min(2.5, max(2.0, total * 0.18))
    body_d = max(0.0, total - hook_d - cta_d)

    body_scene_count = max(1, min(8, int(round(body_d / 2.8))))

    # If body contains explicit step/payoff markers, prefer one scene per marker for coherence.
    marker_hits = re.findall(
        r"\b(?:STEP\s+(?:ONE|TWO|THREE|FOUR|[1-4])|PAYOFF\s*[1-4])\b",
        parts.body or "",
        flags=re.IGNORECASE,
    )
    if marker_hits:
        body_scene_count = max(1, min(6, len(marker_hits)))

    # Deterministic payoff role assignment:
    # - first body -> payoff_1
    # - middle bodies -> payoff_2
    # - last body -> payoff_3
    # Special cases:
    # - 1 body: payoff_2
    # - 2 bodies: payoff_1, payoff_3
    body_roles: list[str] = []
    if body_scene_count == 1:
        body_roles = ["payoff_2"]
    elif body_scene_count == 2:
        body_roles = ["payoff_1", "payoff_3"]
    else:
        body_roles = ["payoff_1"] + ["payoff_2"] * (body_scene_count - 2) + ["payoff_3"]

    # Base durations per role, then normalize to body_d with deterministic clamp + redistribution.
    base_by_role = {"payoff_1": 2.7, "payoff_2": 2.4, "payoff_3": 2.1}
    # Allow body beats to fill the requested duration while staying snappy.
    # These bounds also avoid spilling leftover time into an overlong CTA.
    bounds_by_role = {
        "payoff_1": (2.0, 3.5),
        "payoff_2": (2.0, 3.5),
        "payoff_3": (1.8, 3.2),
    }
    base_sum = sum(base_by_role[r] for r in body_roles) or 1.0
    scale = (body_d / base_sum) if body_d > 0 else 1.0
    body_durations = [base_by_role[r] * scale for r in body_roles]

    # Clamp to bounds.
    for i, role in enumerate(body_roles):
        lo, hi = bounds_by_role[role]
        body_durations[i] = max(lo, min(hi, body_durations[i]))

    # Redistribute leftover seconds deterministically (0.05s ticks) within bounds.
    def _redistribute(delta: float) -> None:
        nonlocal body_durations
        step = 0.05
        if abs(delta) < 0.01:
            return
        # Prefer extending payoff_2 (clarity), then payoff_1, then payoff_3.
        priority = ["payoff_2", "payoff_1", "payoff_3"]
        # Use scene order to keep deterministic.
        indices_by_role = {r: [i for i, rr in enumerate(body_roles) if rr == r] for r in priority}

        guard = 0
        while abs(delta) >= 0.01 and guard < 5000:
            guard += 1
            changed = False
            for role in priority:
                lo, hi = bounds_by_role[role]
                for i in indices_by_role.get(role, []):
                    if delta > 0:
                        if body_durations[i] + step <= hi + 1e-6:
                            body_durations[i] += step
                            delta -= step
                            changed = True
                    else:
                        if body_durations[i] - step >= lo - 1e-6:
                            body_durations[i] -= step
                            delta += step
                            changed = True
                    if abs(delta) < 0.01:
                        return
            if not changed:
                return

    _redistribute(body_d - sum(body_durations))

    # Build scene ranges with role labels.
    ranges: list[tuple[str, str, float, float]] = []
    t = 0.0
    ranges.append(("hook", "hook", t, min(total, t + hook_d)))
    t = ranges[-1][3]
    for i in range(body_scene_count):
        role = body_roles[i]
        dur = body_durations[i] if i < len(body_durations) else (body_d / max(1, body_scene_count))
        start = t
        end = min(total, start + dur)
        ranges.append(("body", role, start, end))
        t = end
    # CTA absorbs any rounding drift to end exactly on `total`.
    ranges.append(("cta", "cta", t, total))

    body_chunks = _split_text_evenly(parts.body, body_scene_count)
    body_index = 0

    scenes: List[ScenePlan] = []
    for index, (part, role, start, end) in enumerate(ranges, start=1):
        if part == "hook":
            txt = parts.hook or "Watch this!"
            if stock_mode:
                hook_pattern = _classify_hook_pattern(parts.hook or "")
                hook_display = _stock_hook_text(parts.hook or "", hook_pattern)
                hook_intent = _stock_hook_visual_intent(hook_pattern, parts.hook or "")
                object_tokens = _extract_hook_objects(parts.hook or "", max_words=3)
                object_phrase = " ".join(tok.lower() for tok in object_tokens[:3]) if object_tokens else "creator workflow"
                visual = _stock_hook_visual_description(hook_intent, object_phrase)
                subtitle = txt or ""
                on_screen_text = hook_display or subtitle
            else:
                visual = "high emotion reaction or bold symbolic opening stock footage matching the hook"
                subtitle = txt or ""
                on_screen_text = subtitle
            energy = "urgency"
            fallback = ["attention", "speed", "notification", "abstract"]
        elif part == "body":
            txt = body_chunks[min(body_index, len(body_chunks) - 1)] if body_chunks else parts.body
            body_index += 1
            if stock_mode:
                lower = (txt or "").lower()
                moneyish = any(
                    token in lower
                    for token in [
                        "$",
                        "charge",
                        "charged",
                        "invoice",
                        "payment",
                        "paid",
                        "upfront",
                        "deliver",
                        "delivered",
                        "hours",
                        "hour",
                        "24",
                    ]
                )
                dashboardish = any(
                    token in lower
                    for token in [
                        "dashboard",
                        "analytics",
                        "metrics",
                        "growth",
                        "graph",
                        "chart",
                        "subscriber",
                        "subscribers",
                        "newsletter",
                        "email",
                        "open rate",
                        "ctr",
                        "reach",
                        "revenue",
                        "sales",
                        "listing",
                        "listings",
                        "downloads",
                    ]
                )
                infoish = any(token in lower for token in ["why", "because", "means", "myth", "truth", "rule", "mistake", "wrong"])
                if moneyish:
                    visual = "freelancer invoice payment on laptop screen, money transfer, client deal close up, high contrast"
                elif dashboardish:
                    visual = "clean dashboard mockup showing key business metrics (subscribers, growth, sales), high contrast"
                elif infoish:
                    visual = "bold info card with key idea in large readable text, high contrast, minimal distractions"
                else:
                    visual = "specific concept stock footage illustrating the body idea, avoid generic office visuals"
            else:
                visual = "specific concept stock footage illustrating the body idea, avoid generic office visuals"
            energy = "curiosity"
            fallback = ["workflow", "process", "automation", "business"]
            subtitle = txt
            on_screen_text = subtitle
        else:
            txt = parts.cta or "Follow for more!"
            if stock_mode:
                visual = "clean CTA card with big readable call to action text, high contrast"
            else:
                visual = "clear success, decision, or call to action ending stock footage"
            energy = "confidence"
            fallback = ["growth", "success", "goal", "minimal"]
            subtitle = txt or ""
            # Display-only CTA strengthening; spoken subtitle stays immutable.
            on_screen_text = _stock_cta_display_text(subtitle or "")

        scene_obj = ScenePlan(
            idx=index,
            start=round(start, 2),
            end=round(end, 2),
            part=part,
            source_text=txt,
            subtitle=subtitle,
            visual_description=visual,
            keywords=_extract_keywords(txt, fallback),
            energy=energy,
        )
        setattr(scene_obj, "role_label", str(role))
        # Sidecar field for display-only text (never used for captions).
        setattr(scene_obj, "on_screen_text", _clean_text(on_screen_text or subtitle))
        scenes.append(scene_obj)

        try:
            d = float(scene_obj.end) - float(scene_obj.start)
        except Exception:
            d = float(max(0.0, end - start))
        print(
            "[RETENTION] "
            f"scene={scene_obj.idx} role={getattr(scene_obj, 'role_label', '')} "
            f"start={scene_obj.start:.2f} end={scene_obj.end:.2f} duration={d:.2f}"
        )

    return scenes


def _cache_path(url: str) -> Path:
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.mp4"


async def _download_file(url: str, destination: Path, client: httpx.AsyncClient):
    destination.parent.mkdir(parents=True, exist_ok=True)
    cache_path = _cache_path(url)
    if cache_path.exists():
        shutil.copyfile(cache_path, destination)
        return

    response = await client.get(url)
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    if content_type and "video" not in content_type and not str(url).lower().endswith(".mp4"):
        raise RuntimeError("Provided clip URL did not return a video file.")

    cache_path.write_bytes(response.content)
    shutil.copyfile(cache_path, destination)


async def _search_pexels_video(query: str, min_duration: float = 2.0, client: Optional[httpx.AsyncClient] = None) -> Optional[str]:
    # Return cached result if still fresh
    _cached = _pexels_search_cache.get(query)
    if _cached and _time_mod.time() < _cached[0]:
        return _cached[1]

    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return None

    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": 12,
        "orientation": "portrait",
        "size": "small",
    }
    close_client = client is None
    api_client = client or httpx.AsyncClient(timeout=30.0)
    try:
        res = await api_client.get("https://api.pexels.com/v1/videos/search", headers=headers, params=params)
        res.raise_for_status()
        videos = res.json().get("videos", [])
    finally:
        if close_client:
            await api_client.aclose()

    if not videos:
        return None

    candidate = None
    best_score = float("inf")
    target_area = FAST_TARGET_W * FAST_TARGET_H
    query_tokens = _semantic_tokens(query)
    # IMPORTANT: Pexels video search results do not reliably include rich tag text in this payload.
    # A strict token-overlap gate here can accidentally filter *everything* and cause stock-mode failures.
    # Keep default permissive and rely on downstream clip scoring/rejection for relevance.
    strict_relevance = os.getenv("STRICT_SCENE_RELEVANCE", "0") == "1"
    min_overlap = max(0, int(os.getenv("SCENE_RELEVANCE_MIN_OVERLAP", "0")))
    learning_intent = bool(query_tokens.intersection({"learn", "learning", "beginner", "guide", "tutorial", "master", "prompt", "course", "study"}))
    off_topic_tokens = {"traffic", "highway", "city", "road", "car", "street", "bridge", "building", "night", "skyline"}
    # Hard irrelevant rejection (deterministic) using Pexels `video.url` slug tokens.
    scenic_tokens = {"sunset", "beach", "ocean", "palm", "nature", "scenic"}
    animal_tokens = {"dinosaur", "trex", "t-rex", "cat", "dog", "monkey", "wildlife", "zoo", "pet"}
    greenscreen_tokens = {"greenscreen", "green", "screen", "chroma", "chromakey", "key"}
    for video in videos:
        if float(video.get("duration", 0) or 0) < min_duration:
            continue
        meta_blob = " ".join([
            str(video.get("url", "")),
            str((video.get("user") or {}).get("name", "")),
        ])
        meta_tokens = _semantic_tokens(meta_blob)
        if meta_tokens:
            if meta_tokens.intersection(scenic_tokens) and not query_tokens.intersection(scenic_tokens):
                continue
            if meta_tokens.intersection(animal_tokens) and not query_tokens.intersection(animal_tokens):
                continue
            if ("greenscreen" in meta_tokens or ("chroma" in meta_tokens and "key" in meta_tokens)) and not query_tokens.intersection({"greenscreen", "chroma", "chromakey"}):
                continue
        overlap_count = len(query_tokens.intersection(meta_tokens)) if query_tokens and meta_tokens else 0
        if strict_relevance and query_tokens and meta_tokens and overlap_count < min_overlap:
            continue
        off_topic_overlap = len(meta_tokens.intersection(off_topic_tokens)) if meta_tokens else 0
        for vf in video.get("video_files", []):
            if vf.get("file_type") != "video/mp4":
                continue
            width = int(vf.get("width") or 0)
            height = int(vf.get("height") or 0)
            if width == 0 or height == 0:
                continue
            area = width * height
            portrait_penalty = 0 if height >= width else 500000
            size_penalty = abs(area - target_area)
            oversize_penalty = max(0, area - int(target_area * 1.2))
            relevance_bonus = overlap_count * 250000
            intent_penalty = (off_topic_overlap * 180000) if learning_intent else 0
            score = portrait_penalty + size_penalty + oversize_penalty + intent_penalty - relevance_bonus
            if score < best_score:
                best_score = score
                candidate = vf.get("link")

    _pexels_search_cache[query] = (_time_mod.time() + _SEARCH_CACHE_TTL, candidate)
    return candidate


async def _search_pixabay_video(query: str, min_duration: float = 2.0, client: Optional[httpx.AsyncClient] = None) -> Optional[str]:
    _cached = _pixabay_search_cache.get(query)
    if _cached and _time_mod.time() < _cached[0]:
        return _cached[1]

    api_key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not api_key:
        return None

    params = {
        "key": api_key,
        "q": query,
        "per_page": 15,
        "safesearch": "true",
        "order": "popular",
    }
    close_client = client is None
    api_client = client or httpx.AsyncClient(timeout=30.0)
    try:
        res = await api_client.get("https://pixabay.com/api/videos/", params=params)
        res.raise_for_status()
        hits = res.json().get("hits", [])
    finally:
        if close_client:
            await api_client.aclose()

    if not hits:
        return None

    query_tokens = _semantic_tokens(query)
    # Default permissive; downstream clip scoring handles quality/relevance.
    strict_relevance = os.getenv("STRICT_SCENE_RELEVANCE", "0") == "1"
    min_overlap = max(0, int(os.getenv("SCENE_RELEVANCE_MIN_OVERLAP", "0")))

    best_url = None
    best_score = float("inf")
    target_area = FAST_TARGET_W * FAST_TARGET_H
    scenic_tokens = {"sunset", "beach", "ocean", "palm", "nature", "scenic"}
    animal_tokens = {"dinosaur", "trex", "t-rex", "cat", "dog", "monkey", "wildlife", "zoo", "pet"}
    greenscreen_tokens = {"greenscreen", "green", "screen", "chroma", "chromakey", "key"}
    for hit in hits:
        if float(hit.get("duration", 0) or 0) < min_duration:
            continue
        videos = hit.get("videos", {})
        tag_tokens_all = set(re.findall(r"[a-zA-Z]{3,}", str(hit.get("tags", "")).lower()))
        if tag_tokens_all.intersection(scenic_tokens) and not query_tokens.intersection(scenic_tokens):
            continue
        if tag_tokens_all.intersection(animal_tokens) and not query_tokens.intersection(animal_tokens):
            continue
        if ("greenscreen" in tag_tokens_all or ("chroma" in tag_tokens_all and "key" in tag_tokens_all)) and not query_tokens.intersection({"greenscreen", "chroma", "chromakey"}):
            continue
        for key in ("tiny", "small", "medium", "large"):
            v = videos.get(key) or {}
            url = v.get("url")
            if not url:
                continue
            width = int(v.get("width") or 0)
            height = int(v.get("height") or 0)
            if width == 0 or height == 0:
                continue
            area = width * height
            portrait_penalty = 0 if height >= width else 500000
            size_penalty = abs(area - target_area)
            oversize_penalty = max(0, area - int(target_area * 1.2))
            tag_tokens = set(re.findall(r"[a-zA-Z]{4,}", str(hit.get("tags", "")).lower()))
            overlap_count = len(query_tokens.intersection(tag_tokens)) if query_tokens else 0
            if strict_relevance and query_tokens and overlap_count < min_overlap:
                continue
            relevance_bonus = overlap_count * 250000
            score = portrait_penalty + size_penalty + oversize_penalty - relevance_bonus
            if score < best_score:
                best_score = score
                best_url = url

    _pixabay_search_cache[query] = (_time_mod.time() + _SEARCH_CACHE_TTL, best_url)
    return best_url


def get_hybrid_scene_strategy(scenes: List[ScenePlan], available_credits: float) -> Tuple[List[ScenePlan], float]:
    """
    Smart visual-importance-based Runway allocation.

    Each scene is scored heuristically (zero API cost) and assigned the
    optimal RunwayML model:
      hook / score ≥ 8  → gen4.5   (12 cr/5s)
      score 5-7         → gen4_turbo (10 cr/5s)
      score < 5         → stock footage (0 cr)

    Budget is tracked cumulatively; when credits run low the strategy
    transparently falls back to cheaper models then stock.
    """
    from utils.visual_scoring import score_scene_heuristic, select_runway_model

    credits_budget = max(0.0, float(available_credits) * 0.70)
    credits_remaining = credits_budget
    credits_used = 0.0

    for idx, scene in enumerate(scenes):
        duration = max(1.0, float(scene.end - scene.start))

        # Score this scene
        result = score_scene_heuristic(
            scene_text=scene.source_text or scene.subtitle or "",
            scene_type=scene.part,
            scene_index=idx,
        )
        scene.visual_score = result.score

        if result.use_runway:
            model, rate = select_runway_model(
                scene_type=scene.part,
                visual_score=result.score,
                budget_remaining=credits_remaining,
            )
        else:
            model, rate = None, 0

        if model:
            scene_credits = round((duration / 5.0) * rate, 2)
            use_runway = True
            scene.runway_model = model
            reason = f"Score {result.score}/10 → {model} | {result.reasoning}"
        else:
            scene_credits = 0.0
            use_runway = False
            scene.runway_model = None
            reason = f"Score {result.score}/10 → stock | {result.reasoning}"

        scene.use_runway = use_runway
        scene.credits_cost = scene_credits
        scene.allocation_reason = reason
        # Also set enhanced visual_description if scoring produced one
        if result.visual_prompt:
            scene.visual_description = result.visual_prompt

        if use_runway:
            credits_used += scene_credits
            credits_remaining -= scene_credits

    return scenes, round(credits_used, 2)


async def fetch_scene_clips(scenes: List[ScenePlan], run_id: str, mode: str = None, available_credits: float = 750.0, runway_model: str = None, max_scenes: int = None) -> List[ScenePlan]:

    import functools
    import random
    from moviepy.editor import VideoFileClip

    # --- PATCH: Add mode for AI animation (RunwayML) or stock footage ---
    # mode: "stock" (default), "ai" (RunwayML), or "auto" (try AI, fallback to stock)
    if mode is None:
        mode = os.getenv("VIDEO_SCENE_MODE", "stock")
    # Accept both 'auto' and 'hybrid' as hybrid mode
    if mode == 'hybrid':
        mode = 'auto'
    # max_scenes param overrides env (sent by frontend based on scene_mode selection)
    max_ai_scenes = max_scenes if max_scenes is not None else int(os.getenv("RUNWAYML_MAX_SCENES", "2"))  # hard cap for explicit AI mode
    ai_used = 0
    ai_used_lock = asyncio.Lock()

    if mode in ("auto", "hybrid"):
        scenes, est_credits = get_hybrid_scene_strategy(scenes, available_credits)
        planned_ai = sum(1 for s in scenes if s.use_runway)
        print(f"[HYBRID] Strategy: {planned_ai} Runway scenes, est credits: {est_credits}")
    else:
        for scene in scenes:
            scene.use_runway = mode == "ai"
            scene.credits_cost = max(0.0, round(((scene.end - scene.start) / 5.0) * 10.0, 2)) if scene.use_runway else 0.0
            scene.allocation_reason = "FULL AI MODE" if scene.use_runway else "STOCK MODE"

    experimental_mixed_media_enabled = os.getenv("ENABLE_EXPERIMENTAL_MIXED_MEDIA", "0") == "1"
    if mode == "stock":
        print(f"[MIXED_MEDIA] experimental_mixed_media_enabled={'true' if experimental_mixed_media_enabled else 'false'}")

    asset_strategy: Optional[dict[int, dict]] = None
    stock_video_scenes = scenes
    if mode == "stock" and experimental_mixed_media_enabled:
        asset_strategy = _apply_scene_asset_strategy(scenes)
        stock_video_scenes = [
            s
            for s in scenes
            if (asset_strategy.get(int(s.idx), {}) if asset_strategy else {}).get("asset_type", "stock_video") == "stock_video"
        ]
    needs_search = any(not scene.clip_url for scene in stock_video_scenes)
    if needs_search and mode == "stock" and not os.getenv("PEXELS_API_KEY") and not os.getenv("PIXABAY_API_KEY"):
        raise RuntimeError("Set PEXELS_API_KEY or PIXABAY_API_KEY in backend environment.")

    timeout = httpx.Timeout(60.0, connect=10.0)

    import traceback
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        sem = asyncio.Semaphore(1 if mode == "stock" else 4)
        used_clips: set = set()  # Track used clips to avoid duplicates (Batch 2A)
        recent_visual_profiles: List[dict] = []
        # NOTE: No cross-scene clip reuse fallbacks. If a scene cannot find a match, we fail.
        # (Hook must never reuse another scene's clip.)

        async def _is_valid_video(path, scene_part: str = "body"):
            try:
                clip = VideoFileClip(str(path))
                if not hasattr(clip, 'duration') or clip.duration is None or clip.duration <= 0:
                    return False
                try:
                    _ = clip.get_frame(0)
                except Exception:
                    return False
                clip.close()
                part = (scene_part or "body").lower()
                # Stricter brightness floor for hook/cta; looser for body.
                min_luma_default = "32" if part in {"hook", "cta"} else "26"
                min_luma = float(os.getenv("STOCK_MIN_LUMA", min_luma_default))
                sample_luma = _sample_video_luma(Path(path), sample_points=[0.15, 0.35])
                if sample_luma < min_luma:
                    print(f"[FETCH] Rejecting dark clip {path} (luma={sample_luma:.1f} < {min_luma})")
                    return False
                return True
            except Exception:
                print(f"[DEBUG] Exception in _is_valid_video for {path}:")
                traceback.print_exc()
                return False

        async def _fetch_one(scene: ScenePlan):
            nonlocal ai_used
            async with sem:
                duration = max(1.6, scene.end - scene.start)
                ai_out_path = RAW_DIR / f"{run_id}_scene_{scene.idx}_ai.mp4"
                stock_out_path = RAW_DIR / f"{run_id}_scene_{scene.idx}_stock.mp4"
                # --- AI Animation path ---
                should_try_ai = mode == "ai" or (mode in ("auto", "hybrid") and scene.use_runway)
                async with ai_used_lock:
                    can_use_ai = should_try_ai and (mode == "ai" or ai_used < max_ai_scenes)
                    if can_use_ai and mode != "ai":
                        ai_used += 1  # reserve the slot before releasing the lock
                if can_use_ai:
                    try:
                        prompt = scene.visual_description or scene.subtitle or "cinematic animation"
                        # Per-scene model from visual scoring; fall back to request-level override
                        effective_model = scene.runway_model or runway_model
                        try:
                            await asyncio.to_thread(
                                fetch_runwayml_clip, prompt, ai_out_path, int(duration*12), None, "cinematic", effective_model
                            )
                            if mode == "ai":
                                async with ai_used_lock:
                                    ai_used += 1
                            if await _is_valid_video(ai_out_path, scene_part=scene.part):
                                scene.clip_path = str(ai_out_path)
                                print(f"[AI] RunwayML {effective_model} generated for scene {scene.idx} (score={scene.visual_score})")
                                return
                        except RunwayMLQuotaError as e:
                            print(f"[AI] RunwayML quota/credits issue for scene {scene.idx}: {e}. Falling back to stock.")
                        except Exception as e:
                            print(f"[AI] RunwayML failed for scene {scene.idx}: {e}")
                            traceback.print_exc()
                    except Exception as e:
                        print(f"[AI] Error: {e}")
                        traceback.print_exc()

                scene_intent = ""
                scene_asset_type = "stock_video"
                if mode == "stock" and experimental_mixed_media_enabled and asset_strategy is not None:
                    meta = asset_strategy.get(int(scene.idx), {})
                    scene_intent = str(meta.get("intent") or "")
                    scene_asset_type = str(meta.get("asset_type") or "stock_video")
                    print(f"[ASSET] scene={scene.idx} intent={scene_intent} asset_type={scene_asset_type}")

                    if scene_asset_type in {"info_card", "dashboard_mockup", "cta_card"}:
                        try:
                            if scene_asset_type == "info_card":
                                helper = "_render_info_card"
                                path, render_meta = _render_info_card(scene, run_id=run_id)
                            elif scene_asset_type == "dashboard_mockup":
                                helper = "_render_dashboard_mockup"
                                path, render_meta = _render_dashboard_mockup(scene, run_id=run_id)
                            else:
                                helper = "_render_cta_card"
                                path, render_meta = _render_cta_card(scene, run_id=run_id)

                            scene.clip_path = str(path)
                            motion_applied = bool(
                                float(render_meta.get("zoom_end", 1.0)) > float(render_meta.get("zoom_start", 1.0))
                                or int(render_meta.get("pan_px", 0) or 0) != 0
                            )
                            print(f"[ASSET] scene={scene.idx} asset_type={scene_asset_type} helper={helper}")
                            print(
                                "[MOTION] "
                                f"scene={scene.idx} asset_type={scene_asset_type} "
                                f"duration={float(render_meta.get('duration', duration)):.2f} "
                                f"zoom_start={float(render_meta.get('zoom_start', 1.0)):.2f} "
                                f"zoom_end={float(render_meta.get('zoom_end', 1.0)):.2f} "
                                f"pan_px={int(render_meta.get('pan_px', 0) or 0)} "
                                f"motion_applied={motion_applied} "
                                f"ffmpeg_success={bool(render_meta.get('ffmpeg_success'))} "
                                f"fallback_used={bool(render_meta.get('fallback_used'))}"
                            )
                            return
                        except Exception as e:
                            print(f"[ASSET] Render failed for scene {scene.idx} asset_type={scene_asset_type}: {e} (falling back to stock_video)")
                            traceback.print_exc()
                            scene_asset_type = "stock_video"
                # --- Stock footage fallback (Batch 2A: improved query logic) ---
                if scene.clip_url:
                    try:
                        await _download_file(scene.clip_url, stock_out_path, client=client)
                        if await _is_valid_video(stock_out_path, scene_part=scene.part):
                            scene.clip_path = str(stock_out_path)
                            if mode == "stock":
                                print(f"[ASSET] scene={scene.idx} asset_type=stock_video source=clip_url")
                            return
                        else:
                            print(f"[FETCH] Invalid/corrupt video from clip_url for scene {scene.idx}, retrying search...")
                    except Exception as e:
                        print(f"[FETCH] Download failed for clip_url scene {scene.idx}: {e}")
                        traceback.print_exc()
                
                # Batch 2A: Try query candidates sequentially with scoring
                candidates = _scene_query_candidates(scene)
                # Strict hook fallback order (approved): add strong hook queries + safe hook query,
                # and if still no match -> fail hook (no reuse).
                if scene.part == "hook":
                    extended = list(candidates)
                    for q in _hook_fallback_queries():
                        if q not in extended:
                            extended.append(q)
                    safe_q = "person surprised reaction close up"
                    if safe_q not in extended:
                        extended.append(safe_q)
                    candidates = extended[:8]
                rejected_clips = []
                winning_query = ""
                matched_concepts = _match_concept_families(scene)
                
                for query in candidates:
                    url_pexels = await _search_pexels_video(query, duration, client=client)
                    url_pixabay = await _search_pixabay_video(query, duration, client=client)

                    # Try both sources deterministically per query. This avoids a common failure mode where
                    # Pexels returns a duplicate/low-score clip and we never consider the Pixabay alternative.
                    for source, url in (("pexels", url_pexels), ("pixabay", url_pixabay)):
                        if not url:
                            continue
                        try:
                            # Extract clip title from URL for logging
                            clip_title = url.split("/")[-1][:80] if "/" in url else "unknown"

                            # Score this clip (Batch 2A)
                            score, rejection = _score_clip_quality_for_scene(
                                clip_title,
                                clip_source=source,
                                scene_part=scene.part,
                                query=query,
                                role_label=str(getattr(scene, "role_label", "") or ""),
                                used_clips=used_clips,
                                recent_visual_profiles=list(recent_visual_profiles),
                                matched_concepts=matched_concepts,
                            )

                            if rejection:
                                rejected_clips.append((clip_title, rejection))
                                continue

                            # Clip accepted - try to download
                            await _download_file(url, stock_out_path, client=client)
                            if await _is_valid_video(stock_out_path, scene_part=scene.part):
                                clip_id = f"{source}:{clip_title}"
                                used_clips.add(clip_id)
                                winning_profile = _build_visual_profile(
                                    scene=scene,
                                    query=query,
                                    clip_title=clip_title,
                                    clip_source=source,
                                    matched_concepts=matched_concepts,
                                )
                                recent_visual_profiles.insert(0, winning_profile)
                                recent_visual_profiles[:] = recent_visual_profiles[:2]
                                winning_query = query
                                scene.clip_path = str(stock_out_path)
                                print(
                                    f"[VISUAL_FAMILY] scene={scene.idx} "
                                    f"archetype={winning_profile.get('archetype')} "
                                    f"environment_family={winning_profile.get('environment_family')} "
                                    f"winning_query=\"{winning_query}\""
                                )

                                if mode == "stock":
                                    if experimental_mixed_media_enabled and asset_strategy is not None:
                                        intent_label = scene_intent or asset_strategy.get(int(scene.idx), {}).get("intent", "")
                                        print(
                                            f"[ASSET] scene={scene.idx} intent={intent_label} "
                                            f"asset_type=stock_video winning_query='{winning_query}'"
                                        )
                                    else:
                                        print(
                                            f"[ASSET] scene={scene.idx} "
                                            f"asset_type=stock_video winning_query='{winning_query}'"
                                        )

                                _log_scene_query_process(
                                    scene_idx=scene.idx,
                                    scene_part=scene.part,
                                    candidates=candidates,
                                    winning_query=winning_query,
                                    winning_clip_source=source,
                                    winning_clip_title=clip_title,
                                    winning_profile=winning_profile,
                                    rejected_clips=rejected_clips,
                                )
                                return
                            else:
                                print(
                                    f"[FETCH] Invalid/corrupt video from {source} query '{query}' "
                                    f"for scene {scene.idx}, trying next..."
                                )
                        except Exception as e:
                            print(f"[FETCH] Download failed for {source} query '{query}' scene {scene.idx}: {e}")
                            traceback.print_exc()
                
                print(f"[FETCH] No valid video found for scene {scene.idx}")

        try:
            if mode == "stock":
                # Deterministic visual diversity scoring depends on the previously accepted scenes.
                # Run stock fetches in order so "adjacent repeat" checks reflect real scene order.
                for scene in scenes:
                    await _fetch_one(scene)
            else:
                await asyncio.gather(*[_fetch_one(scene) for scene in scenes])
        except Exception as e:
            print(f"[FETCH] Exception during scene clip fetching: {e}")
            traceback.print_exc()
            raise

    missing = [scene for scene in scenes if not scene.clip_path]
    if missing:
        missing_details = []
        for scene in missing:
            candidate_queries = _scene_query_candidates(scene)
            missing_details.append(
                " | ".join([
                    f"scene={scene.idx}",
                    f"part={scene.part}",
                    f"subtitle={repr((scene.subtitle or '')[:120])}",
                    f"visual={repr((scene.visual_description or '')[:160])}",
                    f"queries={candidate_queries}",
                ])
            )
        detail_text = "; ".join(missing_details)
        print(f"[FETCH] Explicit stock search failure: {detail_text}")
        if len(missing) == len(scenes):
            raise RuntimeError("No matching stock clips found for any scene. Try broader wording or stronger visuals.")
        raise RuntimeError("Failed to find relevant stock clip(s): " + ", ".join(str(scene.idx) for scene in missing))

    return scenes


def _fit_vertical(clip: VideoFileClip, target_w: int = FAST_TARGET_W, target_h: int = FAST_TARGET_H) -> VideoFileClip:
    scale = max(target_w / clip.w, target_h / clip.h)
    resized = clip.resize(scale)
    x1 = (resized.w - target_w) / 2
    y1 = (resized.h - target_h) / 2
    return resized.crop(x1=x1, y1=y1, x2=x1 + target_w, y2=y1 + target_h)


def _srt_timestamp(sec: float) -> str:
    sec = max(0, float(sec))
    h = int(sec // 3600)
    sec %= 3600
    m = int(sec // 60)
    sec %= 60
    s = int(sec)
    ms = int(round((sec - s) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _write_ass(scenes: List[ScenePlan], path: Path, audio_path: Optional[str] = None):
    """Generate MrBeast/TikTok-style ASS captions from scene list."""
    try:
        from utils.caption_generator import generate_ass_from_scenes, _ASS_STYLE  # type: ignore
    except Exception:
        # When invoked from repo root (e.g. scripts/tests), the module path is backend.utils.*
        from backend.utils.caption_generator import generate_ass_from_scenes, _ASS_STYLE  # type: ignore
    content = generate_ass_from_scenes(scenes, audio_path=audio_path)

    dialogue_count = content.count("Dialogue:")
    if dialogue_count <= 0:
        allow_placeholder = os.getenv("ALLOW_RENDER_WITHOUT_CAPTIONS", "0") == "1"
        if not allow_placeholder:
            raise RuntimeError("Caption generation produced 0 Dialogue lines (refusing to render without captions).")
        print(f"[CAPTION] WARNING: No captions generated for {len(scenes)} scenes (writing placeholder).")
        content = f"""[Script Info]
Title: Threadforge Dynamic Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
{_ASS_STYLE}

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,CAPTIONS UNAVAILABLE
"""

    path.write_text(content, encoding="utf-8")
    print(f"[CAPTION] Generated ASS file with {dialogue_count} caption lines")


def _mean_luma_from_frame(frame) -> float:
    try:
        from PIL import Image, ImageStat
        return float(ImageStat.Stat(Image.fromarray(frame).convert("L")).mean[0])
    except Exception:
        return 255.0


def _sample_video_luma(path: Path, sample_points: Optional[list[float]] = None) -> float:
    points = sample_points or [0.15, 0.35, 0.55]
    try:
        clip = VideoFileClip(str(path))
        duration = max(0.2, float(clip.duration or 0.2))
        values: list[float] = []
        for p in points:
            t = min(max(0.0, duration * float(p)), max(0.0, duration - 0.05))
            values.append(_mean_luma_from_frame(clip.get_frame(t)))
        clip.close()
        return float(sum(values) / max(1, len(values)))
    except Exception:
        return 255.0


def _enhance_dark_image(img):
    from PIL import ImageEnhance
    boosted = ImageEnhance.Brightness(img).enhance(1.45)
    return ImageEnhance.Contrast(boosted).enhance(1.25)


def _generate_hf_thumbnail_background(title_text: str, width: int, height: int):
    hf_token = (os.getenv("HF_TOKEN") or "").strip()
    if not hf_token:
        return None

    model = os.getenv("HF_THUMBNAIL_MODEL", os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell"))
    api_url = f"https://router.huggingface.co/hf-inference/models/{model}"
    prompt = (
        "Cinematic vertical social media thumbnail background, bright and high contrast, "
        "clean composition, focal subject area, no logos, no watermark, no readable text. "
        f"Topic: {(title_text or '').strip()}"
    )
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": int(width),
            "height": int(height),
            "num_inference_steps": 4,
            "guidance_scale": 0.0,
        },
    }
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
        "Accept": "image/png",
    }
    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(api_url, headers=headers, json=payload)
        if resp.status_code == 200:
            from io import BytesIO
            from PIL import Image
            return Image.open(BytesIO(resp.content)).convert("RGB")
        print(f"[THUMBNAIL] HF background unavailable (HTTP {resp.status_code})")
        return None
    except Exception as exc:
        print(f"[THUMBNAIL] HF background generation failed: {exc}")
        return None


def _subtitle_filter(caption_path: Path) -> str:
    """Return ffmpeg -vf filter string. Supports both .ass and .srt."""
    cap_str = str(caption_path).replace('\\', '/')
    cap_str = cap_str.replace("'", "\\'")
    # Windows drive letters include ":" which ffmpeg parses as an option separator in filters.
    # Escape it so paths like C:/... work reliably.
    if re.match(r"^[A-Za-z]:/", cap_str):
        cap_str = cap_str.replace(":", "\\:")
    if str(caption_path).lower().endswith(".ass"):
        return f"ass='{cap_str}'"
    return (
        "subtitles='" + cap_str + "'"
        ":force_style='FontName=Arial,Bold=-1,FontSize=24,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,Outline=5,Shadow=1,Alignment=2,MarginV=60'"
    )


def render_thumbnail(video_path: str, title_text: str, output_path: str = None) -> str:
    """Overlay bold title text on a thumbnail frame in PORTRAIT aspect ratio 1080×1920.
    Uses Pillow only — zero API credits consumed.
    Reuses the existing raw thumbnail JPG if it already exists,
    otherwise extracts a fresh frame from the video.
    """
    from PIL import Image, ImageDraw, ImageFont

    if not output_path:
        output_path = str(video_path).replace(".mp4", ".jpg")

    # Prefer loading the existing raw thumbnail (faster than re-reading video)
    img = None
    if os.path.exists(output_path):
        try:
            img = Image.open(output_path).convert("RGB")
        except Exception:
            img = None

    if img is None:
        try:
            from moviepy.editor import VideoFileClip as _VFC
            clip = _VFC(str(video_path))
            # Prefer a later frame to avoid intro overlays/captions being captured mid-word.
            t = min(max(0.0, clip.duration * 0.35), max(0.0, clip.duration - 0.1))
            frame = clip.get_frame(t)
            clip.close()
            img = Image.fromarray(frame)
        except Exception as e:
            print(f"[THUMBNAIL] Frame extract failed, using black bg: {e}")
            img = Image.new("RGB", (1080, 1920), (0, 0, 0))
    
    # CRITICAL: Ensure thumbnail is always portrait 1080×1920 for vertical shorts
    w, h = img.size
    if w > h:  # Landscape detected, rotate or resize to portrait
        # Resize to portrait, maintaining width priority (1080 is standard short width)
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
    elif (w, h) != (1080, 1920):  # Not exactly portrait 1080×1920, normalize
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)

    # If frame is too dark, try HF-generated thumbnail background; fallback to local enhancement.
    from PIL import ImageStat
    min_luma = float(os.getenv("THUMBNAIL_MIN_LUMA", "24"))
    luma = float(ImageStat.Stat(img.convert("L")).mean[0])
    if luma < min_luma:
        hf_bg = _generate_hf_thumbnail_background(title_text=title_text, width=1080, height=1920)
        if hf_bg is not None:
            img = hf_bg.resize((1080, 1920), Image.Resampling.LANCZOS)
            luma = float(ImageStat.Stat(img.convert("L")).mean[0])
            print(f"[THUMBNAIL] Replaced dark frame with HF background (luma={luma:.1f})")
        else:
            img = _enhance_dark_image(img)
            luma = float(ImageStat.Stat(img.convert("L")).mean[0])
            print(f"[THUMBNAIL] Enhanced dark frame locally (luma={luma:.1f})")

    width, height = img.size
    title_text = (title_text or "").upper().strip()
    if not title_text:
        img.save(output_path, "JPEG", quality=90)
        return output_path

    # Font selection — Impact > Arial Black > Arial Bold (Windows paths)
    font_size = max(44, width // 10)
    font = None
    for fp in [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/verdanab.ttf",
    ]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                pass
    if font is None:
        try:
            font = ImageFont.load_default()
        except Exception:
            pass

    # Word-wrap to 88% of image width
    draw_tmp = ImageDraw.Draw(img)
    max_text_w = int(width * 0.88)
    words = title_text.split()
    lines: list = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        try:
            bbox = draw_tmp.textbbox((0, 0), test, font=font)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(test) * (font_size // 2)
        if tw <= max_text_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    lines = lines[:3]

    line_height = int(font_size * 1.28)
    total_h = len(lines) * line_height
    # Keep more safe area from the bottom so platform UI does not clip headline text.
    y_start = height - total_h - int(height * 0.14)

    # Dark gradient overlay on lower area for text legibility
    overlay_top = max(0, y_start - int(font_size * 0.6))
    overlay_h = height - overlay_top
    overlay = Image.new("RGBA", (width, overlay_h), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for row in range(overlay_h):
        alpha = int(200 * (row / max(1, overlay_h)))
        ov_draw.line([(0, row), (width - 1, row)], fill=(0, 0, 0, alpha))
    img_rgba = img.convert("RGBA")
    img_rgba.paste(overlay, (0, overlay_top), overlay)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Draw text with thick black stroke then white fill
    stroke_w = max(3, font_size // 12)
    for i, line in enumerate(lines):
        y = y_start + i * line_height
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(line) * (font_size // 2)
        x = (width - tw) // 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill=(255, 255, 255),
            stroke_width=stroke_w,
            stroke_fill=(0, 0, 0),
        )

    img.save(output_path, "JPEG", quality=92)
    print(f"[THUMBNAIL] Styled thumbnail saved: {output_path}")
    return output_path


from moviepy.editor import AudioFileClip

def assemble_video(scenes: List[ScenePlan], run_id: str, fps: int = 30, audio_path: str = None) -> Dict[str, str]:
    ass_path = TEMP_DIR / f"{run_id}.ass"
    final_path = ASSETS_DIR / f"{run_id}.mp4"


    # --- Robust error handling for video clips ---
    clips = []
    invalid_clips = []
    print("[VIDEO] Scene clip paths:")

    import traceback
    for scene in scenes:
        scene_duration = max(1.2, float(scene.end - scene.start))
        src = scene.clip_path
        print(f"  Scene {scene.idx}: {src}")
        if not src or not Path(src).exists():
            invalid_clips.append((scene.idx, src))
            continue

        try:
            clip = VideoFileClip(src)
            # Validate video: check duration and try to get a frame
            if not hasattr(clip, 'duration') or clip.duration is None or clip.duration <= 0:
                print(f"[VIDEO] Invalid video (no duration) for scene {scene.idx}: {src}")
                invalid_clips.append((scene.idx, src))
                continue
            try:
                _ = clip.get_frame(0)
            except Exception as frame_exc:
                print(f"[VIDEO] Invalid/corrupt video (cannot read frame) for scene {scene.idx}: {src} ({frame_exc})")
                traceback.print_exc()
                invalid_clips.append((scene.idx, src))
                continue
        except Exception as e:
            print(f"[VIDEO] Failed to load video for scene {scene.idx}: {src} ({e})")
            traceback.print_exc()
            invalid_clips.append((scene.idx, src))
            continue

        available_headroom = max(0.0, clip.duration - scene_duration)
        start_offset = 0.0
        if available_headroom > 0.2:
            pattern_seed = (scene.idx * 0.87) + (scene.start * 0.13)
            start_offset = min(available_headroom, pattern_seed % available_headroom)

        if clip.duration < scene_duration:
            # Use MoviePy loop effect to avoid reusing/closing the same clip object,
            # which can invalidate reader state during final render.
            clip = clip.fx(vfx.loop, duration=scene_duration)
        else:
            clip = clip.subclip(start_offset, start_offset + scene_duration)

        clip = _fit_vertical(clip)
        # Normalize scene exposure to keep visual tone consistent across stitched stock clips.
        try:
            luma = _mean_luma_from_frame(clip.get_frame(min(max(0.0, clip.duration * 0.35), max(0.0, clip.duration - 0.05))))
            if luma < 55:
                clip = clip.fx(vfx.colorx, 1.32)
            elif luma < 75:
                clip = clip.fx(vfx.colorx, 1.18)
            elif luma > 190:
                clip = clip.fx(vfx.colorx, 0.92)
        except Exception:
            pass
        is_rendered_card = False
        try:
            name = Path(src).name.lower()
            is_rendered_card = any(tag in name for tag in ["_info.mp4", "_dash.mp4", "_cta.mp4"])
        except Exception:
            is_rendered_card = False

        if not FAST_DISABLE_EFFECTS and (scene.idx % 2 == 0) and not is_rendered_card:
            clip = clip.fx(vfx.resize, lambda t: 1 + 0.02 * (t / max(0.01, clip.duration)))
        if not FAST_DISABLE_EFFECTS:
            fade_d = min(0.12, max(0.0, clip.duration * 0.25))
            if fade_d > 0.01:
                clip = clip.fadein(fade_d).fadeout(fade_d)
        clips.append(clip)

    if invalid_clips:
        print(f"[VIDEO] Invalid or missing video clips: {invalid_clips}")
    if not clips:
        raise RuntimeError(f"Failed to assemble video: no valid source clips. Invalid clips: {invalid_clips}")

    _write_ass(scenes, ass_path, audio_path=audio_path)

    # Use stronger encoding profile when dark scenes dominate to reduce muddy compression.
    dark_scene_count = 0
    sampled = 0
    dark_cutoff = float(os.getenv("VIDEO_DARK_SCENE_LUMA", "28"))
    for scene in scenes[:4]:
        src = getattr(scene, "clip_path", None)
        if src and Path(src).exists():
            sampled += 1
            if _sample_video_luma(Path(src), sample_points=[0.2, 0.45]) < dark_cutoff:
                dark_scene_count += 1

    dark_ratio = (dark_scene_count / sampled) if sampled else 0.0
    tutorial_terms = {"learn", "learning", "beginner", "guide", "tutorial", "master", "day", "days", "prompt", "course"}
    script_tokens = _semantic_tokens(" ".join([(getattr(s, "source_text", "") or "") for s in scenes]))
    tutorial_mode = bool(script_tokens.intersection(tutorial_terms))
    chosen_crf = "19" if tutorial_mode else ("20" if dark_ratio >= 0.4 else "22")
    chosen_bitrate = "3200k" if tutorial_mode else ("2600k" if dark_ratio >= 0.4 else "2200k")
    print(f"[VIDEO] Quality profile dark_ratio={dark_ratio:.2f}, crf={chosen_crf}, bitrate={chosen_bitrate}")

    render_fps = max(24, min(60, int(fps or 30)))
    final = concatenate_videoclips(clips, method="compose").set_fps(render_fps)
    ffmpeg_error = None
    audio_clip = None
    temp_audiofile = None
    # Add audio if provided
    if audio_path and Path(audio_path).exists():
        try:
            size = Path(audio_path).stat().st_size
            print(f"[AUDIO] Merging audio: {audio_path} ({size} bytes)")
            audio_clip = AudioFileClip(audio_path)
            final = final.set_audio(audio_clip)
            temp_audiofile = str((TEMP_DIR / f"{run_id}_audio.m4a").resolve())
        except Exception as e:
            ffmpeg_error = f"Audio merge failed: {e}"
            print(f"[AUDIO] Audio merge failed: {e}")
    try:
        final.write_videofile(
            str(final_path),
            codec="libx264",
            bitrate=chosen_bitrate,
            audio=True if audio_path and Path(audio_path).exists() else False,
            audio_codec="aac",
            audio_bitrate="192k",
            audio_fps=44100,
            temp_audiofile=temp_audiofile,
            remove_temp=True,
            fps=render_fps,
            threads=max(2, os.cpu_count() or 4),
            ffmpeg_params=[
                "-preset", "veryfast",
                "-crf", chosen_crf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-vf", _subtitle_filter(ass_path),
            ],
            logger=None,
        )
    except Exception as exc:
        ffmpeg_error = str(exc)
        allow_no_captions = os.getenv("ALLOW_RENDER_WITHOUT_CAPTIONS", "0") == "1"
        if not allow_no_captions:
            raise RuntimeError(f"Subtitle burn failed (refusing to render without captions): {ffmpeg_error}")
        final.write_videofile(
            str(final_path),
            codec="libx264",
            bitrate=chosen_bitrate,
            audio=True if audio_path and Path(audio_path).exists() else False,
            audio_codec="aac",
            audio_bitrate="192k",
            audio_fps=44100,
            temp_audiofile=temp_audiofile,
            remove_temp=True,
            fps=render_fps,
            threads=max(2, os.cpu_count() or 4),
            ffmpeg_params=[
                "-preset", "veryfast",
                "-crf", chosen_crf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
            ],
            logger=None,
        )
    # --- Generate thumbnail from first source clip when possible (avoid burned caption artifacts) ---
    thumbnail_path = str(final_path).replace('.mp4', '.jpg')
    try:
        thumb_source = str(final_path)
        first_clip_path = next((s.clip_path for s in scenes if getattr(s, "clip_path", None) and Path(s.clip_path).exists()), None)
        if first_clip_path:
            thumb_source = str(first_clip_path)

        thumb_clip = VideoFileClip(thumb_source)
        # Use a later frame to reduce chance of transitional overlays.
        t = min(max(0.0, thumb_clip.duration * 0.35), max(0.0, thumb_clip.duration - 0.1))
        frame = thumb_clip.get_frame(t)
        from PIL import Image
        im = Image.fromarray(frame)
        # CRITICAL: Ensure portrait aspect ratio 1080×1920 for shorts
        w, h = im.size
        if w > h:  # Landscape detected
            im = im.resize((1080, 1920), Image.Resampling.LANCZOS)
        elif (w, h) != (1080, 1920):
            im = im.resize((1080, 1920), Image.Resampling.LANCZOS)
        im.save(thumbnail_path, "JPEG", quality=92)
        thumb_clip.close()
        print(f"[THUMBNAIL] Saved portrait thumbnail (1080×1920) from {thumb_source}: {thumbnail_path}")
    except Exception as e:
        print(f"[THUMBNAIL] Failed to generate thumbnail: {e}")
        thumbnail_path = None
    finally:
        final.close()
        if audio_clip is not None:
            try:
                audio_clip.close()
            except Exception:
                pass
        for c in clips:
            c.close()

    return {
        "video_path": str(final_path),
        "subtitle_path": str(ass_path),
        "thumbnail_path": thumbnail_path,
        "ffmpeg_error": ffmpeg_error,
    }


def make_scene_response(scenes: List[ScenePlan]) -> List[Dict]:
    rows = []
    for scene in scenes:
        rows.append({
            "scene": scene.idx,
            "start": scene.start,
            "end": scene.end,
            "part": scene.part,
            # Spoken script (caption + narration alignment). Must remain immutable after planning.
            "source_text": _clean_text(scene.source_text or scene.subtitle),
            "subtitle": _clean_text(scene.subtitle or scene.source_text),
            "visual_description": scene.visual_description,
            "keywords": scene.keywords,
            # Display-only (never used as a subtitle fallback).
            "on_screen_text": _clean_text(getattr(scene, "on_screen_text", "") or scene.subtitle),
            "energy": scene.energy,
            "clip_url": scene.clip_url,
            "use_runway": bool(scene.use_runway),
            "credits_cost": float(scene.credits_cost or 0.0),
            "reason": scene.allocation_reason,
        })
    return rows


def new_run_id() -> str:
    return f"vid_{uuid.uuid4().hex[:12]}"
