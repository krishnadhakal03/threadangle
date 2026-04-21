"""
Voice Learning System
Analyzes a user's past successful generations to learn their unique writing voice,
then injects those patterns into future generation prompts.
"""
import anthropic
import json
import os


def analyze_user_voice(user_generations):
    """
    Analyze user's writing voice from their past successful generations.

    Args:
        user_generations: List of Generation objects (at least 3, ordered newest first)

    Returns:
        dict: Voice profile, or None if analysis fails
    """
    print("\n🎓 VOICE LEARNING ACTIVATED")
    print("=" * 60)
    print(f"Analyzing {len(user_generations)} successful generations...")

    if len(user_generations) < 3:
        print("❌ Need at least 3 generations to learn voice")
        return None

    # Collect content samples from the most recent generations
    samples = []
    for gen in user_generations[:5]:  # Use last 5 at most
        # twitter_output is a JSON column; SQLAlchemy may return str or parsed value
        tw = gen.twitter_output
        if tw:
            tw_text = tw if isinstance(tw, str) else json.dumps(tw)
            if len(tw_text) > 50:
                samples.append({"platform": "Twitter", "content": tw_text[:500]})

        li = gen.linkedin_output
        if li and len(samples) < 5:
            li_text = li if isinstance(li, str) else json.dumps(li)
            if len(li_text) > 50:
                samples.append({"platform": "LinkedIn", "content": li_text[:500]})

    if len(samples) < 3:
        print(f"❌ Not enough content samples ({len(samples)}/3 minimum)")
        return None

    print(f"📝 Collected {len(samples)} content samples")

    samples_text = "\n\n---SAMPLE---\n\n".join(
        f"Platform: {s['platform']}\n{s['content']}" for s in samples
    )

    analysis_prompt = f"""You are a writing style analyst. Analyze these content samples from the same author and create a detailed voice profile.

CONTENT SAMPLES:
{samples_text}

Analyze and identify:

1. SENTENCE STRUCTURE: Average length (short/medium/long), complexity (simple/compound/complex), rhythm.
2. VOCABULARY & LANGUAGE: Formality level (casual/conversational/professional/technical), recurring phrases.
3. TONE & PERSONALITY: Primary tone (one word), confidence in assertions.
4. STRUCTURAL PATTERNS: How they start, organize ideas, and close content.
5. ENGAGEMENT STYLE: Use of questions, personal pronouns, direct reader address.
6. UNIQUE VOICE MARKERS: Signature phrases, recurring themes, storytelling style.

Return ONLY a valid JSON object (no markdown, no explanation) with this exact structure:
{{
  "sentence_style": "short|medium|long",
  "sentence_complexity": "simple|compound|complex",
  "vocabulary_level": "casual|conversational|professional|technical",
  "primary_tone": "one word description",
  "confidence_level": "tentative|balanced|authoritative",
  "opening_style": "description of how they typically start",
  "structure_pattern": "description of how they organize ideas",
  "closing_style": "description of how they typically end",
  "personal_voice": "first_person|second_person|third_person",
  "question_frequency": "rare|occasional|frequent",
  "signature_phrases": ["phrase1", "phrase2", "phrase3"],
  "unique_patterns": ["pattern1", "pattern2"],
  "example_opening": "an example opening in their style",
  "example_closing": "an example closing in their style"
}}"""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        print("🤖 Analyzing with Claude...")

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",  # same model as ai.py
            max_tokens=1000,
            messages=[{"role": "user", "content": analysis_prompt}],
        )

        response_text = response.content[0].text.strip()

        # Strip markdown code fences if present
        if response_text.startswith("```"):
            parts = response_text.split("```")
            response_text = parts[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        voice_profile = json.loads(response_text)

        print("✅ Voice profile created:")
        print(f"   Tone: {voice_profile.get('primary_tone')}")
        print(
            f"   Style: {voice_profile.get('sentence_style')} sentences, "
            f"{voice_profile.get('vocabulary_level')} vocabulary"
        )
        print(
            f"   Patterns: {len(voice_profile.get('signature_phrases', []))} "
            "signature phrases identified"
        )
        return voice_profile

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse voice profile JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Voice analysis failed: {e}")
        return None


def build_voice_prompt(voice_profile):
    """
    Convert a voice profile dict into prompt instructions for content generation.

    Args:
        voice_profile: dict from analyze_user_voice

    Returns:
        str: Prompt addition to prepend to the generation system prompt
    """
    if not voice_profile:
        return ""

    prompt = f"""CRITICAL — WRITE IN THIS USER'S AUTHENTIC VOICE:

You have learned this user's unique writing style. Match it precisely — do NOT write generic AI content.

SENTENCE STYLE:
- Length: {voice_profile.get('sentence_style', 'medium')}
- Complexity: {voice_profile.get('sentence_complexity', 'compound')}

VOCABULARY & TONE:
- Level: {voice_profile.get('vocabulary_level', 'professional')}
- Tone: {voice_profile.get('primary_tone', 'professional')}
- Confidence: {voice_profile.get('confidence_level', 'balanced')}

STRUCTURE:
- Openings: {voice_profile.get('opening_style', 'bold statement')}
- Organization: {voice_profile.get('structure_pattern', 'problem-solution')}
- Closings: {voice_profile.get('closing_style', 'call-to-action')}

VOICE:
- Perspective: {voice_profile.get('personal_voice', 'second_person')}
- Questions: {voice_profile.get('question_frequency', 'occasional')}
"""

    signature_phrases = voice_profile.get("signature_phrases", [])
    if signature_phrases:
        prompt += f"- Signature phrases to incorporate naturally: {', '.join(signature_phrases[:3])}\n"

    unique_patterns = voice_profile.get("unique_patterns", [])
    if unique_patterns:
        prompt += f"- Patterns to follow: {', '.join(unique_patterns[:2])}\n"

    if voice_profile.get("example_opening"):
        prompt += f'\nOPENING STYLE EXAMPLE:\n"{voice_profile["example_opening"]}"\n'

    if voice_profile.get("example_closing"):
        prompt += f'\nCLOSING STYLE EXAMPLE:\n"{voice_profile["example_closing"]}"\n'

    prompt += "\n"
    return prompt


def should_trigger_voice_learning(user):
    """
    Check whether voice learning should be triggered for this user.

    Triggers once, exactly when the 3rd successful generation is recorded.

    Args:
        user: User ORM object

    Returns:
        bool
    """
    if user.voice_learned:
        return False
    return (user.successful_generations_count or 0) == 3


def analyze_user_voice_from_samples(urls: list, sample_text: str) -> dict:
    """
    Analyze a user's voice from explicitly provided URLs and/or a writing sample.
    Used during onboarding to fast-track voice learning without needing 3 generations.

    Args:
        urls: List of URL strings pointing to the user's past content
        sample_text: Raw text the user wrote as a writing sample

    Returns:
        dict: Voice profile, or None if analysis fails
    """
    print("\n🎓 ONBOARDING VOICE ANALYSIS")
    print("=" * 60)

    combined_sample = ""

    # Use the provided sample text if available
    if sample_text and len(sample_text.strip()) >= 50:
        combined_sample += f"WRITING SAMPLE:\n{sample_text.strip()[:3000]}\n\n"
        print(f"📝 Using writing sample ({len(sample_text)} chars)")

    # Try to fetch content from URLs (best-effort, non-blocking)
    if urls:
        import httpx
        import re
        from bs4 import BeautifulSoup

        for url in urls[:3]:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; VoiceAnalyzer/1.0)"
                }
                response = httpx.get(url, headers=headers, timeout=8.0, follow_redirects=True)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    for tag in soup(["nav", "footer", "script", "style", "header", "aside"]):
                        tag.decompose()
                    text = soup.get_text(separator=" ", strip=True)
                    text = re.sub(r"\s+", " ", text).strip()
                    if len(text) > 100:
                        combined_sample += f"URL CONTENT ({url[:50]}):\n{text[:1500]}\n\n"
                        print(f"  ✅ Extracted content from {url[:50]}")
            except Exception as e:
                print(f"  ⚠️ Could not fetch {url[:50]}: {e}")

    if len(combined_sample.strip()) < 50:
        print("❌ Not enough content to analyze voice")
        return None

    analysis_prompt = f"""You are a writing style analyst. A user wants their AI-generated content to match their unique voice.
Analyze the content samples below and create a detailed voice profile.

CONTENT SAMPLES FROM USER:
{combined_sample[:4000]}

Identify their:
1. SENTENCE STRUCTURE: Average length (short/medium/long), complexity (simple/compound/complex)
2. VOCABULARY: Formality level (casual/conversational/professional/technical)
3. TONE & PERSONALITY: Primary tone (one word), confidence level
4. STRUCTURAL PATTERNS: How they open, organize ideas, close content
5. ENGAGEMENT STYLE: Use of questions, personal pronouns, direct address
6. UNIQUE VOICE MARKERS: Signature phrases, recurring themes

Return ONLY valid JSON (no markdown, no explanation):
{{
  "sentence_style": "short|medium|long",
  "sentence_complexity": "simple|compound|complex",
  "vocabulary_level": "casual|conversational|professional|technical",
  "primary_tone": "one word description",
  "confidence_level": "tentative|balanced|authoritative",
  "opening_style": "description of how they typically start",
  "structure_pattern": "description of how they organize ideas",
  "closing_style": "description of how they typically end",
  "personal_voice": "first_person|second_person|third_person",
  "question_frequency": "rare|occasional|frequent",
  "signature_phrases": ["phrase1", "phrase2", "phrase3"],
  "unique_patterns": ["pattern1", "pattern2"],
  "example_opening": "an example opening in their style",
  "example_closing": "an example closing in their style"
}}"""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": analysis_prompt}],
        )
        response_text = response.content[0].text.strip()
        if response_text.startswith("```"):
            parts = response_text.split("```")
            response_text = parts[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        profile = json.loads(response_text)
        print(f"✅ Onboarding voice profile created: tone={profile.get('primary_tone')}")
        return profile
    except Exception as e:
        print(f"❌ Onboarding voice analysis failed: {e}")
        return None
