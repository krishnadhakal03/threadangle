import asyncio
import json
import os
import re
from datetime import datetime

import anthropic


client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _strip_unwanted_year_tokens(text: str, *, script: str, allow_current_year: bool = False) -> str:
    """
    Remove injected 4-digit years (e.g. "2024") unless they appear in the user/script input.

    Guardrail: we do NOT allow "current year" injection by default because it still isn't
    user-provided; allow_current_year must be explicitly enabled by the caller.
    """
    raw = str(text or "").strip()
    if not raw:
        return ""

    script_text = str(script or "")
    allowed_years = set(re.findall(r"\b(19|20)\d{2}\b", script_text))
    # The regex above returns only the first capturing group if we keep (19|20).
    # Use a non-capturing group to get full matches.
    allowed_years = set(re.findall(r"\b(?:19|20)\d{2}\b", script_text))

    if allow_current_year:
        allowed_years.add(str(datetime.now().year))

    def _repl(match: re.Match) -> str:
        year = match.group(0)
        return year if year in allowed_years else ""

    cleaned = re.sub(r"\b(?:19|20)\d{2}\b", _repl, raw)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    # Clean up common punctuation artifacts: " -  " or trailing separators.
    cleaned = re.sub(r"\s*[-–—]\s*$", "", cleaned).strip()
    cleaned = re.sub(r"^\s*[-–—]\s*", "", cleaned).strip()
    return cleaned


def _parse_json_payload(payload: str) -> dict:
    text = (payload or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\\n?", "", text)
        text = re.sub(r"\\n?```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("SEO metadata response was not valid JSON")
        return json.loads(match.group(0))


async def generate_youtube_metadata(script: str, niche: str = "general", duration: int = 45) -> dict:
    """Generate Shorts-focused SEO metadata from script text."""
    prompt = f"""You are a viral YouTube SEO expert. Generate optimized metadata for this short video.

VIDEO SCRIPT:
{(script or '').strip()[:5000]}

NICHE: {niche or 'general'}
DURATION: {int(duration or 45)} seconds

Return strict JSON only:
{{
  "title": "...",
  "description": "...",
  "tags": ["..."],
  "hashtags": ["#..."],
  "thumbnail_text": "..."
}}

Rules:
- title: <= 60 chars
- description: 80-180 words, keyword rich, CTA at end
- tags: 10-20 entries
- hashtags: 5-7 entries starting with #
- thumbnail_text: 3-5 words
- Do NOT add a year (e.g. "2024") unless it appears in the VIDEO SCRIPT verbatim
"""

    def _call() -> dict:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text if response.content else "{}"
        parsed = _parse_json_payload(raw)
        title_raw = str(parsed.get("title", "")).strip()[:100]
        thumb_raw = str(parsed.get("thumbnail_text", "")).strip()[:50]

        # Deterministic safety: strip injected years unless user/script included them.
        title_clean = _strip_unwanted_year_tokens(title_raw, script=script, allow_current_year=False)
        thumb_clean = _strip_unwanted_year_tokens(thumb_raw, script=script, allow_current_year=False)

        return {
            "title": title_clean[:100],
            "description": str(parsed.get("description", "")).strip(),
            "tags": [str(t).strip() for t in (parsed.get("tags") or []) if str(t).strip()][:20],
            "hashtags": [str(h).strip() for h in (parsed.get("hashtags") or []) if str(h).strip()][:10],
            "thumbnail_text": thumb_clean[:50],
        }

    return await asyncio.to_thread(_call)
