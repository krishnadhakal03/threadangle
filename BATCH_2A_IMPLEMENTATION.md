# BATCH 2A: Exact Implementation Plan
## Minimal, Debuggable Changes to Stock Footage Query Logic

---

## FILE: `backend/utils/video_pipeline.py`

### CHANGE 1: Add Hook Query Templates (after imports, before _VISUAL_KEYWORD_MAP)

**Location:** Line 52 (after STOPWORDS definition, before `_VISUAL_KEYWORD_MAP`)

**Insert:**
```python
# ── Hook-specific query templates (Batch 2A) ────────────────────────────────
# For hook scenes: prioritize high-impact, emotional visuals that stop scrolling
_HOOK_QUERY_TEMPLATES = [
    "person shocked surprised reaction face",  # Shock/surprise (primary)
    "frustrated stressed person work",          # Frustration/struggle
    "urgent dramatic moment person",            # Urgency/momentum
]

# ── Rejection rules for weak clips ─────────────────────────────────────────
_WEAK_CLIP_KEYWORDS = {
    # Generic neutral (OK for body, reject for hook)
    "office", "professional", "desk", "business meeting",
    "calm", "peaceful", "serene", "relaxing",
    # Abstract/non-visual (reject for all)
    "abstract", "animation", "graphic", "text",
    # Too dark (reject for hook)
    "dark", "night", "shadow", "low light",
}
```

---

### CHANGE 2: Rewrite `_scene_query_candidates()` Function

**Location:** Lines 375-420

**Replace entire function with:**

```python
def _scene_query_candidates(scene: ScenePlan) -> List[str]:
    """
    Build a prioritised list (3-4 only) of stock-footage search queries for a scene.
    
    Hook scenes: use high-impact emotional templates
    Other scenes: base + contextual + fallback (3 queries max)
    
    Batch 2A: Minimal, well-logged approach.
    """
    candidates: List[str] = []
    
    # ──────────────────────────────────────────────────────────────────────────
    # HOOK SCENES: special high-impact templates
    # ──────────────────────────────────────────────────────────────────────────
    if scene.part == "hook":
        # Start with high-impact templates
        candidates.extend(_HOOK_QUERY_TEMPLATES)
        
        # Add ONE contextual variant from subtitle/visual desc
        context_words = _extract_meaningful_words(
            f"{scene.source_text or ''} {scene.visual_description or ''}"
        )
        if context_words:
            # Contextual variant: emotion + content idea
            contextual = " ".join(context_words[:3])
            if contextual and contextual not in candidates:
                candidates.append(f"{contextual} person reaction")
        
        # Cap hook candidates at 4
        candidates = candidates[:4]
        
    # ──────────────────────────────────────────────────────────────────────────
    # BODY & CTA SCENES: base + contextual + fallback
    # ──────────────────────────────────────────────────────────────────────────
    else:
        # Step 1: Base query from mapped keywords
        raw_keywords = _extract_keywords(scene.source_text or "", 
                                         fallback=scene.keywords or [])
        mapped_phrases: List[str] = []
        
        _LOW_SIGNAL_VISUAL_TERMS = {
            "dark", "black", "night", "shadow", "silhouette", "background", "gradient",
            "animation", "graphics", "symbol", "symbols", "neon", "overlay", "text",
        }
        
        for kw in raw_keywords:
            if kw.lower() in _LOW_SIGNAL_VISUAL_TERMS:
                continue
            phrase = _VISUAL_KEYWORD_MAP.get(kw.lower())
            if phrase:
                mapped_phrases.append(phrase)
        
        # Best base query: combine top mapped phrase(s)
        if mapped_phrases:
            base_query = mapped_phrases[0]  # Use strongest mapped phrase
            candidates.append(base_query)
        
        # Step 2: Contextual variant from visual_description tokens
        vd_tokens = _visual_description_tokens(scene.visual_description or "")
        if vd_tokens:
            candidates.append(vd_tokens)
        
        # Step 3: Part-aware fallback
        part_fallbacks = {
            "body": "person working office professional",
            "cta": "person celebration success achievement",
        }
        fallback = part_fallbacks.get(scene.part, "professional person concept")
        candidates.append(fallback)
        
        # Cap non-hook candidates at 3
        candidates = candidates[:3]
    
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


def _extract_meaningful_words(text: str, max_words: int = 5) -> List[str]:
    """Extract meaningful keywords from text (skip stopwords)"""
    if not text:
        return []
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return [w for w in words if w not in STOPWORDS][:max_words]


def _visual_description_tokens(visual_desc: str) -> str:
    """Extract meaningful tokens from visual description (Batch 2A: simplified)"""
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
```

---

### CHANGE 3: Add Clip Quality Scorer

**Location:** After `_scene_query_candidates()` function (new helper)

**Insert:**
```python
def _score_clip_quality_for_scene(
    clip_title: str,
    clip_source: str,
    scene_part: str,
    used_clips: set = None,
) -> Tuple[float, str]:
    """
    Simple clip quality scorer for stock footage.
    
    Returns: (score: 0-100, rejection_reason: "" if accepted)
    
    Batch 2A: Minimal scoring rules
    - Penalize duplicates (same source/title)
    - Penalize weak/generic clips for hooks
    - Prefer people, action, close-ups for hooks
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
        # REJECT: Generic neutral clips
        if any(weak in title_lower for weak in _WEAK_CLIP_KEYWORDS):
            # Exception: allow "person" and "reaction" for hooks
            if "person" in title_lower or "reaction" in title_lower:
                score += 10  # boost if it has emotional hint
            else:
                return 0.0, "GENERIC_NEUTRAL_FOR_HOOK"
        
        # BOOST: Emotional/reaction clips
        emotional = ["shocked", "surprised", "frustrated", "stressed", "reaction", 
                    "emotion", "dramatic", "urgent"]
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
    if any(abstract in title_lower for abstract in ["abstract", "graphic", "animation"]):
        score -= 25
    
    # Cap score
    score = max(0.0, min(100.0, score))
    
    return score, rejection
```

---

### CHANGE 4: Add Logging Helper

**Location:** After scoring function (new helper)

**Insert:**
```python
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
```

---

## FILE: `backend/utils/video_pipeline.py`

### CHANGE 5: Update `fetch_scene_clips()` Main Function

**Location:** The main orchestration function (around line 800-900)

**Modify the inner loop that calls `_search_pexels_pixabay()` to:**

```python
async def fetch_scene_clips(
    scenes: List[ScenePlan],
    run_id: str,
    mode: str = "stock",
    available_credits: float = 750.0,
    runway_model: str = "gen4_turbo",
    max_scenes: int = 0,
) -> List[ScenePlan]:
    """
    Fetch stock/AI clips for scenes with improved query logic (Batch 2A).
    """
    # ... existing setup code ...
    
    used_clips: set = set()  # Track used clips to avoid duplicates
    rejected_log: dict = {}  # Track rejections per scene
    
    for scene in scenes:
        if scene.use_runway:
            # AI mode: keep existing logic
            scene.clip_url = await fetch_runwayml_clip(scene, run_id)
        else:
            # STOCK MODE (Batch 2A improvements)
            
            # Step 1: Get query candidates
            candidates = _scene_query_candidates(scene)
            
            # Step 2: Try each candidate in order until one succeeds
            best_clip = None
            rejected_clips = []
            
            for query in candidates:
                # Search with this query
                clip_result = await _search_pexels_pixabay(
                    client, query, scene.part, run_id
                )
                
                if clip_result and clip_result.get("clip_url"):
                    # Score this clip
                    score, rejection = _score_clip_quality_for_scene(
                        clip_result.get("title", "unknown"),
                        clip_result.get("source", "unknown"),
                        scene.part,
                        used_clips=used_clips,
                    )
                    
                    if rejection:
                        # Rejected this clip
                        rejected_clips.append((
                            clip_result.get("title", "unknown"),
                            rejection
                        ))
                    else:
                        # Accepted! Use this one
                        best_clip = clip_result
                        clip_id = f"{clip_result['source']}:{clip_result.get('title', 'unknown')}"
                        used_clips.add(clip_id)
                        break
            
            if best_clip:
                scene.clip_url = best_clip["clip_url"]
                
                # Log the selection process
                _log_scene_query_process(
                    scene_idx=scene.idx,
                    scene_part=scene.part,
                    candidates=candidates,
                    winning_query=query,
                    winning_clip_source=best_clip.get("source", "unknown"),
                    winning_clip_title=best_clip.get("title", "unknown"),
                    rejected_clips=rejected_clips,
                )
            else:
                raise RuntimeError(
                    f"[SCENE {scene.idx}] No valid clip found for candidates: {candidates}"
                )
    
    return scenes
```

---

## SUMMARY: What Changed

### New Constants:
- `_HOOK_QUERY_TEMPLATES` - 3 high-impact queries
- `_WEAK_CLIP_KEYWORDS` - Keywords to penalize

### New Functions:
- `_extract_meaningful_words()` - Simple keyword extraction
- `_visual_description_tokens()` - Extract tokens from Claude description
- `_score_clip_quality_for_scene()` - Simple 0-100 scoring with rejection rules
- `_log_scene_query_process()` - Debug logging per scene

### Modified Functions:
- `_scene_query_candidates()` - Now: hook templates + 3-4 total, not 6-8
- `fetch_scene_clips()` - Now: tries candidates in order, scores results, logs decisions

### Impact:
- ✅ Hook scenes get special emotional queries
- ✅ Only 3-4 candidates tried (fast, debuggable)
- ✅ Simple rejection rules (duplicates, generic content)
- ✅ Full logging of selection process
- ✅ No complex intent engine or parallel fanout
- ✅ Deterministic, easy to debug

