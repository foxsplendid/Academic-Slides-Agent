"""OpenAI-compatible LLM adapter.

One adapter for any Chat Completions endpoint — OpenAI, DeepSeek, aggregators, and local
Ollama/vLLM — selected via ``base_url`` + ``api_key``. The ``openai`` SDK is imported lazily so
``import asa_providers`` needs no SDK; pass ``client=`` to inject a mock in tests.
"""

from __future__ import annotations

import os
from typing import Optional


class OpenAICompatibleLLM:
    def __init__(
        self,
        *,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        client=None,
    ) -> None:
        self.model = model or os.environ.get("ASA_OPENAI_MODEL", "gpt-4o-mini")
        env_t = os.environ.get("ASA_TEMPERATURE")
        self.temperature = float(env_t) if env_t else temperature
        env_mt = os.environ.get("ASA_MAX_TOKENS")  # cap runaway decode (latency); default unset
        self.max_tokens = max_tokens if max_tokens is not None else (int(env_mt) if env_mt and env_mt.isdigit() else None)
        if client is not None:
            self._client = client
        else:
            from openai import OpenAI  # lazy — only needed for a real client

            self._client = OpenAI(
                api_key=api_key or os.environ.get("ASA_OPENAI_API_KEY"),
                base_url=base_url or os.environ.get("ASA_OPENAI_BASE_URL"),
            )

    def complete(self, prompt: str, *, system: Optional[str] = None) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        kwargs = {"model": self.model, "messages": messages, "temperature": self.temperature}
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def complete_vision(self, prompt: str, *, images, system: Optional[str] = None) -> str:
        """Multimodal completion (OpenAI-compatible image_url content parts). Requires a vision model."""
        import base64
        from pathlib import Path

        content: list[dict] = [{"type": "text", "text": prompt}]
        for img in images:
            b64 = base64.b64encode(Path(img).read_bytes()).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})
        kwargs = {"model": self.model, "messages": messages, "temperature": self.temperature}
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
