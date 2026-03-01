"""Intent schema models and validation helpers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


IntentName = Literal[
    "turn_on",
    "turn_off",
    "set_brightness",
    "set_temperature",
    "query_state",
]
DeviceType = Literal["light", "switch", "thermostat"]


class IntentTarget(BaseModel):
    """Target information extracted from the user request."""

    model_config = ConfigDict(extra="forbid")

    room: str | None
    entity_id: str | None
    device_type: DeviceType | None


class IntentParams(BaseModel):
    """Optional parameters attached to an intent."""

    model_config = ConfigDict(extra="forbid")

    brightness_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    temperature_f: float | None = None


class IntentResult(BaseModel):
    """Validated intent result emitted by the extractor."""

    model_config = ConfigDict(extra="forbid")

    intent: IntentName
    target: IntentTarget
    params: IntentParams
    confidence: float = Field(ge=0.0, le=1.0)
    needs_clarification: bool
    clarification_question: str | None


def validate_intent(obj: dict) -> IntentResult:
    """Validate a raw mapping against the strict intent schema."""

    return IntentResult.model_validate(obj)


def get_intent_json_schema() -> dict:
    """Return the JSON schema used to constrain LLM responses."""

    return IntentResult.model_json_schema()


__all__ = [
    "IntentParams",
    "IntentResult",
    "IntentTarget",
    "ValidationError",
    "get_intent_json_schema",
    "validate_intent",
]
