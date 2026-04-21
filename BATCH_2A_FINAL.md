# BATCH 2A: Hook Templates & Adjustments + Bug Fix

## 1. FINAL HOOK TEMPLATE LIST

```python
_HOOK_QUERY_TEMPLATES = [
    "frustrated person laptop stressed work",        # Pain/struggle
    "shocked surprised person reaction close up",    # Shock/surprise  
    "person overwhelmed bills money stress",         # Overwhelm/money stress
    "fast typing computer deadline pressure",        # Urgency/momentum
]
```

**These are concrete, specific, emotionally-resonant queries that avoid generic office vibes.**

---

## 2. REJECTION RULES BY SCENE PART

### HOOK SCENES (Strict)
- **REJECT:** Generic neutral clips (office, professional, calm, peaceful, serene)
  - Exception: allow if also has "person" OR "reaction" (emotional indicator)
- **REJECT:** Abstract/graphics/animation (non-visual)
- **REJECT:** Dark/night (poor for hooks, low luma)
- **BOOST:** Emotional keywords (shocked, surprised, frustrated, stressed, reaction, emotion, dramatic, urgent)
- **BOOST:** Person present in clip
- **PENALIZE:** Slow/calm motion

### BODY & CTA SCENES (Lenient)
- **REJECT:** Duplicates (same clip used twice in video)
- **REJECT:** Dark/night (poor visibility)
- **REJECT:** Abstract/graphics/animation
- **ALLOW:** Office/professional (valid for body/CTA context)
- **ALLOW:** Calm/peaceful (OK for body, not just for hooks)
- **BOOST:** People, action, emotion, movement

---

## 3. BUG FIX: Hook/Body/CTA Markers in TTS

### Current Bug (Line 738 of `backend/routes/generate.py`):

```python
script_text = authoritative_script or f"{parts.hook} {parts.body} {parts.cta}"
```

**PROBLEM:** When user provides full script with markers like:
```
[HOOK]This is the hook[BODY]This is the body[CTA]Follow now
```

The `authoritative_script` still contains the literal `[HOOK]`, `[BODY]`, `[CTA]` markers.

These markers get passed directly to TTS, causing the voiceover to read: **"[HOOK] This is the hook [BODY] This is the body [CTA] Follow now"**

### Fix:

Always use the **parsed parts**, which have markers extracted:

```python
script_text = f"{parts.hook} {parts.body} {parts.cta}"
```

This ensures markers are **always** removed, regardless of input format.

---

## 4. CHANGES SUMMARY

### File: `backend/utils/video_pipeline.py`

**CHANGE 1:** Add Hook Templates (Line ~52)
```python
_HOOK_QUERY_TEMPLATES = [
    "frustrated person laptop stressed work",
    "shocked surprised person reaction close up",
    "person overwhelmed bills money stress",
    "fast typing computer deadline pressure",
]
```

**CHANGE 2:** Rewrite `_scene_query_candidates()` (Lines 375-420)
- Hook scenes: use `_HOOK_QUERY_TEMPLATES` (strict high-impact)
- Body/CTA scenes: mapped base + visual tokens + fallback (3 max)

**CHANGE 3:** Add Scoring Function (new)
```python
def _score_clip_quality_for_scene(clip_title, clip_source, scene_part, used_clips):
    # Strict for hooks, lenient for body/cta
    # Penalize duplicates
    # Penalize weak/generic (only for hooks)
```

**CHANGE 4:** Add Logging Helper (new)
```python
def _log_scene_query_process(...):
    # Log: candidates, winning query, selected clip, rejections
```

**CHANGE 5:** Update `fetch_scene_clips()` (Lines 800-900)
- For stock mode: try candidates sequentially
- Score each result, reject weak ones
- Log the selection process

---

### File: `backend/routes/generate.py`

**CHANGE 6:** Fix TTS Marker Bug (Line 738)

Replace:
```python
script_text = authoritative_script or f"{parts.hook} {parts.body} {parts.cta}"
```

With:
```python
script_text = f"{parts.hook} {parts.body} {parts.cta}"
```

This ensures markers are **always** stripped from TTS input.

---

## 5. IMPLEMENTATION ORDER

1. ✅ Add `_HOOK_QUERY_TEMPLATES` constant
2. ✅ Rewrite `_scene_query_candidates()` function
3. ✅ Add `_extract_meaningful_words()` helper
4. ✅ Add `_visual_description_tokens()` helper
5. ✅ Add `_score_clip_quality_for_scene()` function
6. ✅ Add `_log_scene_query_process()` function
7. ✅ Update `fetch_scene_clips()` orchestration
8. ✅ **Fix TTS marker bug** in `/video/free` endpoint

---

## 6. EXPECTED BEHAVIOR AFTER IMPLEMENTATION

### Hook Scene Query Flow:
```
[SCENE 1] (HOOK)
  Candidates: [
    'frustrated person laptop stressed work',
    'shocked surprised person reaction close up',
    'person overwhelmed bills money stress',
    'fast typing computer deadline pressure'
  ]
  
  Try query 1: 'frustrated person laptop stressed work'
    → Found: "stressed developer at desk" clip
    → Score: 85 (emotional + person + action)
    → Accept ✓
    
  Selected clip: pexels/stressed-developer-working
```

### Body Scene Query Flow:
```
[SCENE 2] (BODY)
  Candidates: [
    'investment growth chart profit',     # From keyword map
    'chart statistics business analysis', # From visual description
    'professional person working office'  # Fallback
  ]
  
  Try query 1: 'investment growth chart profit'
    → Found: "stock market chart animation" clip
    → Score: 45 (abstract, no person)
    → Reject (GENERIC_FOR_STOCK)
    
  Try query 2: 'chart statistics business analysis'
    → Found: "businessman with growth chart" clip
    → Score: 72 (person + business concept)
    → Accept ✓
    
  Selected clip: pixabay/business-growth-chart
```

### TTS Fix:
```
Input script: "[HOOK]Start here[BODY]Middle content[CTA]Follow now"
Parse: parts.hook="Start here", parts.body="Middle content", parts.cta="Follow now"

BEFORE (BUG):
  script_text = "[HOOK]Start here[BODY]Middle content[CTA]Follow now"
  TTS reads: "[HOOK] Start here [BODY] Middle content [CTA] Follow now" ❌

AFTER (FIX):
  script_text = "Start here Middle content Follow now"
  TTS reads: "Start here Middle content Follow now" ✓
```

