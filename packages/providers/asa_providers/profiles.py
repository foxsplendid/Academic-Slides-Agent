"""Named OpenAI-compatible provider profiles + environment resolution.

Built-in defaults are generic public endpoints. Account-specific endpoints (e.g. a private
gateway) come from the environment (``ASA_<NAME>_BASE_URL``) and are never committed.
"""

from __future__ import annotations

import os

from .openai_compat import OpenAICompatibleLLM

_OPENAI_PROFILES: dict[str, dict] = {
    "openai": {"base_url": None, "default_model": "gpt-4o-mini"},
    "deepseek": {"base_url": "https://api.deepseek.com", "default_model": "deepseek-chat"},
}


def known_openai_profiles() -> list[str]:
    return list(_OPENAI_PROFILES)


def resolve_openai_profile(name: str) -> dict:
    """Resolve ``{base_url, api_key, model}`` for a profile, overlaying env overrides. Pure."""
    if name not in _OPENAI_PROFILES:
        raise ValueError(f"unknown OpenAI profile: {name!r}")
    prof = _OPENAI_PROFILES[name]
    up = name.upper()
    return {
        "base_url": os.environ.get(f"ASA_{up}_BASE_URL", prof["base_url"]),
        "api_key": os.environ.get(f"ASA_{up}_API_KEY") or os.environ.get("ASA_OPENAI_API_KEY"),
        "model": os.environ.get(f"ASA_{up}_MODEL") or os.environ.get("ASA_LLM_MODEL") or prof["default_model"],
    }


def openai_for_profile(name: str) -> OpenAICompatibleLLM:
    cfg = resolve_openai_profile(name)
    return OpenAICompatibleLLM(model=cfg["model"], api_key=cfg["api_key"], base_url=cfg["base_url"])
