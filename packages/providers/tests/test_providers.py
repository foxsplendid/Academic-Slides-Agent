"""Provider adapter tests — offline via mock clients.

Each test maps to a scenario in
openspec/changes/add-llm-providers/specs/llm-providers/spec.md.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from asa_providers import AnthropicLLM, OpenAICompatibleLLM, provider_from_env


class _FakeOpenAIClient:
    def __init__(self):
        self.captured = {}

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(self, *, model, messages, temperature):
        self.captured = {"model": model, "messages": messages, "temperature": temperature}
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="HELLO_IR"))])


class _FakeAnthropicClient:
    def __init__(self):
        self.captured = {}

    @property
    def messages(self):
        return self

    def create(self, **kwargs):
        self.captured = kwargs
        return SimpleNamespace(content=[SimpleNamespace(text="ANTHRO"), SimpleNamespace(text="_IR")])


def test_openai_builds_messages_and_extracts_content():
    client = _FakeOpenAIClient()
    out = OpenAICompatibleLLM(model="m1", client=client).complete("the prompt", system="sys")
    assert out == "HELLO_IR"
    assert client.captured["model"] == "m1"
    assert [m["role"] for m in client.captured["messages"]] == ["system", "user"]
    assert client.captured["messages"][1]["content"] == "the prompt"


def test_openai_omits_system_when_absent():
    client = _FakeOpenAIClient()
    OpenAICompatibleLLM(client=client).complete("p")
    assert [m["role"] for m in client.captured["messages"]] == ["user"]


def test_anthropic_builds_request_and_joins_blocks():
    client = _FakeAnthropicClient()
    out = AnthropicLLM(model="claude-x", client=client).complete("p", system="sys")
    assert out == "ANTHRO_IR"
    assert client.captured["model"] == "claude-x"
    assert client.captured["system"] == "sys"
    assert client.captured["messages"][0]["content"] == "p"


def test_adapters_satisfy_llm_protocol():
    from asa_agents import LLM

    assert isinstance(OpenAICompatibleLLM(client=_FakeOpenAIClient()), LLM)
    assert isinstance(AnthropicLLM(client=_FakeAnthropicClient()), LLM)


def test_provider_from_env_unknown_raises(monkeypatch):
    monkeypatch.setenv("ASA_LLM_PROVIDER", "nope")
    with pytest.raises(ValueError):
        provider_from_env()


@pytest.mark.skipif(not os.environ.get("ASA_OPENAI_API_KEY"), reason="no ASA_OPENAI_API_KEY for live test")
def test_openai_live_roundtrip():
    out = OpenAICompatibleLLM().complete("Reply with the single word OK.", system="Be terse.")
    assert isinstance(out, str) and out
