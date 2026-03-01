"""Thin, pluggable LLM client wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Protocol


class BackendCallable(Protocol):
    """Callable protocol for injectable LLM backends."""

    def __call__(self, prompt: str) -> str:
        """Execute a prompt and return raw text."""


@dataclass(slots=True)
class LLMClient:
    """Wrapper around a pluggable text-generation backend."""

    backend: BackendCallable
    timeout_seconds: float = 30.0
    max_retries: int = 2
    backoff_seconds: float = 0.25
    sleep: Callable[[float], None] = field(default=time.sleep)

    def call(self, prompt: str) -> str:
        """Call the backend with retry and timeout handling."""

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started_at = time.monotonic()
            try:
                response = self.backend(prompt)
                elapsed = time.monotonic() - started_at
                if elapsed > self.timeout_seconds:
                    raise TimeoutError(
                        f"LLM backend exceeded timeout of {self.timeout_seconds} seconds."
                    )
                if not isinstance(response, str):
                    raise TypeError("LLM backend must return a string.")
                return response
            except Exception as exc:  # pragma: no cover - exercised via tests
                last_error = exc
                if attempt >= self.max_retries:
                    break
                self.sleep(self.backoff_seconds * (2**attempt))
        raise RuntimeError("LLM call failed after retries.") from last_error


def create_http_backend(
    url: str,
    *,
    model: str,
    timeout_seconds: float = 30.0,
    session: Any = None,
) -> BackendCallable:
    """Create a simple JSON-over-HTTP backend for local LLM runtimes."""

    try:
        import requests
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("requests is required for the HTTP backend.") from exc

    http_session = session or requests.Session()

    def _call(prompt: str) -> str:
        response = http_session.post(
            url,
            json={"model": model, "prompt": prompt},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if "response" in payload:
            return payload["response"]
        if "text" in payload:
            return payload["text"]
        raise RuntimeError("HTTP backend response did not contain `response` or `text`.")

    return _call
