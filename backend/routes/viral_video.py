from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.openai_client import chat_complete

router = APIRouter(prefix="/api/generate", tags=["ViralVideo"])

# Niche prompt templates (expand as needed)
NICHE_TEMPLATES = {
    "ai": {
        "tone": "witty",
        "emotional_triggers": "curiosity, surprise, future shock",
        "template": "You are an AI/Tech viral video scriptwriter. Use curiosity, surprise, and future shock. Make the viewer feel they're missing out if they don't watch."
    },
    "health": {
        "tone": "bold",
        "emotional_triggers": "fear, hope, urgency",
        "template": "You are a Health/Wellness viral video scriptwriter. Use fear, hope, and urgency. Make the viewer feel this info could change their life or health."
    },
    "crime": {
        "tone": "controversial",
        "emotional_triggers": "shock, suspense, intrigue",
        "template": "You are a Crime/True Crime viral video scriptwriter. Use shock, suspense, and intrigue. Make the viewer feel they must know what happens next."
    }
}

class ViralScriptRequest(BaseModel):
    topic: str
    niche: str
    duration: int  # seconds

class ViralScriptResponse(BaseModel):
    scenes: list
    raw_script: str
    prompt_used: str

@router.post("/viral-script", response_model=ViralScriptResponse)
async def generate_viral_script(req: ViralScriptRequest):
    niche = req.niche.lower()
    if niche not in NICHE_TEMPLATES:
        raise HTTPException(status_code=400, detail="Unsupported niche")
    template = NICHE_TEMPLATES[niche]
    # Compose prompt
    prompt = f"""
{template['template']}

Write a script for a faceless, high-retention viral video on the topic: '{req.topic}'.

Structure:
HOOK (0-3 sec): [grab attention]
BUILDUP (3-7 sec): [set up curiosity or suspense]
VALUE (7-80%): [deliver main info, keep fast pace, use pattern interrupts every 3-5 sec]
CTA (final 2-5 sec): [call to action, e.g., follow, like, comment]

Rules:
- Use emotionally engaging language ({template['emotional_triggers']})
- Insert a pattern interrupt every 3-5 seconds (zoom, popup, sfx, scene change)
- Keep sentences short and punchy
- Output as a JSON array: [{{ "time": "0-3", "text": "...", "scene": "..." }}, ...]
- Duration: {req.duration} seconds
- Do NOT include any explanation, only the JSON array
"""
    try:
        content = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4",
            max_tokens=1200,
            temperature=1.05,
        )
        # Parse JSON array from response
        import json
        try:
            if content.startswith("```"):
                content = content.split("```", 2)[1]
            scenes = json.loads(content)
        except Exception:
            # Fallback: try to extract JSON array
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                scenes = json.loads(match.group())
            else:
                raise ValueError("Could not parse JSON array from model output.")
        return ViralScriptResponse(scenes=scenes, raw_script=content, prompt_used=prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")
