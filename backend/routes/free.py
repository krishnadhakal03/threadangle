import os
import json
from fastapi import APIRouter, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from anthropic import AsyncAnthropic
from pydantic import BaseModel

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class HookRequest(BaseModel):
    topic: str
    category: str

MAX_TOPIC_LENGTH = 500  # ~125 tokens, enough for any real topic

@router.post("/generate-hooks")
@limiter.limit("5/day")
async def generate_free_hooks(request: Request, hook_req: HookRequest):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI Service unavailable")

    topic = hook_req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    if len(topic) > MAX_TOPIC_LENGTH:
        raise HTTPException(status_code=400, detail=f"Topic must be {MAX_TOPIC_LENGTH} characters or less.")

    client = AsyncAnthropic(api_key=api_key)

    user_prompt = f"""Generate 5 viral Twitter hook lines about: {topic}
Category: {hook_req.category}

Each hook must use a different psychological trigger.
Return valid JSON only, no explanation:
{{
  "hooks": [
    {{"type": "Curiosity Gap",  "text": "...", "why_it_works": "one sentence"}},
    {{"type": "Bold Claim",     "text": "...", "why_it_works": "one sentence"}},
    {{"type": "Personal Story", "text": "...", "why_it_works": "one sentence"}},
    {{"type": "Number/Stat",    "text": "...", "why_it_works": "one sentence"}},
    {{"type": "Pain Point",     "text": "...", "why_it_works": "one sentence"}}
  ]
}}"""

    try:
        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            system="You are a viral copywriting expert. Output JSON only.",
            messages=[{"role": "user", "content": user_prompt}]
        )
        return json.loads(response.content[0].text)
    except Exception as e:
        print(f"Hook Generation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate hooks")
