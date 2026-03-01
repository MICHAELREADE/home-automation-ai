"""Intent extraction service with repair and fail-closed behavior."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.llm import config
from app.llm.llm_client import LLMClient
from app.llm.prompts import build_intent_extraction_prompt, build_repair_prompt
from app.llm.schema import IntentResult, get_intent_json_schema, validate_intent

UNSAFE_KEYWORDS = ("lock", "garage", "alarm", "security")


def extract_intent(
    text: str,
    client: LLMClient,
    *,
    confidence_threshold: float = config.INTENT_CONFIDENCE_THRESHOLD,
    max_repair: int = config.MAX_REPAIR_ATTEMPTS,
    fail_closed: bool = config.FAIL_CLOSED,
) -> IntentResult:
    """Extract a validated intent from typed input using the configured LLM client."""

    stripped_text = text.strip()
    if not stripped_text:
        return _clarification_result(
            clarification_question="Please enter a home control request.",
            confidence=0.0,
        )

    if _contains_unsafe_domain(stripped_text):
        return _clarification_result(
            clarification_question=(
                "That device category is not supported yet. Please try a light, switch, or thermostat request."
            ),
            confidence=0.0,
        )

    schema = get_intent_json_schema()
    raw_output = client.call(build_intent_extraction_prompt(stripped_text, schema))
    last_error: Exception | None = None

    for attempt in range(max_repair + 1):
        try:
            parsed = _parse_json_object(raw_output)
            result = validate_intent(parsed)
            return _apply_confidence_policy(
                result,
                original_text=stripped_text,
                confidence_threshold=confidence_threshold,
                fail_closed=fail_closed,
            )
        except (json.JSONDecodeError, TypeError, ValidationError) as exc:
            last_error = exc
            if attempt >= max_repair:
                break
            raw_output = client.call(build_repair_prompt(raw_output, schema))

    if fail_closed:
        return _clarification_result(
            clarification_question="Please rephrase that request.",
            confidence=0.0,
        )
    raise RuntimeError("Intent extraction failed.") from last_error


def _parse_json_object(raw_output: str) -> dict[str, Any]:
    """Parse a raw LLM response as a JSON object."""

    parsed = json.loads(raw_output)
    if not isinstance(parsed, dict):
        raise TypeError("LLM output must decode to a JSON object.")
    return parsed


def _apply_confidence_policy(
    result: IntentResult,
    *,
    original_text: str,
    confidence_threshold: float,
    fail_closed: bool,
) -> IntentResult:
    """Apply fail-closed handling for low-confidence responses."""

    if result.needs_clarification or result.confidence >= confidence_threshold:
        return result

    if fail_closed:
        question = _infer_clarification_question(result, original_text)
        return result.model_copy(
            update={
                "needs_clarification": True,
                "clarification_question": question,
            }
        )

    return result


def _infer_clarification_question(result: IntentResult, original_text: str) -> str:
    """Choose a simple clarification prompt for uncertain results."""

    lowered = original_text.lower()
    if result.target.room is None and "room" not in lowered:
        return "Which room did you mean?"
    if result.target.device_type is None:
        return "Which device did you mean?"
    return "Please clarify what you want me to control."


def _contains_unsafe_domain(text: str) -> bool:
    """Return True when the request mentions disallowed early-phase domains."""

    lowered = text.lower()
    return any(keyword in lowered for keyword in UNSAFE_KEYWORDS)


def _clarification_result(
    *,
    clarification_question: str,
    confidence: float,
) -> IntentResult:
    """Create a fail-closed clarification response that still matches schema."""

    return IntentResult(
        intent="query_state",
        target={"room": None, "entity_id": None, "device_type": None},
        params={"brightness_pct": None, "temperature_f": None},
        confidence=confidence,
        needs_clarification=True,
        clarification_question=clarification_question,
    )
