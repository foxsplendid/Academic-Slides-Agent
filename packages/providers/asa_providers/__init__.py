"""asa_providers — real LLM adapters (OpenAI-compatible, Anthropic) for the LLM Protocol."""

from __future__ import annotations

import os

from .anthropic_llm import AnthropicLLM
from .openai_compat import OpenAICompatibleLLM

__all__ = ["OpenAICompatibleLLM", "AnthropicLLM", "provider_from_env"]


def provider_from_env():
    """Construct an adapter selected by ``ASA_LLM_PROVIDER`` (default ``openai``)."""
    name = os.environ.get("ASA_LLM_PROVIDER", "openai").strip().lower()
    if name in ("openai", "openai-compatible", "openai_compatible"):
        return OpenAICompatibleLLM()
    if name == "anthropic":
        return AnthropicLLM()
    raise ValueError(f"unknown ASA_LLM_PROVIDER: {name!r} (use 'openai' or 'anthropic')")
