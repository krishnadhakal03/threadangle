"""
Hook Variations Generator
Generates 5 alternative opening hooks (curiosity, controversial, statistics, story, promise)
for each platform in a single Claude call.
"""
import json
import os
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def extract_current_hook(content: str, platform: str) -> str | None:
    """Extract the opening hook from generated content."""
    if not content:
        return None

    if platform == "twitter":
        match = re.match(r"1/\s*(.+?)(?=\n\n2/|\n2/|$)", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content.split("\n")[0].strip()

    if platform == "linkedin":
        parts = content.split("\n\n")
        return parts[0].strip() if parts else content.split(".")[0].strip() + "."

    if platform == "tiktok":
        match = re.search(r"🎬[^\n]*\n(.+?)(?=\n\n📱|$)", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content.split("\n")[0].strip()

    return content.split("\n")[0].strip()


def generate_all_hook_variations(
    ai_output: dict,
    platforms: list,
    reels_title: str = None,
    reels_description: str = None,
    shorts_title: str = None,
    shorts_description: str = None,
) -> dict | None:
    """
    Generate 5 hook variations (curiosity, controversial, stats, story, promise)
    for each platform in ONE Claude call.

    Returns {platform: [hook1, hook2, hook3, hook4, hook5]} or None on failure.
    """
    # Build platform_data: {platform: {hook, context}}
    platform_data = {}

    for p in platforms:
        content = ai_output.get(p) or ""
        if content:
            hook = extract_current_hook(content, p)
            if hook:
                platform_data[p] = {"hook": hook, "context": content[:250]}

    if reels_title:
        platform_data["reels"] = {
            "hook": reels_title,
            "context": (reels_description or "")[:250],
        }
    if shorts_title:
        platform_data["shorts"] = {
            "hook": shorts_title,
            "context": (shorts_description or "")[:250],
        }

    if not platform_data:
        return None

    print(f"\n🎣 Generating hook variations for: {list(platform_data.keys())}")

    # Build platform sections
    sections = []
    for pname, pdata in platform_data.items():
        sections.append(
            f'PLATFORM: {pname.upper()}\n'
            f'Current hook: "{pdata["hook"]}"\n'
            f'Context: {pdata["context"]}'
        )
    sections_text = "\n\n".join(sections)

    # Expected JSON template
    json_template = "\n".join(
        f'  "{p}": ["curiosity hook", "controversial hook", "statistics hook", "story hook", "promise hook"]'
        for p in platform_data
    )

    prompt = f"""You are a world-class social media hook writer. Generate 5 scroll-stopping alternative hooks for each platform below.

HOOK TYPES — generate in this exact order:
1. CURIOSITY — Irresistible information gap ("The one thing nobody tells you about...", "What nobody explains...")
2. CONTROVERSIAL — Bold challenge to conventional wisdom ("Stop doing X.", "Everyone is wrong about...", "Unpopular opinion:")
3. STATISTICS — Specific, surprising number ("87% of people make this mistake...", "Only 3% know...", "I analyzed 500...")
4. STORY — First-person personal narrative ("I tried X for 30 days...", "My biggest failure taught me...", "Last week I discovered...")
5. PROMISE — Clear, concrete outcome ("Master X in 10 minutes", "The 3-step system for...", "How to double X without...")

RULES:
- Each hook = 1-2 punchy sentences, scroll-stopping
- Match the topic and energy of the original content
- Twitter hooks: max 220 characters
- Make each hook distinctly different from the others

PLATFORMS:
{sections_text}

Return ONLY valid JSON (no markdown fences, no explanation):
{{{json_template}
}}"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        print(f"[HookGen] Response preview: {text[:150]}")

        # Strip markdown fences if present
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
            text = text.strip()

        data = json.loads(text)

        result = {}
        for p in platform_data:
            hooks = data.get(p)
            if isinstance(hooks, list) and len(hooks) == 5:
                result[p] = [str(h).strip() for h in hooks]
                print(f"   ✅ {p}: 5 hooks generated")
            else:
                print(f"   ⚠️  {p}: unexpected format — skipping")

        return result if result else None

    except (json.JSONDecodeError, KeyError) as exc:
        print(f"[HookGen] Parse error: {exc}")
        return None
    except Exception as exc:
        print(f"[HookGen] Generation failed: {exc}")
        return None
