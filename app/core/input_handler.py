"""Typed input integration for Phase A intent extraction."""

from __future__ import annotations

from app.llm.intent_extractor import extract_intent
from app.llm.llm_client import LLMClient
from app.llm.schema import IntentResult


def handle_typed_input(text: str, client: LLMClient) -> IntentResult:
    """Convert typed user input into a validated intent result."""

    return extract_intent(text=text, client=client)
