"""Deterministic tests for the live-model evaluation scorer."""

from __future__ import annotations

from app.llm.schema import IntentResult
from tools.evaluate_intents import evaluate_result


def test_evaluate_result_accepts_matching_expected_fields() -> None:
    case = {
        "name": "living room lights",
        "expected": {
            "intent": "turn_on",
            "target": {"room": "living_room", "device_type": "light"},
            "needs_clarification": False,
        },
    }
    result = IntentResult(
        intent="turn_on",
        target={"room": "living_room", "entity_id": None, "device_type": "light"},
        params={"brightness_pct": None, "temperature_f": None},
        confidence=0.98,
        needs_clarification=False,
        clarification_question=None,
    )

    evaluation = evaluate_result(case, result)

    assert evaluation.passed is True
    assert evaluation.failures == []


def test_evaluate_result_reports_mismatched_fields() -> None:
    case = {
        "name": "ambiguous lights",
        "expected": {
            "intent": "turn_on",
            "needs_clarification": True,
            "requires_clarification_question": True,
        },
    }
    result = IntentResult(
        intent="turn_off",
        target={"room": "living_room", "entity_id": None, "device_type": "light"},
        params={"brightness_pct": None, "temperature_f": None},
        confidence=0.98,
        needs_clarification=False,
        clarification_question=None,
    )

    evaluation = evaluate_result(case, result)

    assert evaluation.passed is False
    assert "intent: expected 'turn_on', got 'turn_off'" in evaluation.failures
    assert "needs_clarification: expected True, got False" in evaluation.failures
    assert "clarification_question: expected a non-empty value" in evaluation.failures
