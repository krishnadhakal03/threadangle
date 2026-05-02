"""Backend kill-switches for paid providers.

Safety principle: paid-provider protection must live at the provider boundary,
not only in the UI payload. If a route, preview, confirmed plan, or old state
accidentally asks for a paid provider, these guards stop the call before any
external paid API request is made.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class PaidProviderBlockedError(RuntimeError):
    """Raised when a paid provider call is blocked by local safety settings."""


_FALSE_VALUES = {"0", "false", "no", "off", "disabled", "disable"}
_TRUE_VALUES = {"1", "true", "yes", "on", "enabled", "enable"}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    return default


@dataclass(frozen=True)
class PaidProviderPolicy:
    allow_paid_providers: bool
    allow_runwayml: bool
    allow_elevenlabs: bool
    allow_gemini: bool
    allow_openai: bool
    allow_anthropic: bool


def get_paid_provider_policy() -> PaidProviderPolicy:
    """Return current backend paid-provider policy.

    Defaults are intentionally conservative for local/manual QA:
    - paid providers are blocked unless explicitly enabled.
    - each provider also has its own allow flag.

    To intentionally spend later, set both:
      ALLOW_PAID_PROVIDERS=1
      ALLOW_RUNWAYML=1   # or relevant provider flag
    """

    allow_all = _env_bool("ALLOW_PAID_PROVIDERS", False)
    return PaidProviderPolicy(
        allow_paid_providers=allow_all,
        allow_runwayml=allow_all and _env_bool("ALLOW_RUNWAYML", False),
        allow_elevenlabs=allow_all and _env_bool("ALLOW_ELEVENLABS", False),
        allow_gemini=allow_all and _env_bool("ALLOW_GEMINI", False),
        allow_openai=allow_all and _env_bool("ALLOW_OPENAI", False),
        allow_anthropic=allow_all and _env_bool("ALLOW_ANTHROPIC", False),
    )


def assert_paid_provider_allowed(provider: str) -> None:
    provider_key = (provider or "").strip().lower()
    policy = get_paid_provider_policy()
    allowed = {
        "runwayml": policy.allow_runwayml,
        "runway": policy.allow_runwayml,
        "elevenlabs": policy.allow_elevenlabs,
        "gemini": policy.allow_gemini,
        "openai": policy.allow_openai,
        "anthropic": policy.allow_anthropic,
        "claude": policy.allow_anthropic,
    }.get(provider_key, False)

    if allowed:
        return

    raise PaidProviderBlockedError(
        f"Paid provider '{provider}' is blocked by backend safety policy. "
        "Set ALLOW_PAID_PROVIDERS=1 and the provider-specific ALLOW_* flag only when intentionally spending."
    )
