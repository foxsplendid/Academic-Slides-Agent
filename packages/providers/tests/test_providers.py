"""Provider adapter tests — offline via mock clients.

Each test maps to a scenario in
openspec/changes/add-llm-providers/specs/llm-providers/spec.md.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from asa_providers import AnthropicLLM, OpenAICompatibleLLM, provider_from_env, resolve_openai_profile


class _FakeOpenAIClient:
    def __init__(self):
        self.captured = {}

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(self, **kwargs):
        self.captured = kwargs
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


def test_resolve_deepseek_profile_with_env(monkeypatch):
    # This asserts the profile *defaults*, so clear any ambient override that a stray .env
    # may have leaked into os.environ (python-dotenv's load_dotenv() walks up the tree, so a
    # parent checkout's .env can pollute the global env for the whole pytest session).
    monkeypatch.delenv("ASA_DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("ASA_LLM_MODEL", raising=False)
    monkeypatch.delenv("ASA_DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.setenv("ASA_DEEPSEEK_API_KEY", "dk")
    cfg = resolve_openai_profile("deepseek")
    assert cfg["base_url"] == "https://api.deepseek.com"
    assert cfg["api_key"] == "dk"
    assert cfg["model"] == "deepseek-chat"


def test_profile_default_is_hermetic_against_leaked_model_override(monkeypatch):
    """Regression: an ambient ASA_DEEPSEEK_MODEL (e.g. injected by python-dotenv finding a
    parent repo's .env and mutating the global os.environ) must not silently change what a
    profile-*default* test resolves. Clearing the override restores the documented default."""
    monkeypatch.setenv("ASA_DEEPSEEK_API_KEY", "dk")
    # A leaked override is honoured by resolution — this is exactly the pollution that bit the
    # default test when it ran after an app test that had loaded a stray .env:
    monkeypatch.setenv("ASA_DEEPSEEK_MODEL", "leaked-deepseek-vX")
    assert resolve_openai_profile("deepseek")["model"] == "leaked-deepseek-vX"
    # Clearing the overrides (what the hermetic default tests do) restores the profile default:
    monkeypatch.delenv("ASA_DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("ASA_LLM_MODEL", raising=False)
    assert resolve_openai_profile("deepseek")["model"] == "deepseek-chat"


def test_resolve_profile_env_overrides_base_url_and_model(monkeypatch):
    monkeypatch.setenv("ASA_DEEPSEEK_API_KEY", "dk")
    monkeypatch.setenv("ASA_DEEPSEEK_BASE_URL", "https://gateway.example/v1")  # private gateway override
    monkeypatch.setenv("ASA_DEEPSEEK_MODEL", "deepseek-x")
    cfg = resolve_openai_profile("deepseek")
    assert cfg == {"base_url": "https://gateway.example/v1", "api_key": "dk", "model": "deepseek-x"}


@pytest.mark.skipif(not os.environ.get("ASA_OPENAI_API_KEY"), reason="no ASA_OPENAI_API_KEY for live test")
def test_openai_live_roundtrip():
    out = OpenAICompatibleLLM().complete("Reply with the single word OK.", system="Be terse.")
    assert isinstance(out, str) and out


def test_max_tokens_forwarded_when_set():
    client = _FakeOpenAIClient()
    llm = OpenAICompatibleLLM(model="m", max_tokens=900, client=client)
    llm.complete("hi", system="s")
    assert client.captured.get("max_tokens") == 900


def test_max_tokens_omitted_by_default():
    client = _FakeOpenAIClient()
    OpenAICompatibleLLM(model="m", client=client).complete("hi")
    assert "max_tokens" not in client.captured  # unset -> not sent (no truncation risk)
