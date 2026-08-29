"""Configuration defaults for the intent extraction subsystem."""

from __future__ import annotations

import os


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


INTENT_CONFIDENCE_THRESHOLD = _get_float("INTENT_CONFIDENCE_THRESHOLD", 0.75)
MAX_REPAIR_ATTEMPTS = _get_int("MAX_REPAIR_ATTEMPTS", 1)
FAIL_CLOSED = _get_bool("FAIL_CLOSED", True)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_GENERATE_PATH = os.getenv("OLLAMA_GENERATE_PATH", "/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b-instruct")
OLLAMA_TIMEOUT_SECONDS = _get_float("OLLAMA_TIMEOUT_SECONDS", 30.0)
OLLAMA_MAX_RETRIES = _get_int("OLLAMA_MAX_RETRIES", 2)
OLLAMA_BACKOFF_SECONDS = _get_float("OLLAMA_BACKOFF_SECONDS", 0.25)
