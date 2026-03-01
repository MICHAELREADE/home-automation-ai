"""LLM client retry behavior tests."""

from __future__ import annotations

import pytest

from app.llm.llm_client import LLMClient


def test_llm_client_retries_then_succeeds() -> None:
    attempts = {"count": 0}

    def flaky_backend(prompt: str) -> str:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("transient failure")
        return '{"ok": true}'

    sleeps: list[float] = []
    client = LLMClient(
        backend=flaky_backend,
        max_retries=2,
        backoff_seconds=0.1,
        sleep=sleeps.append,
    )

    result = client.call("hello")

    assert result == '{"ok": true}'
    assert attempts["count"] == 2
    assert sleeps == [0.1]


def test_llm_client_raises_after_retries() -> None:
    client = LLMClient(
        backend=lambda prompt: (_ for _ in ()).throw(RuntimeError("boom")),
        max_retries=1,
        sleep=lambda seconds: None,
    )

    with pytest.raises(RuntimeError, match="LLM call failed after retries."):
        client.call("hello")
