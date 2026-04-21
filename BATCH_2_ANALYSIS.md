# Batch 2: Footage Intelligence Upgrade
## Analysis & Design Doc

---

## 1. CURRENT QUERY GENERATION LOGIC

### Location: `backend/utils/video_pipeline.py` → `_scene_query_candidates()`

#### Current Process (3-step priority):

```python
# STEP 1: Script Keywords → Mapped Phrases
# Uses _VISUAL_KEYWORD_MAP (165 keywords)
# Example mappings:
#   "money"      → "cash money wallet dollar"
#   "mistake"    → "mistake failure problem stress"
#   "hack"       → "productivity life hack solution"

raw_keywords = _extract_keywords(scene.source_text)
for kw in raw_keywords:
    phrase = _VISUAL_KEYWORD_MAP.get(kw.lower())  # literal keyword matching
    if phrase:
        mapped_phrases.append(phrase)

# STEP 2: Visual Description Tokens
# Extracts 4+ letter words from Claude's visual_description
# Filters out template boilerplate ("cinematic", "symbolic", etc.)
vd_tokens = [w for w in visual_description.lower().split() 
             if len(w) > 4 and w not in TEMPLATE_NOISE]
vd_query = " ".join(vd_tokens[:5])

# STEP 3: Part-Aware Fallback Queries
# Generic queries per scene type
part_fallbacks = {
    "hook": ["dramatic cinematic person close up", 
             "shocked surprised person reaction"],
    "body": ["professional person working office",
             "explainer business concept desk"],
    "cta": ["success achievement celebration person",
            "goal accomplished happy growth"],
}

# FINAL: Build candidate list (max 6 queries)
candidates = [
    combined_mapped,       # top 2 mapped phrases joined
    *mapped_phrases[:3],   # individual mapped fallbacks
    vd_query,             # visual description tokens
    unmapped_terms,       # any keywords without mappings
    *part_fallbacks,      # part-aware generic queries
]
```

#### Limitations:

❌ **Purely literal keyword matching** — doesn't understand intent  
❌ **No emotion/context focus** — uses generic stock terminology  
❌ **Hook scenes get same fallbacks as body** — "dramatic cinematic close up" is too vague  
❌ **Single query per priority level** — no A/B testing of variations  
❌ **Generic results** — "person working office" matches thousands of clips  

---

## 2. PROPOSED IMPROVED QUERY GENERATION LOGIC

### Strategy: Intent-Based, Emotion-Focused, Hook-Aware

#### New Process (4 layers with multiple variations):

```python
# LAYER 1: INTENT-BASED MAPPING
# Extract intent from script, not just keywords
# Example: "My business makes $50k passive" 
#   Keywords: ["business", "money"]
#   Intent: WEALTH_BUILDING
#   Rich emotional queries:
#     - "successful entrepreneur busy work" (emotion: ambitious)
#     - "laptop side hustle confident person" (emotion: empowered)
#     - "income growth financial freedom" (emotion: aspiration)

_INTENT_BASED_QUERIES = {
    # Income/passive income
    "PASSIVE_INCOME_INTENT": [
        "person laptop laptop working remote income",
        "side hustle online business confident",
        "passive income digital nomad laptop",
    ],
    # Productivity/efficiency
    "PRODUCTIVITY_INTENT": [
        "person focused desk laptop concentration",
        "workflow automation busy work stressed",  # emotion: work pressure
        "efficient organized person achieving goals",
    ],
    # Problems/challenges (for pain points)
    "PAIN_POINT_INTENT": [
        "frustrated person laptop struggling work",
        "overwhelmed stressed finances bills",
        "confused person difficulty problem solving",
    ],
    # Success/achievement
    "SUCCESS_INTENT": [
        "person celebrating success achievement happy",
        "growth upward success person confident",
        "accomplished goal person proud victory",
    ],
    # Learning/education
    "EDUCATION_INTENT": [
        "person learning laptop online course",
        "student studying focused concentration",
        "beginner learning tutorial teaching",
    ],
}

# LAYER 2: EMOTIONAL/CONTEXTUAL ENRICHMENT
# Add emotional keywords to make queries more specific
# Instead of: "money"
# Use: "frustrated person money bills stress"
#   OR "successful person income confident"
#   OR "confused person cryptocurrency confused"

_EMOTIONAL_MODIFIERS = {
    "frustrated": ["frustrated", "stressed", "overwhelmed", "worried"],
    "successful": ["confident", "proud", "celebrated", "winning"],
    "confused": ["confused", "questioning", "puzzled", "discovering"],
    "busy": ["busy", "productive", "focused", "hustling"],
    "dramatic": ["shocking", "dramatic", "surprising", "dramatic reveal"],
}

# LAYER 3: HOOK-SPECIFIC INTENSITY BOOST
# Hook scenes get high-emotion, attention-grabbing queries
# Not just "dramatic cinematic" but VISCERAL emotional content

HOOK_EMOTIONAL_QUERIES = [
    # Tier 1: Shock/surprise (primary hook driver)
    "person shocked surprised reaction face",
    "person confused questioning mind blown",
    "person stunned revelation dramatic moment",
    # Tier 2: Strong action/energy
    "person frustrated stressed overwhelming work",
    "person excited enthusiastic celebration moment",
    "person confident powerful determination face",
    # Tier 3: Visual momentum
    "rapid motion dynamic energy person movement",
    "close up person expression reaction emotion",
    "dramatic lighting contrast person focus",
]

# LAYER 4: MULTIPLE QUERY VARIATIONS PER SCENE
# Instead of 1 query per level, generate 2-3 variations
# Try each in parallel, pick best match

def _scene_query_candidates_improved(scene):
    """Generate multiple query variations per scene"""
    
    candidates = []
    
    # ── HOOK SCENES: Special treatment ──────────────────────────────────
    if scene.part == "hook":
        # High-emotion queries that prioritize compelling visuals
        candidates.extend([
            "person shocked surprised reaction close up",      # v1: shock
            "dramatic moment person reacting face emotion",    # v2: drama
            "stunning visual person expressing emotion",       # v3: emotion
        ])
        
        # Add secondary variation based on script content
        script_intent = _detect_intent(scene.source_text)  # new helper
        if script_intent in ("PAIN_POINT", "PROBLEM"):
            candidates.extend([
                "frustrated person struggling stressed",
                "overwhelmed person difficult situation",
            ])
        elif script_intent == "SUCCESS":
            candidates.extend([
                "confident person celebration winning",
                "person proud achievement excited",
            ])
    
    # ── BODY SCENES: Intent-focused queries ────────────────────────────
    else:
        # Step 1: Intent-based mapping (gets 2-3 queries per intent)
        intent = _detect_intent(scene.source_text)
        if intent in _INTENT_BASED_QUERIES:
            # Add all 2-3 variations for this intent
            candidates.extend(_INTENT_BASED_QUERIES[intent])
        
        # Step 2: Keyword mapping with emotional color
        raw_keywords = _extract_keywords(scene.source_text)
        for kw in raw_keywords:
            base = _VISUAL_KEYWORD_MAP.get(kw.lower())
            if base:
                # Original mapped phrase
                candidates.append(base)
                
                # ENHANCED: Add 1-2 emotional variants
                if kw in ("money", "income", "wealth"):
                    candidates.extend([
                        f"person confident {base} success",
                        f"busy work {base} stressed",
                    ])
                elif kw in ("mistake", "problem", "fail"):
                    candidates.extend([
                        f"frustrated person {base}",
                        f"confused person {base} struggle",
                    ])
        
        # Step 3: Visual description (keep existing)
        vd_query = _visual_description_tokens(scene.visual_description)
        if vd_query:
            candidates.append(vd_query)
        
        # Step 4: Fallback (improved version)
        candidates.extend([
            "person working laptop office professional",
            "busy workflow productive desk focus",
            "concept explanation business learning",
        ])
    
    # ── DEDUP & RETURN top variations ──────────────────────────────────
    seen = set()
    result = []
    for c in candidates:
        cleaned = re.sub(r"\s+", " ", str(c)).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    
    # Return TOP 6-8 (increased from 6) to allow parallel testing
    return result[:8]
```

---

## 3. HOOK SCENE SPECIAL HANDLING

### Current Hook Logic (Insufficient):

```python
# In visual_scoring.py:
if scene_type == "hook":
    position_score = 10  # Max score
    # But for STOCK mode, just uses fallback queries:
    # ["dramatic cinematic person close up", "shocked surprised person reaction"]
    # ❌ Problem: Too generic, not emotionally compelling
```

### Proposed Hook Logic (Footage Intelligence):

#### Hook Requirements:

```python
class HookScene:
    """Special handling for hook scenes in stock footage mode"""
    
    # MUST HAVE: Emotional resonance
    # - Shock/surprise facial expression
    # - Intense engagement (not neutral/professional)
    # - Close-up or dynamic movement
    # - Person-focused (not landscape/abstract)
    
    # REJECT: Generic/neutral
    # - Calm office workers
    # - Wide shots of buildings
    # - Stock footage clichés
    # - Slow-paced content

    HOOK_QUERY_TIERS = {
        # Tier 1: SHOCK & SURPRISE (best for hooks)
        "shock": [
            "person shocked surprised reaction face",
            "stunned face expression moment",
            "mind blown confused reaction person",
        ],
        # Tier 2: STRONG EMOTION
        "emotion": [
            "frustrated stressed overwhelmed person face",
            "excited enthusiastic celebration person",
            "confident powerful determined person",
        ],
        # Tier 3: VISUAL MOMENTUM
        "momentum": [
            "dynamic movement person energy motion",
            "close up person dramatic moment",
            "rapid action person engaged focus",
        ],
    }
```

#### Implementation Strategy:

1. **Detect Hook's Trigger Type** (from script):
   - Is it asking for shock? ("Wait until second 3...")
   - Is it building hype? ("This breaks the internet...")
   - Is it showing struggle? ("Frustrated with...")

2. **Query by Trigger Type**:
   ```python
   if "wait" or "reveal" or "unbelievable" in hook_text:
       queries = HOOK_QUERY_TIERS["shock"]  # Prioritize shock
   elif "frustrated" or "struggling" in hook_text:
       queries = HOOK_QUERY_TIERS["emotion"]  # Prioritize frustration/relief
   elif hook_text mentions speed/momentum:
       queries = HOOK_QUERY_TIERS["momentum"]  # Prioritize dynamic movement
   ```

3. **Multi-Query Parallel Search**:
   ```python
   # Instead of trying queries sequentially, try all 3-4 in parallel
   async def fetch_hook_clips(scene):
       tasks = [
           search_pexels(query) for query in hook_queries[:3]
       ]
       results = await asyncio.gather(*tasks)
       
       # Pick best: 
       # - Prioritize shock/emotion queries over generic
       # - Reject dark/neutral results
       # - Prefer person-focused clips
       best_clip = max(results, key=score_hook_clip_quality)
       return best_clip
   ```

4. **Quality Score for Hook Clips**:
   ```python
   def score_hook_clip_quality(clip_metadata):
       score = 0
       
       # GOOD: Emotional content
       if "person" in clip_tags:
           score += 30  # Must have person
       if any(emotion in clip_tags for emotion in ["shocked", "surprised", "frustrated"]):
           score += 25  # Emotional reaction = good
       if "reaction" in clip_tags or "expression" in clip_tags:
           score += 20  # Expression visible = good
       
       # GOOD: Composition
       if clip_aspect_ratio >= 0.9:  # closeup
           score += 15
       if "fast" in clip_tags or "dynamic" in clip_tags:
           score += 10
       
       # BAD: Generic/neutral
       if "office" in clip_tags and "emotion" not in clip_tags:
           score -= 20  # Generic office worker
       if "landscape" in clip_tags or "wide shot" in clip_tags:
           score -= 25  # No emotional resonance
       if clip_duration < 2:
           score -= 15  # Too short for hook
       
       # Brightness guardrail (dark clips are bad for hooks)
       if luma < 25:
           score -= 50
       
       return score
   ```

---

## 4. MULTIPLE QUERY VARIATIONS & SELECTION

### Current Process:
- Single query per priority level
- No testing of alternatives
- First match wins (luck-dependent)

### Proposed Process:

```python
async def fetch_scene_clips_improved(scene, run_id):
    """
    Generate multiple query variations and test each in parallel.
    Select best clip based on quality scoring.
    """
    
    # Generate 3-8 query variations (depending on scene type)
    queries = _scene_query_candidates_improved(scene)
    
    print(f"[SCENE {scene.idx}] Testing {len(queries)} query variations...")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. '{q}'")
    
    # Search all queries in parallel (for speed)
    async with httpx.AsyncClient() as client:
        tasks = [
            _search_pexels_pixabay(client, q, scene.part)
            for q in queries
        ]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect valid clips from all queries
    valid_clips = []
    for query, result in zip(queries, all_results):
        if isinstance(result, dict) and result.get("clip_url"):
            valid_clips.append({
                "url": result["clip_url"],
                "query": query,
                "source": result["source"],  # pexels or pixabay
                "quality_score": _score_clip_for_scene(
                    result, scene.part
                ),
            })
    
    if not valid_clips:
        raise RuntimeError(f"No valid clips for scene {scene.idx}")
    
    # Pick BEST match based on scene type
    if scene.part == "hook":
        # For hooks: prioritize emotional/shock queries
        best = max(valid_clips, 
                   key=lambda c: c["quality_score"] * (
                       2.0 if "shock" in c["query"] or "emotion" in c["query"]
                       else 1.0
                   ))
    else:
        # For body/cta: just pick highest quality
        best = max(valid_clips, key=lambda c: c["quality_score"])
    
    print(f"[SCENE {scene.idx}] Selected: '{best['query']}' from {best['source']}")
    
    scene.clip_url = best["url"]
    scene.selected_query = best["query"]
    return scene
```

---

## 5. IMPLEMENTATION CHECKLIST

### Files to Modify:

- [ ] `backend/utils/video_pipeline.py`
  - [ ] Add `_INTENT_BASED_QUERIES` constant
  - [ ] Add `_detect_intent()` helper function
  - [ ] Rewrite `_scene_query_candidates()` with improved logic
  - [ ] Update `_search_pexels_pixabay()` to score clips by quality

- [ ] `backend/utils/visual_scoring.py`
  - [ ] Add `score_hook_clip_quality()` function
  - [ ] Add `HOOK_QUERY_TIERS` constant
  - [ ] Update hook scene scoring (no changes needed, keeps gen4.5 preference)

- [ ] `backend/routes/generate.py`
  - [ ] Update `fetch_scene_clips()` to use improved query generation
  - [ ] No UI changes needed (hidden backend improvement)

### No Changes To:

- ✅ UI (hidden backend improvement)
- ✅ AI/Hybrid modes (stock footage only)
- ✅ Pexels/Pixabay API calls (same endpoints, better queries)

---

## 6. EXPECTED IMPROVEMENTS

### Before (Current):
```
Hook scene query: "dramatic cinematic person close up"
 → Returns: calm professional, generic office worker, landscape

Body scene query: "money" 
 → Returns: generic wallet, cash stack, unrelated business content

CTA scene query: "success achievement celebration person"
 → Returns: generic celebration, sometimes wrong emotion
```

### After (Improved):
```
Hook scene queries: ["shocked surprised reaction face", "mind blown expression", "dramatic moment person"]
 → All 3 tested in parallel
 → Returns: emotional close-up, shocking expression, dynamic movement
 → Selects: "shocked surprised reaction face" (highest emotional score)

Body scene query: "frustrated person laptop struggling work stress"
 → Returns: visibly frustrated person at computer, realistic scenario

Hook pain-point query: "overwhelmed stressed person busy work"
 → Returns: realistic frustration visuals, high relatability

CTA scene queries: ["confident person achievement winning", "person celebration success", "proud determined face"]
 → All tested, best match selected
 → Returns: authentic celebration, visible confidence, appropriate energy
```

---

## Ready to Code?

Once approved:
1. Implement intent detection helper
2. Create improved `_scene_query_candidates()` 
3. Add clip quality scoring
4. Update `fetch_scene_clips()` for parallel testing
5. Run tests to confirm no UI breaks

