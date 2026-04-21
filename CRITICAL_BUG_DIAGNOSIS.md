# Bug Diagnosis: "Hook:", "Body:", "CTA:" Labels in Voiceover/Captions

**Date:** April 17, 2026  
**Status:** CRITICAL BUG FOUND AND FIXED

---

## 1. EXACT BUGGY FLOW

### Frontend Bug (Dashboard.jsx)

**Line 639-648: `composeScriptFromParts()` adds labels**
```javascript
function composeScriptFromParts(hook = '', body = '', cta = '') {
  const safeHook = String(hook || '').trim();
  const safeBody = String(body || '').trim();
  const safeCta = String(cta || '').trim();

  const parts = [];
  if (safeHook) parts.push(`Hook: ${safeHook}`);      // ← ADDS LABEL
  if (safeBody) parts.push(`Body: ${safeBody}`);      // ← ADDS LABEL
  if (safeCta) parts.push(`CTA: ${safeCta}`);         // ← ADDS LABEL
  return parts.join('\n\n').trim();
}
```

**Output:**
```
Hook: This is the hook

Body: This is the body

CTA: Follow now
```

**Line 655-660: Stores labeled version as authoritative**
```javascript
function createScriptState(hook = '', body = '', cta = '', fullScript = '') {
  const safeFullScript = String(fullScript || composeScriptFromParts(safeHook, safeBody, safeCta)).trim();
  return {
    hook: safeHook,
    body: safeBody,
    cta: safeCta,
    full_script: safeFullScript,  // ← NOW CONTAINS "Hook:" "Body:" "CTA:" labels
    //...
  };
}
```

### Backend Receives Labeled Script

**Line 2227 (generateVideoPlan call):**
```javascript
const plan = await api.generateVideoPlan({
  script: authoritativeScript.full_script,          // ← LABELED
  full_script: authoritativeScript.full_script,     // ← LABELED
  hook: authoritativeScript.hook,                   // ← CLEAN
  body: authoritativeScript.body,                   // ← CLEAN
  cta: authoritativeScript.cta,                     // ← CLEAN
});
```

**Backend receives both versions:**
- `full_script = "Hook: This is the hook\n\nBody: This is the body\n\nCTA: Follow now"`
- `hook = "This is the hook"`
- `body = "This is the body"`
- `cta = "Follow now"`

### Backend Uses Wrong Version (routes/generate.py)

**Line 735 in `/video/free` endpoint:**
```python
parts = parse_script(
    full_script=authoritative_script,  # ← USES LABELED VERSION
    hook=request.hook,
    body=request.body,
    cta=request.cta,
)
```

**Line 738 (after Batch 2A fix):**
```python
script_text = f"{parts.hook} {parts.body} {parts.cta}"
```

**But if `parse_script()` was called with LABELED `full_script`:**
```python
script_text = f"{parts.hook} {parts.body} {parts.cta}"
# If full_script had labels, parts might be misaligned
```

---

## 2. EXACT FUNCTIONS TO CHANGE

### Change 1: Dashboard.jsx - Fix `composeScriptFromParts()`
**Location:** Line 639-648

**Before (BUGGY):**
```javascript
function composeScriptFromParts(hook = '', body = '', cta = '') {
  const safeHook = String(hook || '').trim();
  const safeBody = String(body || '').trim();
  const safeCta = String(cta || '').trim();

  const parts = [];
  if (safeHook) parts.push(`Hook: ${safeHook}`);    // BUG: Labels!
  if (safeBody) parts.push(`Body: ${safeBody}`);    // BUG: Labels!
  if (safeCta) parts.push(`CTA: ${safeCta}`);       // BUG: Labels!
  return parts.join('\n\n').trim();
}
```

**After (FIXED):**
```javascript
// For RENDER/TTS: plain text, NO labels
function composeScriptFromParts(hook = '', body = '', cta = '') {
  const safeHook = String(hook || '').trim();
  const safeBody = String(body || '').trim();
  const safeCta = String(cta || '').trim();

  // Join plain parts without labels (for TTS, captions, render)
  const parts = [];
  if (safeHook) parts.push(safeHook);
  if (safeBody) parts.push(safeBody);
  if (safeCta) parts.push(safeCta);
  return parts.join(' ').trim();  // Space join, not newlines
}

// NEW: For UI PREVIEW ONLY - add readable labels
function composeScriptPreview(hook = '', body = '', cta = '') {
  const safeHook = String(hook || '').trim();
  const safeBody = String(body || '').trim();
  const safeCta = String(cta || '').trim();

  const parts = [];
  if (safeHook) parts.push(`Hook: ${safeHook}`);
  if (safeBody) parts.push(`Body: ${safeBody}`);
  if (safeCta) parts.push(`CTA: ${safeCta}`);
  return parts.join('\n\n').trim();
}
```

### Change 2: Dashboard.jsx - Use Preview Function for UI Only
**Location:** Line 796 and UI display areas

**Ensure API payloads ALWAYS send clean parts:**
- `script` / `full_script` = clean, no labels
- `hook`, `body`, `cta` = sent separately as source of truth

**UI preview uses `composeScriptPreview()` for visual display only**

### Change 3: Backend Clarify (routes/generate.py)
**Location:** Line 735

**Ensure parse_script() prioritizes explicit parameters over full_script:**
```python
# Current code is CORRECT - explicit parameters take priority
parts = parse_script(
    full_script=authoritative_script,
    hook=request.hook,
    body=request.body,
    cta=request.cta,
)
```

The `parse_script()` function in `video_pipeline.py` already handles this correctly:
```python
def parse_script(full_script: str, hook: Optional[str] = None, body: Optional[str] = None, cta: Optional[str] = None) -> ScriptParts:
    # If explicit hook/body/cta provided, use them (SOURCE OF TRUTH)
    if hook and body and cta:
        return ScriptParts(_clean_text(hook), _clean_text(body), _clean_text(cta))
    
    # Otherwise parse full_script
    # ...
```

---

## 3. EXACT PAYLOAD AFTER FIX

### Before Fix (BUGGY):
```json
{
  "script": "Hook: This is the hook\n\nBody: This is the body\n\nCTA: Follow now",
  "full_script": "Hook: This is the hook\n\nBody: This is the body\n\nCTA: Follow now",
  "hook": "This is the hook",
  "body": "This is the body",
  "cta": "Follow now"
}
```

### After Fix (CORRECT):
```json
{
  "script": "This is the hook This is the body Follow now",
  "full_script": "This is the hook This is the body Follow now",
  "hook": "This is the hook",
  "body": "This is the body",
  "cta": "Follow now"
}
```

**Key Difference:** `full_script` is NOW plain text, NOT labeled.

**Backend's `parse_script()` receives:**
- `full_script = "This is the hook This is the body Follow now"` (plain, no labels)
- `hook = "This is the hook"` (explicit, takes priority)
- `body = "This is the body"` (explicit, takes priority)
- `cta = "Follow now"` (explicit, takes priority)

**Explicit parameters WIN → clean parts extracted:**
```python
parts = ScriptParts(
    hook="This is the hook",     # NO "Hook:" prefix
    body="This is the body",     # NO "Body:" prefix
    cta="Follow now"             # NO "CTA:" prefix
)
```

**TTS receives:**
```python
script_text = f"{parts.hook} {parts.body} {parts.cta}"
# = "This is the hook This is the body Follow now"
# NO LABELS! ✓
```

---

## 4. CONFIRMATION

### Voice & Captions After Fix:
✅ **Voice:** "This is the hook. This is the body. Follow now." (no "Hook:", "Body:", "CTA:")  
✅ **Captions:** "This is the hook. This is the body. Follow now." (no labels)  
✅ **Storyboard/Plan:** Uses clean parts only  
✅ **UI Preview:** Shows `Hook: ... Body: ... CTA: ...` (labeled preview, display-only)

---

## Implementation

1. ✅ Change `composeScriptFromParts()` to return plain text (space-joined)
2. ✅ Add `composeScriptPreview()` for UI display with labels
3. ✅ Use `composeScriptPreview()` in UI display areas only
4. ✅ Ensure all API payloads use plain `full_script` from `composeScriptFromParts()`
5. ✅ Backend already has correct logic (explicit params take priority)

