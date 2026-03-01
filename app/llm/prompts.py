"""Prompt builders for intent extraction."""

from __future__ import annotations

import json


FEW_SHOT_EXAMPLES = [
    {
        "input": "turn on the living room lights",
        "output": {
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
        },
    },
    {
        "input": "turn on the lights",
        "output": {
            "intent": "turn_on",
            "target": {"room": None, "entity_id": None, "device_type": "light"},
            "params": {"brightness_pct": None, "temperature_f": None},
            "confidence": 0.41,
            "needs_clarification": True,
            "clarification_question": "Which room did you mean?",
        },
    },
    {
        "input": "are the kitchen lights on?",
        "output": {
            "intent": "query_state",
            "target": {
                "room": "kitchen",
                "entity_id": None,
                "device_type": "light",
            },
            "params": {"brightness_pct": None, "temperature_f": None},
            "confidence": 0.95,
            "needs_clarification": False,
            "clarification_question": None,
        },
    },
]


def build_intent_extraction_prompt(text: str, schema: dict) -> str:
    """Build the primary prompt for intent extraction."""

    examples = "\n\n".join(
        [
            "Example input:\n"
            f"{example['input']}\n"
            "Example output:\n"
            f"{json.dumps(example['output'], indent=2)}"
            for example in FEW_SHOT_EXAMPLES
        ]
    )
    return (
        "You are an intent extraction service for a local-first smart home assistant.\n"
        "Respond ONLY with valid JSON that matches the provided schema.\n"
        "Do not include explanations, markdown, or extra keys.\n"
        "Do not guess missing targets or invent entity_id values.\n"
        "If the request is ambiguous or unsafe, set needs_clarification to true and "
        "provide a clarification_question.\n"
        "Only use these intents: turn_on, turn_off, set_brightness, set_temperature, query_state.\n"
        "Disallowed domains include locks, garage doors, alarm systems, and security-critical devices.\n\n"
        "JSON schema:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        f"{examples}\n\n"
        "User input:\n"
        f"{text}\n"
    )


def build_repair_prompt(raw_output: str, schema: dict) -> str:
    """Build a repair prompt after malformed or invalid output."""

    return (
        "Your previous response was invalid.\n"
        "Return ONLY valid JSON that matches this schema exactly.\n"
        "Do not include explanations, markdown, or extra keys.\n"
        "If unsure, set needs_clarification to true.\n\n"
        "JSON schema:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Previous invalid output:\n"
        f"{raw_output}\n"
    )
