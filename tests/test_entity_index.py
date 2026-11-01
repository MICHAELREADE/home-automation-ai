"""Tests for read-only Home Assistant entity resolution previews."""

from __future__ import annotations

from app.ha.entity_index import EntityIndex
from app.llm.schema import IntentResult, IntentTarget


def _states() -> list[dict]:
    return [
        {
            "entity_id": "light.living_room_lamp",
            "state": "off",
            "attributes": {"friendly_name": "Living Room Lamp"},
        },
        {
            "entity_id": "light.living_room_ceiling",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Ceiling"},
        },
        {
            "entity_id": "switch.kitchen_fan",
            "state": "off",
            "attributes": {"friendly_name": "Kitchen Fan"},
        },
        {
            "entity_id": "sensor.living_room_temperature",
            "state": "70",
            "attributes": {"friendly_name": "Living Room Temperature"},
        },
    ]


def test_index_filters_to_supported_entity_domains() -> None:
    index = EntityIndex.from_states(_states())

    preview = index.preview_target(
        IntentTarget(room="living_room", entity_id=None, device_type="light")
    )

    assert [entity.entity_id for entity in preview.matches] == [
        "light.living_room_lamp",
        "light.living_room_ceiling",
    ]


def test_index_matches_room_and_device_type() -> None:
    index = EntityIndex.from_states(_states())

    preview = index.preview_target(
        IntentTarget(room="kitchen", entity_id=None, device_type="switch")
    )

    assert preview.resolved is True
    assert [entity.entity_id for entity in preview.matches] == ["switch.kitchen_fan"]


def test_index_matches_only_explicit_entity_id() -> None:
    index = EntityIndex.from_states(_states())

    preview = index.preview_target(
        IntentTarget(
            room=None,
            entity_id="light.living_room_lamp",
            device_type="light",
        )
    )

    assert preview.resolved is True
    assert preview.reason == "Matched the explicit entity_id."


def test_index_does_not_resolve_clarification_intents() -> None:
    index = EntityIndex.from_states(_states())
    intent = IntentResult(
        intent="turn_on",
        target={"room": None, "entity_id": None, "device_type": "light"},
        params={"brightness_pct": None, "temperature_f": None},
        confidence=0.4,
        needs_clarification=True,
        clarification_question="Which room did you mean?",
    )

    preview = index.preview(intent)

    assert preview.resolved is False
    assert preview.matches == ()
    assert "clarification" in preview.reason.lower()


def test_index_reports_no_match_without_guessing() -> None:
    index = EntityIndex.from_states(_states())

    preview = index.preview_target(
        IntentTarget(room="garage", entity_id=None, device_type="light")
    )

    assert preview.resolved is False
    assert preview.matches == ()
    assert "No supported entities" in preview.reason
