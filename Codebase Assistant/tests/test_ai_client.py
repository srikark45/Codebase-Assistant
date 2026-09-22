"""
Tests for the AI orchestration layer. These never hit the real
Anthropic API - RefactorAssistant accepts a client via dependency
injection, so we pass a fake one instead.
"""

import shutil

import pytest

from ai.refactor_assistant import RefactorAssistant
from ai.cache import ResponseCache


class FakeClient:
    """Stands in for AIClient; records how many times it was called."""

    def __init__(self, response_text="FAKE RESPONSE"):
        self.call_count = 0
        self.response_text = response_text

    def complete(self, prompt, max_tokens=1024, system=None):
        self.call_count += 1
        return f"{self.response_text} #{self.call_count}"


@pytest.fixture
def cache(tmp_path):
    return ResponseCache(cache_dir=str(tmp_path / "ai_cache"))


@pytest.fixture
def sample_file(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("def foo():\n    return 1\n")
    return str(f)


def test_first_call_hits_client_and_caches(sample_file, cache):
    fake = FakeClient()
    assistant = RefactorAssistant(client=fake, cache=cache)

    result = assistant.run(sample_file, "summarize")

    assert result["from_cache"] is False
    assert fake.call_count == 1
    assert "FAKE RESPONSE" in result["response"]


def test_second_call_is_served_from_cache(sample_file, cache):
    fake = FakeClient()
    assistant = RefactorAssistant(client=fake, cache=cache)

    first = assistant.run(sample_file, "summarize")
    second = assistant.run(sample_file, "summarize")

    assert first["response"] == second["response"]
    assert second["from_cache"] is True
    assert fake.call_count == 1  # no second API call


def test_different_action_is_not_cached_together(sample_file, cache):
    fake = FakeClient()
    assistant = RefactorAssistant(client=fake, cache=cache)

    assistant.run(sample_file, "summarize")
    result = assistant.run(sample_file, "refactor")

    assert result["from_cache"] is False
    assert fake.call_count == 2


def test_no_cache_flag_bypasses_cache(sample_file, cache):
    fake = FakeClient()
    assistant = RefactorAssistant(client=fake, cache=cache)

    assistant.run(sample_file, "summarize")
    result = assistant.run(sample_file, "summarize", use_cache=False)

    assert result["from_cache"] is False
    assert fake.call_count == 2


def test_unknown_action_raises(sample_file, cache):
    fake = FakeClient()
    assistant = RefactorAssistant(client=fake, cache=cache)

    with pytest.raises(ValueError):
        assistant.run(sample_file, "not_a_real_action")


def test_missing_file_raises(cache):
    fake = FakeClient()
    assistant = RefactorAssistant(client=fake, cache=cache)

    with pytest.raises(FileNotFoundError):
        assistant.run("/no/such/file.py", "summarize")
