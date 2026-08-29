"""Schema validation tests for Phase A intent extraction."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.llm.schema import get_intent_json_schema, validate_intent


def test_validate_intent_accepts_valid_payload() -> None:
    payload = {
        "intent": "turn_on",
        "target": {"room": "living_room", "entity_id": None, "device_type": "light"},
        "params": {"brightness_pct": None, "temperature_f": None},
        "confidence": 0.92,
        "needs_clarification": False,
        "clarification_question": None,
    }

    result = validate_intent(payload)

    assert result.intent == "turn_on"
    assert result.target.room == "living_room"


def test_validate_intent_rejects_extra_keys() -> None:
    payload = {
        "intent": "turn_on",
        "target": {
            "room": "living_room",
            "entity_id": None,
            "device_type": "light",
            "alias": "lamp",
        },
        "params": {"brightness_pct": None, "temperature_f": None},
        "confidence": 0.92,
        "needs_clarification": False,
        "clarification_question": None,
    }

    with pytest.raises(ValidationError):
        validate_intent(payload)


def test_validate_intent_rejects_confidence_out_of_range() -> None:
    payload = {
        "intent": "turn_on",
        "target": {"room": "living_room", "entity_id": None, "device_type": "light"},
        "params": {"brightness_pct": None, "temperature_f": None},
        "confidence": 1.5,
        "needs_clarification": False,
        "clarification_question": None,
    }

    with pytest.raises(ValidationError):
        validate_intent(payload)


def test_validate_intent_rejects_unsupported_device_type() -> None:
    payload = {
        "intent": "turn_on",
        "target": {"room": "front_door", "entity_id": None, "device_type": "lock"},
        "params": {"brightness_pct": None, "temperature_f": None},
        "confidence": 0.61,
        "needs_clarification": True,
        "clarification_question": "That device category is not supported yet.",
    }

    with pytest.raises(ValidationError):
        validate_intent(payload)


def test_validate_intent_requires_target_without_clarification() -> None:
    payload = {
        "intent": "turn_on",
        "target": {"room": None, "entity_id": None, "device_type": "light"},
        "params": {"brightness_pct": None, "temperature_f": None},
        "confidence": 0.92,
        "needs_clarification": False,
        "clarification_question": None,
    }

    with pytest.raises(ValidationError, match="target.room or target.entity_id"):
        validate_intent(payload)


def test_json_schema_exposes_expected_top_level_fields() -> None:
    schema = get_intent_json_schema()

    assert "properties" in schema
    assert "intent" in schema["properties"]
    assert "confidence" in schema["properties"]
