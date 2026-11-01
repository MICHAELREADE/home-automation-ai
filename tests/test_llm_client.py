"""LLM client retry behavior tests."""

from __future__ import annotations

import pytest

from app.llm.llm_client import LLMClient, create_ollama_backend


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


def test_create_ollama_backend_posts_to_generate_endpoint() -> None:
    calls: list[dict] = []

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"response": '{"intent":"turn_on"}'}

    class DummySession:
        def post(self, url: str, json: dict, timeout: float) -> DummyResponse:
            calls.append({"url": url, "json": json, "timeout": timeout})
            return DummyResponse()

    backend = create_ollama_backend(
        base_url="http://127.0.0.1:11434",
        model="qwen2.5:14b-instruct",
        timeout_seconds=12.0,
        session=DummySession(),
    )

    result = backend("extract intent")

    assert result == '{"intent":"turn_on"}'
    assert calls == [
        {
            "url": "http://127.0.0.1:11434/api/generate",
            "json": {
                "model": "qwen2.5:14b-instruct",
                "prompt": "extract intent",
                "stream": False,
            },
            "timeout": 12.0,
        }
    ]
