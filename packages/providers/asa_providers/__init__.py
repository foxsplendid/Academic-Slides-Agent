"""asa_providers — real LLM adapters (OpenAI-compatible, Anthropic) for the LLM Protocol."""

from __future__ import annotations

import os

from .anthropic_llm import AnthropicLLM
from .openai_compat import OpenAICompatibleLLM
from .profiles import known_openai_profiles, openai_for_profile, resolve_openai_profile

__all__ = [
    "OpenAICompatibleLLM",
    "AnthropicLLM",
    "provider_from_env",
    "resolve_openai_profile",
    "known_openai_profiles",
]


def provider_from_env():
    """Construct an adapter selected by ``ASA_LLM_PROVIDER`` (default ``openai``).

    Accepts a named OpenAI-compatible profile (openai/deepseek/mimo) or ``anthropic``.
    """
    name = os.environ.get("ASA_LLM_PROVIDER", "openai").strip().lower()
    if name == "anthropic":
        return AnthropicLLM()
    if name in ("openai-compatible", "openai_compatible"):
        name = "openai"
    if name in known_openai_profiles():
        return openai_for_profile(name)
    raise ValueError(
        f"unknown ASA_LLM_PROVIDER: {name!r} (use one of {known_openai_profiles()} or 'anthropic')"
    )
