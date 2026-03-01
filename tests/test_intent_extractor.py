"""Intent extractor tests using mocked LLM responses."""

from __future__ import annotations

import json

from app.llm.intent_extractor import extract_intent
from app.llm.llm_client import LLMClient


def test_extract_intent_returns_valid_result_for_happy_path() -> None:
    client = LLMClient(
        backend=lambda prompt: json.dumps(
            {
                "intent": "turn_on",
                "target": {
                    "room": "living_room",
                    "entity_id": None,
                    "device_type": "light",
                },
                "params": {"brightness_pct": None, "temperature_f": None},
                "confidence": 0.98,
                "needs_clarification": False,
                "clarification_question": None,
            }
        )
    )

    result = extract_intent("turn on the living room lights", client)

    assert result.intent == "turn_on"
    assert result.needs_clarification is False
    assert result.target.room == "living_room"


def test_extract_intent_repairs_malformed_json_once() -> None:
    responses = iter(
        [
            '{"intent":"turn_on"',
            json.dumps(
                {
                    "intent": "turn_on",
                    "target": {
                        "room": "living_room",
                        "entity_id": None,
                        "device_type": "light",
                    },
                    "params": {"brightness_pct": None, "temperature_f": None},
                    "confidence": 0.9,
                    "needs_clarification": False,
                    "clarification_question": None,
                }
            ),
        ]
    )
    client = LLMClient(backend=lambda prompt: next(responses))

    result = extract_intent("turn on the living room lights", client, max_repair=1)

    assert result.intent == "turn_on"
    assert result.needs_clarification is False


def test_extract_intent_fails_closed_for_low_confidence() -> None:
    client = LLMClient(
        backend=lambda prompt: json.dumps(
            {
                "intent": "turn_on",
                "target": {"room": None, "entity_id": None, "device_type": "light"},
                "params": {"brightness_pct": None, "temperature_f": None},
                "confidence": 0.32,
                "needs_clarification": False,
                "clarification_question": None,
            }
        )
    )

    result = extract_intent("turn on the lights", client, confidence_threshold=0.75)

    assert result.needs_clarification is True
    assert result.clarification_question == "Which room did you mean?"


def test_extract_intent_blocks_unsafe_domains() -> None:
    client = LLMClient(backend=lambda prompt: "{}")

    result = extract_intent("unlock the front door", client)

    assert result.needs_clarification is True
    assert "not supported" in result.clarification_question


def test_extract_intent_fails_closed_when_repair_is_exhausted() -> None:
    client = LLMClient(backend=lambda prompt: "not json")

    result = extract_intent("turn on the lamp", client, max_repair=1)

    assert result.needs_clarification is True
    assert result.clarification_question == "Please rephrase that request."
