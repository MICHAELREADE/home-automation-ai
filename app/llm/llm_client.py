"""Thin, pluggable LLM client wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Mapping, Protocol

from app.llm import config


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
    request_options: Mapping[str, Any] | None = None,
) -> BackendCallable:
    """Create a simple JSON-over-HTTP backend for local LLM runtimes."""

    try:
        import requests
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("requests is required for the HTTP backend.") from exc

    http_session = session or requests.Session()

    def _call(prompt: str) -> str:
        payload = {"model": model, "prompt": prompt}
        if request_options:
            payload.update(request_options)
        response = http_session.post(
            url,
            json=payload,
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


def create_ollama_backend(
    *,
    base_url: str = config.OLLAMA_BASE_URL,
    model: str = config.OLLAMA_MODEL,
    timeout_seconds: float = config.OLLAMA_TIMEOUT_SECONDS,
    session: Any = None,
) -> BackendCallable:
    """Create an Ollama-compatible backend using the local generate endpoint."""

    url = f"{base_url.rstrip('/')}{config.OLLAMA_GENERATE_PATH}"
    return create_http_backend(
        url,
        model=model,
        timeout_seconds=timeout_seconds,
        session=session,
        request_options={"stream": False},
    )


def create_ollama_client(
    *,
    base_url: str | None = None,
    model: str | None = None,
    timeout_seconds: float = config.OLLAMA_TIMEOUT_SECONDS,
    max_retries: int = config.OLLAMA_MAX_RETRIES,
    backoff_seconds: float = config.OLLAMA_BACKOFF_SECONDS,
    session: Any = None,
) -> LLMClient:
    """Create an `LLMClient` configured for a local Ollama runtime."""

    resolved_base_url = base_url or config.OLLAMA_BASE_URL
    resolved_model = model or config.OLLAMA_MODEL
    return LLMClient(
        backend=create_ollama_backend(
            base_url=resolved_base_url,
            model=resolved_model,
            timeout_seconds=timeout_seconds,
            session=session,
        ),
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    )
