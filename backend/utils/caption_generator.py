"""
Dynamic caption generator — MrBeast/TikTok-style ASS word highlighting.

Produces .ass files that FFmpeg's `subtitles=` filter renders natively.
Zero API credits consumed. Timing is estimated when no audio analysis available.

ASS colour format: &HAABBGGRR (alpha, blue, green, red)
  White  = &H00FFFFFF
  Yellow = &H0000FFFF   (karaoke/highlight colour)
  Black  = &H00000000
"""
from __future__ import annotations

import os
import re
import math
import difflib
from pathlib import Path
from typing import List, Optional


# ── Timing constants ──────────────────────────────────────────────────────────
_SECS_PER_WORD = 0.38     # estimated average reading/speech pace
_CHUNK_SIZE    = 4        # words per caption line (mobile-friendly)
_NUMBERED_STARTERS = {"method", "step", "tip", "tips", "way", "ways", "reason", "reasons"}
_ACTION_WORDS = {"sell", "make", "grow", "build", "start", "stop", "use", "create", "edit", "turn", "scale"}
_PAYOFF_CONNECTORS = {"for", "with", "into", "through", "using", "to"}
_WEAK_CONNECTOR_ENDINGS = {"and", "or", "to", "for", "with", "of", "in", "on", "the", "a", "an"}

# ── ASS style template ────────────────────────────────────────────────────────
# Fields: Name,Font,Size,PrimaryColour,SecondaryColour,OutlineColour,BackColour,
#         Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,
#         BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
_ASS_STYLE = (
    "Style: Default,"
    "Impact,"           # font — Impact gives TikTok aesthetic; Arial Bold is fallback
    "60,"               # size
    "&H00FFFFFF,"       # primary   = white (unplayed text)
    "&H0000FFFF,"       # secondary = yellow (karaoke fill sweep)
    "&H00000000,"       # outline   = black
    "&H80000000,"       # back      = semi-transparent black shadow box
    "-1,"               # bold
    "0,0,0,"            # italic, underline, strikeout
    "100,100,"          # scaleX, scaleY
    "0,0,"              # spacing, angle
    "1,"                # border style 1=outline+shadow
    "5,"                # outline thickness (thick = readable on any background)
    "1,"                # shadow
    "2,"                # alignment = bottom-centre (\an2)
    "30,30,"            # marginL, marginR
    "460,"              # marginV from bottom — places captions in the 3rd quarter
                        # (PlayResY=1280: 460px up = ~64% from top, above all platform UI)
    "1"                 # encoding
)


def _ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format h:mm:ss.cs"""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds % 1) * 100))
    # Guard against rounding overflow (e.g., 25.999 -> 25.100), which is invalid ASS.
    if cs >= 100:
        cs = 0
        s += 1
        if s >= 60:
            s = 0
            m += 1
            if m >= 60:
                m = 0
                h += 1
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _chunk_words(words: List[str], size: int) -> List[List[str]]:
    return [words[i:i + size] for i in range(0, len(words), size)]


def _word_count(text: str) -> int:
    return len([w for w in re.split(r"\s+", (text or "").strip()) if w])


def _normalize_word_token(token: str) -> str:
    """
    Normalize a single Whisper/script token for deterministic matching.
    - lowercase
    - normalize common unicode dashes to '-'
    - normalize curly apostrophes to "'"
    - strip punctuation
    """
    t = str(token or "").lower()
    # Dash normalization
    t = (
        t.replace("—", "-")
        .replace("–", "-")
        .replace("‑", "-")
        .replace("−", "-")
    )
    # Apostrophe normalization
    t = t.replace("’", "'").replace("`", "'")
    # Remove punctuation (keep alnum + apostrophe), then normalize small number words.
    t = re.sub(r"[^a-z0-9']+", "", t)
    number_words = {
        "zero": "0",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
    }
    homophone_words = {
        "eye": "ai",
    }
    t = number_words.get(t, t)
    t = homophone_words.get(t, t)
    return t


def _token_match_score(expected: str, candidate: str) -> float:
    exp = _normalize_word_token(expected)
    cand = _normalize_word_token(candidate)
    if not exp or not cand:
        return 0.0
    if exp == cand:
        return 1.0
    if len(exp) >= 4 and (exp.startswith(cand) or cand.startswith(exp)):
        return 0.92
    return difflib.SequenceMatcher(None, exp, cand).ratio()


def _tokens_match(expected: str, candidate: str) -> bool:
    score = _token_match_score(expected, candidate)
    exp = _normalize_word_token(expected)
    cand = _normalize_word_token(candidate)
    if exp == cand:
        return True
    if min(len(exp), len(cand)) <= 3:
        return score >= 0.84
    return score >= 0.78


def _is_numeric_caption_token(token: str) -> bool:
    return bool(re.sub(r"[^0-9]", "", str(token or "")))


def _match_scene_word_timings(
    all_word_timings: List[dict],
    start_index: int,
    text: str,
    scene_start: float,
    scene_end: float,
    max_lookahead: int = 120,
    max_whisper_skips: int = 28,
    max_expected_skips: int = 4,
    min_confidence: float = 0.62,
) -> tuple[Optional[List[dict]], int, int, float, str, str]:
    """
    Deterministic sequential alignment:
    - consumes Whisper words in order across scenes
    - tolerates punctuation/tokenization differences
    - allows small skips/mismatches

    Returns: (timings|None, next_index, aligned_words, confidence, reason, mode)
    """
    # Preserve original subtitle words for display while matching on normalized forms.
    raw_tokens = [w for w in re.split(r"\s+", str(text or "").strip()) if w]
    expected_pairs = [(surface, _normalize_word_token(surface)) for surface in raw_tokens if _normalize_word_token(surface)]
    expected = [norm for _, norm in expected_pairs]
    if not expected:
        return None, start_index, 0, 0.0, "EMPTY_TEXT", "none"

    i = max(0, int(start_index or 0))
    j = 0
    whisper_skips = 0
    expected_skips = 0
    matched: List[dict] = []

    while j < len(expected) and i < len(all_word_timings):
        target = expected[j]
        found_at = None
        merged_found = False
        upper = min(len(all_word_timings), i + max(1, int(max_lookahead)))
        for k in range(i, upper):
            cand = _normalize_word_token(all_word_timings[k].get("word", ""))
            if _tokens_match(target, cand):
                found_at = k
                break
            if k + 1 < upper:
                merged_two = _normalize_word_token(
                    f"{all_word_timings[k].get('word', '')}{all_word_timings[k + 1].get('word', '')}"
                )
                if _tokens_match(target, merged_two):
                    found_at = k
                    merged_found = True
                    break

        if found_at is not None:
            matched_item = dict(all_word_timings[found_at])
            if merged_found and found_at + 1 < len(all_word_timings):
                matched_item["end"] = all_word_timings[found_at + 1].get("end", matched_item.get("end"))
            matched_item["word"] = expected_pairs[j][0]
            matched.append(matched_item)
            i = found_at + (2 if merged_found else 1)
            j += 1
            continue

        # For short scenes, prefer skipping a stubborn script token before
        # burning through the sequential Whisper cursor.
        if len(expected) <= 10:
            if expected_skips < max_expected_skips and j + 1 < len(expected):
                j += 1
                expected_skips += 1
                continue
            if whisper_skips < max_whisper_skips and i + 1 < len(all_word_timings):
                i += 1
                whisper_skips += 1
                continue
        else:
            if expected_skips < max_expected_skips and j + 1 < len(expected):
                j += 1
                expected_skips += 1
                continue
            if whisper_skips < max_whisper_skips and i + 1 < len(all_word_timings):
                i += 1
                whisper_skips += 1
                continue
        break

    aligned_words = len(matched)
    confidence = aligned_words / max(1, len(expected))

    expected_len = int(len(expected))
    acceptance_mode = "strong"
    if expected_len <= 6:
        min_aligned = max(2, int(math.ceil(0.30 * expected_len)))
        min_conf = 0.45
    elif expected_len <= 10:
        min_aligned = max(2, int(math.ceil(0.40 * expected_len)))
        min_conf = 0.55
    else:
        min_aligned = max(3, int(math.ceil(0.45 * expected_len)))
        min_conf = float(min_confidence)

    # Allow more graceful partial acceptance for short/medium scenes once at least
    # a few anchor words are locked to the real audio.
    if expected_len <= 12 and aligned_words >= 2:
        if aligned_words < min_aligned or confidence < min_conf:
            acceptance_mode = "partial"
    else:
        if aligned_words < min_aligned:
            return None, start_index, aligned_words, confidence, "TOO_FEW_ALIGNED_WORDS", "none"
        if confidence < min_conf:
            return None, start_index, aligned_words, confidence, "LOW_CONFIDENCE", "none"

    try:
        first_start = float(matched[0].get("start", scene_start))
        last_end = float(matched[-1].get("end", scene_end))
        allowed_drift = 0.75
        if expected_len <= 10:
            allowed_drift = 1.50
        if expected_len > 10 and confidence >= 0.75 and aligned_words >= 3:
            allowed_drift = max(allowed_drift, 2.50)
        if expected_len > 12 and (first_start < scene_start - allowed_drift or last_end > scene_end + allowed_drift):
            if confidence < 0.60 or aligned_words < 3:
                return None, start_index, aligned_words, confidence, "DRIFT_OUTSIDE_SCENE_WINDOW", "none"
    except Exception:
        pass

    normalized: List[dict] = []
    cursor = float(max(0.0, matched[0].get("start", scene_start)))
    for idx2, item in enumerate(matched):
        raw_start = float(item.get("start", cursor))
        raw_end = float(item.get("end", raw_start + 0.1))
        start = max(cursor, raw_start)
        end = max(raw_end, start + 0.12)
        if idx2 == len(matched) - 1:
            end = max(end, start + 0.12)
        normalized.append({"word": item.get("word", ""), "start": round(start, 3), "end": round(end, 3)})
        cursor = end

    if not normalized or normalized[-1]["end"] <= normalized[0]["start"]:
        return None, start_index, aligned_words, confidence, "INVALID_CLAMP", "none"

    # If the accepted match only anchored part of the subtitle, expand the full subtitle
    # across the matched audio span so captions keep the original narration text.
    if aligned_words < expected_len:
        span_start = normalized[0]["start"]
        span_end = max(span_start + 0.3, normalized[-1]["end"])
        normalized = _estimate_word_timings_in_window(text, span_start, span_end)

    return normalized, i, aligned_words, confidence, "OK", acceptance_mode

def _chunk_word_timings_phrase_aware(word_timings: List[dict], max_words: int = _CHUNK_SIZE) -> List[List[dict]]:
    """Chunk timings with punctuation-aware boundaries for better mobile readability."""
    if not word_timings:
        return []

    chunks: List[List[dict]] = []
    current: List[dict] = []
    for item in word_timings:
        current.append(item)
        token = str(item.get("word", "")).strip()
        end_punct = token[-1:] in {".", "!", "?", ":", ";", "—"}
        if len(current) >= max_words or (end_punct and len(current) >= 2):
            chunks.append(current)
            current = []

    if current:
        chunks.append(current)

    # Merge single-word tail fragments into previous chunk when possible.
    if len(chunks) >= 2 and len(chunks[-1]) == 1 and len(chunks[-2]) < max_words + 1:
        chunks[-2].extend(chunks[-1])
        chunks.pop()
    return chunks


def _chunk_word_timings_phrase_aware(word_timings: List[dict], max_words: int = _CHUNK_SIZE) -> List[List[dict]]:
    """Chunk timings with phrase-aware boundaries for sharper mobile readability."""
    if not word_timings:
        return []

    units: List[List[dict]] = []
    idx = 0
    while idx < len(word_timings):
        current = [word_timings[idx]]
        token = _normalize_word_token(word_timings[idx].get("word", ""))

        if (
            token in _NUMBERED_STARTERS
            and idx + 1 < len(word_timings)
            and _is_numeric_caption_token(word_timings[idx + 1].get("word", ""))
        ):
            current.append(word_timings[idx + 1])
            idx += 2
            units.append(current)
            continue

        if token in _ACTION_WORDS:
            next_idx = idx + 1
            while next_idx < len(word_timings) and len(current) < 3:
                next_token = _normalize_word_token(word_timings[next_idx].get("word", ""))
                if next_token in _WEAK_CONNECTOR_ENDINGS:
                    break
                current.append(word_timings[next_idx])
                next_idx += 1
            idx = next_idx
            units.append(current)
            continue

        if token in _PAYOFF_CONNECTORS:
            next_idx = idx + 1
            while next_idx < len(word_timings) and len(current) < 3:
                current.append(word_timings[next_idx])
                next_idx += 1
            idx = next_idx
            units.append(current)
            continue

        idx += 1
        units.append(current)

    chunks: List[List[dict]] = []
    current_chunk: List[dict] = []
    current_word_count = 0
    for unit in units:
        unit_word_count = len(unit)
        end_punct = str(unit[-1].get("word", "")).strip()[-1:] in {".", "!", "?", ":", ";", "—"}

        if current_chunk and current_word_count + unit_word_count > max_words:
            tail_token = _normalize_word_token(current_chunk[-1].get("word", ""))
            if tail_token in _WEAK_CONNECTOR_ENDINGS and len(current_chunk) > 1:
                current_chunk.pop()
                current_word_count -= 1
            chunks.append(current_chunk)
            current_chunk = []
            current_word_count = 0

        current_chunk.extend(unit)
        current_word_count += unit_word_count

        if end_punct and current_word_count >= 2:
            tail_token = _normalize_word_token(current_chunk[-1].get("word", ""))
            if tail_token in _WEAK_CONNECTOR_ENDINGS and len(current_chunk) > 1:
                current_chunk.pop()
                current_word_count -= 1
            chunks.append(current_chunk)
            current_chunk = []
            current_word_count = 0

    if current_chunk:
        tail_token = _normalize_word_token(current_chunk[-1].get("word", ""))
        if tail_token in _WEAK_CONNECTOR_ENDINGS and len(current_chunk) > 1:
            current_chunk.pop()
        chunks.append(current_chunk)

    return chunks


def _estimate_word_timings(
    text: str,
    start_offset: float = 0.0,
) -> List[dict]:
    """
    Estimate per-word start/end times at a fixed pace.
    Replace with Whisper output when available for frame-perfect sync.
    """
    raw_words = [w for w in re.split(r"\s+", (text or "").strip()) if w]
    timings = []
    t = start_offset
    for word in raw_words:
        # Slightly longer pause after punctuation
        duration = _SECS_PER_WORD * (1.3 if word.rstrip()[-1:] in ".!?" else 1.0)
        timings.append({"word": word, "start": round(t, 3), "end": round(t + duration, 3)})
        t += duration
    return timings


def _estimate_word_timings_in_window(
    text: str,
    window_start: float,
    window_end: float,
) -> List[dict]:
    """Estimate timings that fill a full scene window to avoid dead caption zones."""
    raw_words = [w for w in re.split(r"\s+", (text or "").strip()) if w]
    if not raw_words:
        return []

    start = float(window_start)
    end = max(start + 0.3, float(window_end))
    available = max(0.3, end - start)

    # Keep punctuation words slightly longer while normalizing to scene duration.
    weights = [1.3 if w.rstrip()[-1:] in ".!?" else 1.0 for w in raw_words]
    total_weight = max(0.001, sum(weights))

    timings: List[dict] = []
    t = start
    for idx, word in enumerate(raw_words):
        duration = available * (weights[idx] / total_weight)
        next_t = min(end, t + duration)
        if idx == len(raw_words) - 1:
            next_t = end
        timings.append({"word": word, "start": round(t, 3), "end": round(next_t, 3)})
        t = next_t

    return timings


def _karaoke_line(chunk_timings: List[dict]) -> str:
    """
    Build a karaoke-tagged text sequence.
    {\kf<centiseconds>} sweeps the secondary (yellow) colour across the word.
    Text is UPPERCASED for TikTok style.
    """
    parts = []
    for item in chunk_timings:
        duration_cs = max(1, int(round((item["end"] - item["start"]) * 100)))
        word = item["word"].upper()
        parts.append(f"{{\\kf{duration_cs}}}{word}")
    return " ".join(parts)


def _normalize_emphasis_token(token: str) -> str:
    return "".join(re.findall(r"[a-z0-9']+", str(token or "").lower()))


def _choose_emphasis_phrases(text: str, role: str) -> list[str]:
    """
    Deterministic, sparse emphasis selection.

    Rules:
    - max one emphasized phrase per scene
    - hook/cta may use up to two only if very short
    - prefer phrase-level emphasis, not many individual word highlights
    """
    role = (role or "").strip().lower()
    raw_words = [w for w in re.split(r"\s+", (text or "").strip()) if w]
    if not raw_words:
        return []

    words = raw_words[:]

    # Identify "high-signal" anchor (numbers / money / %).
    num_idx = None
    for i, w in enumerate(words):
        if re.search(r"(\$?\d+[\d,]*%?|\d+x|\d+/\d+)", w.lower()):
            num_idx = i
            break

    def _span_around(index: int, *, before: int = 1, after: int = 2, max_len: int = 5) -> str:
        start = max(0, index - before)
        end = min(len(words), index + after + 1)
        span = words[start:end]
        return " ".join(span[:max_len]).strip()

    def _first_phrase(max_words: int = 5) -> str:
        return " ".join(words[:max_words]).strip()

    def _last_phrase(max_words: int = 5) -> str:
        return " ".join(words[max(0, len(words) - max_words):]).strip()

    phrases: list[str] = []

    if num_idx is not None:
        phrases.append(_span_around(num_idx, before=1, after=2, max_len=5))
    elif role in {"hook", "payoff_3"}:
        phrases.append(_first_phrase(5))
    elif role == "cta":
        phrases.append(_last_phrase(5))
    else:
        # Keep emphasis sparse on payoff_1/payoff_2 unless there's a number.
        phrases = []

    phrases = [p for p in phrases if p]
    phrases = phrases[:1]

    # Hook/CTA: allow a second phrase only if very short (<= 6 words),
    # and only if the second phrase is distinct.
    if role in {"hook", "cta"} and len(words) <= 6:
        if role == "hook":
            p2 = _last_phrase(2)
        else:
            p2 = _first_phrase(2)
        if p2 and (not phrases or p2.lower() not in phrases[0].lower()):
            phrases = (phrases + [p2])[:2]

    # Final clamp: keep phrase length reasonable.
    out: list[str] = []
    for p in phrases:
        toks = [w for w in re.split(r"\s+", p.strip()) if w]
        if len(toks) > 6:
            toks = toks[:6]
        if len(toks) >= 2:
            out.append(" ".join(toks))
    return out


def _karaoke_line_with_emphasis(chunk_timings: List[dict], emphasis_state: dict) -> str:
    """
    Karaoke line renderer that optionally emphasizes one phrase per scene (two for short hook/cta).

    Emphasis is applied as a single override span (font-size bump) and is deterministic.
    """
    parts = []
    phrases = emphasis_state.get("phrases") or []
    pos = int(emphasis_state.get("pos") or 0)

    for item in chunk_timings:
        duration_cs = max(1, int(round((item["end"] - item["start"]) * 100)))
        word_raw = str(item.get("word") or "")
        word = word_raw.upper()
        token_norm = _normalize_emphasis_token(word_raw)

        prefix = ""
        suffix = ""

        if phrases:
            phrase = phrases[0]
            if token_norm and token_norm == phrase[pos]:
                if pos == 0:
                    # Slight emphasis bump (sparse, readable).
                    prefix = r"{\fs68}"
                pos += 1
                if pos >= len(phrase):
                    suffix = r"{\r}"
                    phrases.pop(0)
                    pos = 0
            else:
                # Reset partial match; allow immediate restart on current token.
                if pos > 0 and token_norm and token_norm == phrase[0]:
                    prefix = r"{\fs68}"
                    pos = 1
                    if len(phrase) == 1:
                        suffix = r"{\r}"
                        phrases.pop(0)
                        pos = 0
                else:
                    pos = 0

        parts.append(f"{prefix}{{\\kf{duration_cs}}}{word}{suffix}")

    emphasis_state["phrases"] = phrases
    emphasis_state["pos"] = pos
    return " ".join(parts)


def generate_ass_captions(
    text: str,
    audio_path: Optional[str] = None,
    start_offset: float = 0.0,
) -> str:
    """
    Generate a complete .ass caption file from script text.

    - style: word-by-word yellow karaoke highlight (MrBeast / TikTok style)
    - Falls back to estimated timing when word_timestamps unavailable
    - audio_path: if Whisper is installed, precise alignment is used automatically

    Returns the full ASS file content as a string.
    """
    # ── 1. Get word timings ─────────────────────────────────────────────────
    word_timings = None

    if audio_path and Path(audio_path).exists():
        try:
            word_timings = _whisper_word_timings(audio_path, start_offset)
        except Exception as exc:
            print(f"[CAPTION] Whisper unavailable ({exc}), using estimated timing.")

    if not word_timings:
        word_timings = _estimate_word_timings(text, start_offset)

    if not word_timings:
        return ""

    # ── 2. Split into display chunks ─────────────────────────────────────────
    chunks = _chunk_word_timings_phrase_aware(word_timings, max_words=_CHUNK_SIZE)

    # ── 3. Build ASS content ─────────────────────────────────────────────────
    header = f"""[Script Info]
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
"""

    lines = []
    for chunk in chunks:
        if not chunk:
            continue
        chunk_start = chunk[0]["start"]
        chunk_end   = chunk[-1]["end"]
        karaoke_text = _karaoke_line(chunk)
        line = (
            f"Dialogue: 0,"
            f"{_ass_time(chunk_start)},"
            f"{_ass_time(chunk_end)},"
            f"Default,,0,0,0,,"
            f"{karaoke_text}"
        )
        lines.append(line)

    return header + "\n".join(lines) + "\n"


def write_ass_file(text: str, path: Path, audio_path: Optional[str] = None, start_offset: float = 0.0) -> Path:
    """Write ASS captions to the given path and return the path."""
    content = generate_ass_captions(text, audio_path=audio_path, start_offset=start_offset)
    path.write_text(content, encoding="utf-8")
    return path


def generate_ass_from_scenes(scenes: list, audio_path: Optional[str] = None) -> str:
    """
    Build an ASS file from a list of ScenePlan objects.
    Each scene's subtitle text is timed to the scene window.
    """
    header = f"""[Script Info]
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
    """
    all_word_timings: Optional[List[dict]] = None
    next_word_index = 0
    whisper_used = False
    whisper_available = True
    fallback_reason = ""
    total_words_loaded = 0
    if audio_path and Path(audio_path).exists():
        try:
            all_word_timings = _whisper_word_timings(audio_path, 0.0)
            whisper_used = bool(all_word_timings)
            if not whisper_used:
                fallback_reason = "WHISPER_EMPTY"
            total_words_loaded = int(len(all_word_timings or []))
        except ModuleNotFoundError as exc:
            whisper_available = False
            fallback_reason = f"WHISPER_FAILED:{exc}"
            print("[CAPTION] whisper_available=false (fallback to estimation)")
            print(f"[CAPTION] Whisper unavailable ({exc}), using estimated scene timing.")
        except ImportError as exc:
            whisper_available = False
            fallback_reason = f"WHISPER_FAILED:{exc}"
            print("[CAPTION] whisper_available=false (fallback to estimation)")
            print(f"[CAPTION] Whisper unavailable ({exc}), using estimated scene timing.")
        except Exception as exc:
            fallback_reason = f"WHISPER_FAILED:{exc}"
            print(f"[CAPTION] Whisper unavailable ({exc}), using estimated scene timing.")
    else:
        fallback_reason = "AUDIO_MISSING"

    print(
        f"[CAPTION] whisper_used={'true' if whisper_used else 'false'} "
        f"total_words={total_words_loaded} "
        f"fallback_reason={fallback_reason or 'none'}"
    )

    lines = []
    scenes_with_text = 0
    fallback_scenes = 0
    confidence_values: list[float] = []
    global_caption_cursor = 0.0
    for scene in scenes:
        text = (getattr(scene, "subtitle", None) or getattr(scene, "source_text", None) or "").strip()
        # Encoding fix (approved): normalize mojibake em dash sequence before caption generation.
        text = text.replace("â€”", "—")
        if not text:
            continue
        scenes_with_text += 1
        scene_role = str(getattr(scene, "role_label", "") or "").strip().lower()
        scene_start = float(getattr(scene, "start", 0))
        scene_end   = float(getattr(scene, "end", scene_start + 1))
        word_timings = None
        used_fallback_timing = False
        aligned_words = 0
        confidence = 0.0
        scene_fallback_reason = ""

        if all_word_timings:
            try:
                matched, new_index, aligned_words, confidence, reason, match_mode = _match_scene_word_timings(
                    all_word_timings=all_word_timings,
                    start_index=next_word_index,
                    text=text,
                    scene_start=scene_start,
                    scene_end=scene_end,
                )
                expected_len = _word_count(text)
                accepted = bool(matched)
                print(
                    "[WHISPER_MATCH] "
                    f"scene={getattr(scene, 'idx', '?')} "
                    f"aligned={aligned_words} "
                    f"confidence={confidence:.2f} "
                    f"accepted={'true' if accepted else 'false'} "
                    f"mode={match_mode if accepted else 'none'}"
                )
                if matched:
                    word_timings = matched
                    next_word_index = new_index
                    confidence_values.append(float(confidence or 0.0))
                    print(
                        f"[CAPTION] scene={getattr(scene, 'idx', '?')} "
                        f"aligned_words={aligned_words} confidence={confidence:.2f}"
                    )
                else:
                    print(
                        f"[CAPTION] scene={getattr(scene, 'idx', '?')} "
                        f"aligned_words={aligned_words} confidence={confidence:.2f} "
                        f"fallback_reason={reason}"
                    )
                    used_fallback_timing = True
                    scene_fallback_reason = reason or "ALIGN_NO_MATCH"
            except Exception as exc:
                print(
                    f"[CAPTION] scene={getattr(scene, 'idx', '?')} "
                    f"fallback_reason=ALIGN_EXCEPTION error={exc}"
                )
                used_fallback_timing = True
                scene_fallback_reason = "ALIGN_EXCEPTION"

        if not word_timings:
            fallback_start = max(scene_start, global_caption_cursor)
            fallback_end = max(scene_end, fallback_start + 0.3)
            word_timings = _estimate_word_timings_in_window(text, fallback_start, fallback_end)
            used_fallback_timing = True
            aligned_words = 0
            confidence = 0.0
            if not scene_fallback_reason:
                scene_fallback_reason = "ESTIMATION"

        if used_fallback_timing:
            fallback_scenes += 1
            # Per-scene observability even when estimation was used.
            print(
                f"[CAPTION] scene={getattr(scene, 'idx', '?')} "
                f"aligned_words={aligned_words} confidence={confidence:.2f} "
                f"fallback_reason={scene_fallback_reason or 'ESTIMATION'}"
            )

        # Emphasis selection is display-only and sparse (at most one phrase per scene,
        # hook/cta may use up to two only if very short).
        emphasis_phrases = _choose_emphasis_phrases(text, role=scene_role)
        emphasis_state = {"phrases": [], "pos": 0}
        if emphasis_phrases:
            # Normalize phrase tokens for matching against karaoke words.
            norm_phrases = []
            for phrase in emphasis_phrases:
                toks = [_normalize_emphasis_token(t) for t in re.split(r"\s+", phrase.strip()) if t]
                toks = [t for t in toks if t]
                if toks:
                    norm_phrases.append(toks)
                    print(
                        f"[CAPTION_EMPHASIS] scene={getattr(scene, 'idx', '?')} "
                        f"role={scene_role or 'unknown'} phrase=\"{phrase.strip()}\""
                    )
            emphasis_state = {"phrases": norm_phrases, "pos": 0}

        chunks = _chunk_word_timings_phrase_aware(word_timings, max_words=_CHUNK_SIZE)
        if used_fallback_timing:
            chunk_preview = [" ".join(str(item.get("word", "")).strip() for item in chunk) for chunk in chunks]
            print(
                f"[CAPTION] scene={getattr(scene, 'idx', '?')} "
                f"subtitle={text!r} chunks={chunk_preview}"
            )
        prev_chunk_end = max(scene_start, global_caption_cursor) if used_fallback_timing else global_caption_cursor
        for chunk in chunks:
            if not chunk:
                continue
            if used_fallback_timing:
                # Estimated timings still respect the planned scene window, but should
                # never move backwards relative to already-emitted captions.
                chunk_start = min(max(prev_chunk_end, chunk[0]["start"]), scene_end - 0.1)
                chunk_end = min(max(chunk_start + 0.2, chunk[-1]["end"]), scene_end)
            else:
                # For Whisper-aligned chunks, follow real audio timing.
                chunk_start = max(prev_chunk_end, float(chunk[0]["start"]))
                chunk_end = max(chunk_start + 0.2, float(chunk[-1]["end"]))
            if chunk_end <= chunk_start:
                chunk_end = chunk_start + 0.3
            karaoke_text = (
                _karaoke_line_with_emphasis(chunk, emphasis_state)
                if (emphasis_state.get("phrases") or []) else _karaoke_line(chunk)
            )
            lines.append(
                f"Dialogue: 0,{_ass_time(chunk_start)},{_ass_time(chunk_end)},"
                f"Default,,0,0,0,,{karaoke_text}"
            )
            prev_chunk_end = chunk_end
            global_caption_cursor = chunk_end

    print(
        "[CAPTION_SUMMARY] "
        f"whisper_used={'true' if whisper_used else 'false'} "
        f"total_words={total_words_loaded} "
        f"scenes={scenes_with_text} "
        f"fallback_scenes={fallback_scenes} "
        f"avg_confidence={(sum(confidence_values) / max(1, len(confidence_values))):.2f}"
    )

    return header + "\n".join(lines) + "\n"


# ── Optional faster-whisper integration ──────────────────────────────────────
_FW_MODEL = None
_FW_MODEL_NAME = None


def _get_faster_whisper_model(model_name: str):
    """Load and cache the faster-whisper model at module scope (never reload per call)."""
    global _FW_MODEL, _FW_MODEL_NAME
    name = (model_name or "base").strip() or "base"
    if _FW_MODEL is not None and _FW_MODEL_NAME == name:
        return _FW_MODEL

    from faster_whisper import WhisperModel  # type: ignore

    _FW_MODEL = WhisperModel(
        name,
        device="cpu",
        compute_type="int8",
    )
    _FW_MODEL_NAME = name
    return _FW_MODEL


def _whisper_word_timings(audio_path: str, start_offset: float = 0.0) -> List[dict]:
    """
    Use faster-whisper for word timestamps.
    Model is cached at module scope. Default model comes from FAST_WHISPER_MODEL (default: base).
    """
    model_name = os.getenv("FAST_WHISPER_MODEL", "base").strip() or "base"
    model = _get_faster_whisper_model(model_name)

    timings: List[dict] = []
    segments, _info = model.transcribe(
        str(audio_path),
        word_timestamps=True,
    )
    for segment in segments:
        for w in getattr(segment, "words", []) or []:
            word = getattr(w, "word", "") or ""
            start = getattr(w, "start", None)
            end = getattr(w, "end", None)
            if start is None or end is None:
                continue
            timings.append(
                {
                    "word": str(word).strip(),
                    "start": round(float(start) + float(start_offset), 3),
                    "end": round(float(end) + float(start_offset), 3),
                }
            )
    return timings
