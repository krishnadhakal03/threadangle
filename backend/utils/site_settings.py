from datetime import datetime, timedelta
from sqlalchemy import select

from models import CMSContent

_settings_cache = {}
_cache_expiry = {}
CACHE_TTL_SECONDS = 120


async def get_setting(db, key: str, default=None):
    now = datetime.utcnow()
    if key in _settings_cache and key in _cache_expiry and now < _cache_expiry[key]:
        return _settings_cache[key]

    result = await db.execute(select(CMSContent).where(CMSContent.content_key == key))
    row = result.scalar_one_or_none()
    if not row:
        _settings_cache[key] = default
        _cache_expiry[key] = now + timedelta(seconds=CACHE_TTL_SECONDS)
        return default

    value = row.content_value
    if row.content_type == "integer":
        try:
            value = int(value)
        except Exception:
            value = default
    elif row.content_type == "boolean":
        value = str(value).lower() == "true"

    _settings_cache[key] = value
    _cache_expiry[key] = now + timedelta(seconds=CACHE_TTL_SECONDS)
    return value


async def get_plan_limit(db, plan: str):
    defaults = {
        "free": 5,
        "starter": 30,
        "solo": 30,
        "pro": 100,
        "founder": 100,
    }

    if plan in ("free",):
        return await get_setting(db, "free_plan_limit", defaults[plan])
    if plan in ("starter", "solo"):
        return await get_setting(db, "starter_plan_limit", defaults[plan])
    if plan in ("pro", "founder"):
        return await get_setting(db, "pro_plan_limit", defaults[plan])

    return defaults["free"]
