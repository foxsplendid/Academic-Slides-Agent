"""Provider-agnostic LLM seam.

The agents never import a vendor SDK; they depend only on the ``LLM`` Protocol. Real adapters
(OpenAI / Anthropic / OpenAI-compatible) implement it in a later change. ``FakeLLM`` enables
deterministic unit tests with no network.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class LLM(Protocol):
    def complete(self, prompt: str, *, system: Optional[str] = None) -> str:
        """Return a completion for ``prompt`` (with an optional ``system`` instruction)."""
        ...


class FakeLLM:
    """A scripted LLM for tests/dev. Returns queued responses in order (repeating the last),
    and records every call for assertions."""

    def __init__(self, *responses: str) -> None:
        if not responses:
            raise ValueError("FakeLLM needs at least one scripted response")
        self._responses = list(responses)
        self._index = 0
        self.calls: list[dict] = []

    def complete(self, prompt: str, *, system: Optional[str] = None) -> str:
        self.calls.append({"prompt": prompt, "system": system})
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return response
