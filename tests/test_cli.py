"""CLI tests for manual A.1 extraction entrypoint."""

from __future__ import annotations

import json

from app import cli
from app.llm.schema import IntentResult


def test_create_client_uses_ollama_backend_defaults() -> None:
    args = cli.build_parser().parse_args(["turn on the living room lights"])

    client = cli.create_client(args)

    assert client is not None


def test_cli_main_prints_intent_json(monkeypatch, capsys) -> None:
    result = IntentResult(
        intent="turn_on",
        target={"room": "living_room", "entity_id": None, "device_type": "light"},
        params={"brightness_pct": None, "temperature_f": None},
        confidence=0.98,
        needs_clarification=False,
        clarification_question=None,
    )

    monkeypatch.setattr(cli, "create_client", lambda args: object())
    monkeypatch.setattr(cli, "handle_typed_input", lambda text, client: result)

    exit_code = cli.main(["turn on the living room lights"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["intent"] == "turn_on"
    assert output["target"]["room"] == "living_room"
