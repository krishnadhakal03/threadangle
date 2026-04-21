import json
from typing import List, Dict

from utils.openai_client import chat_complete


def _fallback_titles(topic: str) -> List[str]:
    base = topic.strip()[:60]
    return [
        f"This Changed Everything About {base}",
        f"No One Is Talking About {base}",
        f"This Should Be Illegal: {base}",
    ]


def _fallback_hashtags(keywords: List[str]) -> List[str]:
    tags = [k.strip().replace(" ", "") for k in (keywords or []) if k.strip()]
    base = ["#viral", "#shorts", "#reels", "#tiktok", "#trending"]
    return base + [f"#{t}" for t in tags[:10]]


def generate_seo(topic: str, niche: str, keywords: List[str]) -> Dict[str, object]:
    if not topic:
        raise ValueError("Topic is required for SEO generation.")

    prompt = (
        "You are a viral video SEO strategist. Create 3 titles, a keyword-rich description, "
        "and 10-15 hashtags. Use hooks like: 'This Changed Everything', 'No One Is Talking About This', "
        "and 'This Should Be Illegal'. Return ONLY valid JSON with keys: titles, description, hashtags."\
        f"\nTopic: {topic}\nNiche: {niche}\nKeywords: {', '.join(keywords or [])}"
    )

    try:
        text = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4",
            max_tokens=800,
            temperature=0.8,
        )
        data = json.loads(text)
        return {
            "titles": data.get("titles") or _fallback_titles(topic),
            "description": data.get("description") or f"Discover {topic}.",
            "hashtags": data.get("hashtags") or _fallback_hashtags(keywords or []),
        }
    except Exception:
        return {
            "titles": _fallback_titles(topic),
            "description": f"Discover {topic}.",
            "hashtags": _fallback_hashtags(keywords or []),
        }
