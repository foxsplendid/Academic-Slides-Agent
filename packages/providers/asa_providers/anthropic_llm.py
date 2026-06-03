"""Anthropic (Claude) LLM adapter.

The ``anthropic`` SDK is imported lazily; pass ``client=`` to inject a mock in tests.
"""

from __future__ import annotations

import os
from typing import Optional


class AnthropicLLM:
    def __init__(
        self,
        *,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        client=None,
    ) -> None:
        self.model = model or os.environ.get("ASA_ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        self.max_tokens = max_tokens
        self.temperature = temperature
        if client is not None:
            self._client = client
        else:
            from anthropic import Anthropic  # lazy

            self._client = Anthropic(api_key=api_key or os.environ.get("ASA_ANTHROPIC_API_KEY"))

    def complete(self, prompt: str, *, system: Optional[str] = None) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system  # Anthropic passes system separately, not as a message
        response = self._client.messages.create(**kwargs)
        return "".join(getattr(block, "text", "") for block in response.content)
