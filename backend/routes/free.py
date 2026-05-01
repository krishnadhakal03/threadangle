from fastapi import APIRouter, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field

from utils.hook_lab import build_hook_lab

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class HookRequest(BaseModel):
    topic: str
    category: str
    candidate_count: int = Field(default=8, ge=5, le=10)
    selected_hook_id: str | None = None
    override_hook: str | None = None

MAX_TOPIC_LENGTH = 500  # ~125 tokens, enough for any real topic

@router.post("/generate-hooks")
@limiter.limit("5/day")
async def generate_free_hooks(request: Request, hook_req: HookRequest):
    topic = hook_req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    if len(topic) > MAX_TOPIC_LENGTH:
        raise HTTPException(status_code=400, detail=f"Topic must be {MAX_TOPIC_LENGTH} characters or less.")

    try:
        lab = build_hook_lab(
            topic=topic,
            category=hook_req.category,
            candidate_count=hook_req.candidate_count,
            selected_hook_id=hook_req.selected_hook_id,
            override_hook=hook_req.override_hook,
        )
        return {
            **lab,
            "hooks": [
                {
                    "type": candidate["archetype"],
                    "text": candidate["text"],
                    "why_it_works": candidate["why_it_works"],
                    "score": candidate["total_score"],
                    "rank": candidate["rank"],
                }
                for candidate in lab["candidates"]
            ],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as e:
        print(f"Hook Generation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate hooks")
