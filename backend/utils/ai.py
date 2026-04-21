import httpx
from bs4 import BeautifulSoup
import os
import re
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Use synchronous client — simpler and reliable for our use case
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


async def extract_content_from_url(url: str) -> str:
    """Fetch URL and extract main article text."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http_client:
        try:
            response = await http_client.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove noise
            for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside', 'form', 'iframe', 'noscript']):
                tag.decompose()

            # Try semantic content containers first
            content_node = (
                soup.find('article') or
                soup.find('main') or
                soup.find(attrs={'class': re.compile(r'(article|post|content|story|body)', re.I)}) or
                soup.find('div', id=re.compile(r'(article|post|content|story|body)', re.I))
            )
            target = content_node if content_node else soup
            text = target.get_text(separator='\n', strip=True)

            # Clean up whitespace
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            cleaned = '\n'.join(lines)

            if len(cleaned) < 100:
                raise Exception("Could not extract meaningful content from this URL. Try pasting the text directly.")

            return cleaned[:6000]

        except httpx.TimeoutException:
            raise Exception("URL took too long to load. Try pasting the article text directly.")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Could not access this URL (HTTP {e.response.status_code}). Try pasting the text directly.")
        except Exception as e:
            raise Exception(f"URL extraction failed: {str(e)}")


VIDEO_PROMPT_PREFIX = """IMPORTANT — SOURCE IS A VIDEO TRANSCRIPT:
This content comes from a spoken video. Apply these rules:
- Extract and include personal stories, anecdotes, and "I remember when..." moments — they make content engaging
- Preserve specific examples: named companies, people, products, numbers, statistics, case studies
- Capture memorable one-liners, controversial statements, and wisdom nuggets
- If the speaker gives a framework (3 steps, 5 rules, etc.), keep its structure and number the points
- Ignore filler tangents and "anyway..." diversions that go nowhere
GOAL: Make the reader feel like they watched the video and took excellent notes — not like they read a generic summary.
"""


def build_prompt(input_text: str, platforms: list, tone: str, is_youtube: bool = False, voice_prefix: str = "", niche_context: str = "") -> str:
    tone_map = {
        'professional': 'authoritative, expert tone',
        'casual': 'conversational, friendly tone',
        'bold': 'provocative, direct, bold claims',
        'educational': 'clear, informative, teach-focused',
        'witty': 'witty, clever, viral-friendly tone',
        'controversial': 'provocative, controversial, debate-sparking tone',
    }
    tone_desc = tone_map.get(tone, 'professional tone')

    platform_instructions = []

    if 'twitter' in platforms:
        platform_instructions.append('"twitter": a numbered Twitter thread of 5-8 tweets. Number each: 1/, 2/, 3/ etc. Hook first. Under 280 chars each. Max 2 hashtags on last tweet only. Plain text, no markdown.')

    if 'linkedin' in platforms:
        platform_instructions.append('"linkedin": a 150-250 word LinkedIn post. Scroll-stopping first line. Short paragraphs. End with a question. 3-5 hashtags at end. Plain text, no markdown.')

    if 'tiktok' in platforms:
        platform_instructions.append(
            '"tiktok": a 45-60 second spoken TikTok script. '
            'CRITICAL: Output MUST use these exact emoji headers on their own lines, in this order:\\n\\n'
            '🎬 HOOK (0-3 seconds)\\n[Attention-grabbing opening line]\\n\\n'
            '📱 SETUP (3-10 seconds)\\n[Context and problem statement]\\n\\n'
            '💡 VALUE (10-45 seconds)\\n[Main content in 2-3 short sentences with line breaks]\\n\\n'
            '✨ CTA (45-60 seconds)\\n[Call to action — ask a question, tell them to follow, or prompt engagement]\\n\\n'
            '🏷️ HASHTAGS\\n[20-30 viral hashtags relevant to content. Format: #hashtag1 #hashtag2 #hashtag3. Mix: 3-5 mega hashtags (10M+ views like #fyp #viral #trending), 5-8 large (1M-10M), 8-12 medium (100K-1M), 5-8 small/targeted (10K-100K)]\\n\\n'
            'Keep each section concise and easy to read aloud. Plain text only within each section, no markdown.'
        )
    if 'reels_title' in platforms:
        platform_instructions.append(
            '"reels_title": engaging Instagram Reels title, 8-15 words, curiosity-driven, front-load the hook, use power words (secret, mistake, truth, hack, proven). Example: "The Interview Mistake 90% of Candidates Make"'
        )

    if 'reels_description' in platforms:
        platform_instructions.append(
            '"reels_description": Instagram Reels caption, 3-5 sentences: hook first, quick value preview, CTA at end (tag a friend / save this / follow for more). 1-2 emojis max. Casual conversational tone. Under 2200 characters.'
        )

    if 'reels_hashtags' in platforms:
        platform_instructions.append(
            '"reels_hashtags": 20-30 hashtags, space-separated on one line, each starting with #. Mix sizes: 3-5 mega (1M+ posts), 5-8 large (100K-1M), 8-12 medium (10K-100K), 5-8 niche (1K-10K). No spaces within a hashtag. All on one line.'
        )

    if 'shorts_title' in platforms:
        platform_instructions.append(
            '"shorts_title": YouTube Shorts title, maximum 60 characters. Front-load keywords for SEO. Include numbers when possible. Clear and searchable. Example: "3 Startup Mistakes That Cost Me $50K"'
        )

    if 'shorts_description' in platforms:
        platform_instructions.append(
            '"shorts_description": YouTube Shorts description. First 2-3 sentences must contain target keywords (these appear in search). Include a CTA (Subscribe / Watch full video). Keyword-rich and formal tone. Under 500 characters.'
        )

    if 'shorts_tags' in platforms:
        platform_instructions.append(
            '"shorts_tags": 10-15 YouTube tags, comma-separated, NO # symbol. Searchable keywords: topic terms, broad category, specific niche, and format (shorts). Example: startup tips, interview advice, career advice, entrepreneurship, shorts'
        )
    platforms_json_keys = ', '.join(f'"{p}"' for p in platforms)
    instructions_text = '\n'.join(f'- {i}' for i in platform_instructions)
    trimmed_input = input_text[:2000].strip()
    video_prefix = VIDEO_PROMPT_PREFIX if is_youtube else ''

    return f"""{voice_prefix}{video_prefix}You are an expert viral content strategist. Write in {tone_desc}.{niche_context}

SOURCE CONTENT:
{trimmed_input}

Create social media content based on the source above. Sound human, not AI. Lead with the most surprising insight. Use specific numbers where possible.

Platforms needed:
{instructions_text}

IMPORTANT: Respond with ONLY valid JSON — no explanation, no preamble, no markdown code blocks. Just the raw JSON object.
Format:
{{{platforms_json_keys and ", ".join(f'"{p}": "content here"' for p in platforms)}}}

Use \\n for line breaks within strings. Plain text only in values."""


def parse_response(text: str, platforms: list) -> dict:
    """Parse JSON response from Claude. Falls back to empty strings on failure."""
    # Strip markdown code fences if Claude added them anyway
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()

    try:
        data = json.loads(text)
        return {p: str(data.get(p, '')).strip() for p in platforms}
    except json.JSONDecodeError:
        # Try to extract JSON object from within the text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return {p: str(data.get(p, '')).strip() for p in platforms}
            except json.JSONDecodeError:
                pass
        return {p: '' for p in platforms}


def generate_content(input_text: str, platforms: list, tone: str, is_youtube: bool = False, voice_prefix: str = "", niche_context: str = "") -> dict:
    """
    Generate social media content using Claude Haiku.
    Synchronous function — safe to call from async FastAPI routes.
    """
    if not input_text or len(input_text.strip()) < 50:
        raise Exception("Input text too short. Please provide more content.")

    if not platforms:
        raise Exception("Please select at least one platform.")

    prompt = build_prompt(input_text, platforms, tone, is_youtube=is_youtube, voice_prefix=voice_prefix, niche_context=niche_context)

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        print(f"\n[AI] Raw response (first 300 chars): {response_text[:300]}")

        if not response_text or len(response_text) < 10:
            raise Exception("AI returned empty response. Please try again.")

        result = parse_response(response_text, platforms)
        print(f"[AI] Parsed keys: { {k: len(v) for k, v in result.items()} }")

        has_content = any(len(v) > 20 for v in result.values())
        if not has_content:
            print(f"[AI] Parse failed — raw response:\n{response_text[:500]}")
            raise Exception("Content generation failed. Please try again.")

        return result

    except anthropic.AuthenticationError:
        raise Exception("API key invalid. Check your .env file.")
    except anthropic.RateLimitError:
        raise Exception("Rate limit hit. Please wait 60 seconds and try again.")
    except anthropic.BadRequestError as e:
        raise Exception(f"Bad request: {str(e)}")
    except Exception as e:
        raise Exception(str(e))


def _build_video_plan_prompt(script: str, duration_seconds: int) -> str:
        return f"""You are a short-form video strategist and SEO expert.

TASK:
Given a raw short-video script, produce an optimized version for retention and SEO, then return ONLY valid JSON.

CONTEXT:
- Target: faceless 9:16 short video
- Duration target: {duration_seconds} seconds
- Platforms: YouTube Shorts, Instagram Reels, TikTok

INPUT SCRIPT:
{script.strip()}

OUTPUT JSON FORMAT (strict):
{{
    "final_script": "...",
    "hook": "...",
    "body": "...",
    "cta": "...",
    "retention_notes": ["...", "..."],
    "scenes": [
        {{
            "scene": 1,
            "start": 0.0,
            "end": 2.5,
            "part": "hook",
            "visual_description": "...",
            "keywords": ["...", "..."],
            "on_screen_text": "...",
            "energy": "urgency"
        }}
    ],
    "platform_meta": {{
        "youtube_shorts": {{
            "title": "...",
            "description": "...",
            "hashtags": "#... #... #..."
        }},
        "reels": {{
            "title": "...",
            "description": "...",
            "hashtags": "#... #... #..."
        }},
        "tiktok": {{
            "title": "...",
            "description": "...",
            "hashtags": "#... #... #..."
        }}
    }}
}}

RULES:
- Return only JSON, no markdown.
- Keep script human, specific, and concise.
- Scene count must be 2 to 5.
- Ensure scene timings fit total duration.
- Make SEO metadata search-friendly with intent keywords.
"""


def generate_video_plan(script: str, duration_seconds: int = 12) -> dict:
        if not script or len(script.strip()) < 20:
                raise Exception("Script is too short for video planning.")

        prompt = _build_video_plan_prompt(script, duration_seconds)

        try:
                message = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=2500,
                        messages=[{"role": "user", "content": prompt}],
                )

                response_text = (message.content[0].text or "").strip()
                if response_text.startswith("```"):
                        response_text = re.sub(r'^```[a-zA-Z]*\\n?', '', response_text)
                        response_text = re.sub(r'\\n?```$', '', response_text).strip()

                try:
                        parsed = json.loads(response_text)
                except json.JSONDecodeError:
                        match = re.search(r'\{.*\}', response_text, re.DOTALL)
                        if not match:
                                raise Exception("Claude returned invalid JSON for video plan.")
                        parsed = json.loads(match.group())

                return parsed

        except anthropic.AuthenticationError:
                raise Exception("API key invalid. Check ANTHROPIC_API_KEY.")
        except anthropic.RateLimitError:
                raise Exception("Rate limit hit. Please retry in a moment.")
        except Exception as e:
                raise Exception(str(e))

