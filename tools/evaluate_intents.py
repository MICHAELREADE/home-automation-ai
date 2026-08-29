"""Run the Phase A.1 prompt corpus against a local Ollama model."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.input_handler import handle_typed_input
from app.llm.llm_client import create_ollama_client
from app.llm.schema import IntentResult

DEFAULT_CASES_PATH = Path(__file__).with_name("intent_eval_cases.json")


@dataclass(frozen=True)
class EvaluationResult:
    """The outcome of matching one evaluated intent against its expectation."""

    name: str
    passed: bool
    failures: list[str]


def load_cases(path: Path) -> list[dict[str, Any]]:
    """Load the JSON prompt corpus from disk."""

    with path.open(encoding="utf-8") as source:
        cases = json.load(source)
    if not isinstance(cases, list):
        raise ValueError("Evaluation corpus must be a JSON array.")
    return cases


def evaluate_result(case: dict[str, Any], result: IntentResult) -> EvaluationResult:
    """Compare one validated intent result to its expected fields."""

    expected = case["expected"]
    failures: list[str] = []
    _compare_field(failures, "intent", result.intent, expected)
    _compare_field(
        failures,
        "needs_clarification",
        result.needs_clarification,
        expected,
    )

    expected_target = expected.get("target", {})
    for field in ("room", "entity_id", "device_type"):
        _compare_field(failures, f"target.{field}", getattr(result.target, field), expected_target)

    expected_params = expected.get("params", {})
    for field in ("brightness_pct", "temperature_f"):
        _compare_field(failures, f"params.{field}", getattr(result.params, field), expected_params)

    if expected.get("requires_clarification_question") and not result.clarification_question:
        failures.append("clarification_question: expected a non-empty value")

    return EvaluationResult(
        name=case["name"],
        passed=not failures,
        failures=failures,
    )


def _compare_field(
    failures: list[str],
    field: str,
    actual: Any,
    expected: dict[str, Any],
) -> None:
    """Record a mismatch only when the corpus specifies an expected field."""

    key = field.rsplit(".", maxsplit=1)[-1]
    if key in expected and actual != expected[key]:
        failures.append(f"{field}: expected {expected[key]!r}, got {actual!r}")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the evaluation runner."""

    parser = argparse.ArgumentParser(
        description="Evaluate Phase A.1 intent extraction against local Ollama."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Path to the JSON evaluation corpus.",
    )
    parser.add_argument("--model", help="Override the configured Ollama model.")
    parser.add_argument("--base-url", help="Override the Ollama base URL.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Evaluate every corpus case and return a nonzero status on any failure."""

    args = build_parser().parse_args(argv)
    cases = load_cases(args.cases)
    client = create_ollama_client(model=args.model, base_url=args.base_url)
    passed = 0

    for case in cases:
        try:
            result = handle_typed_input(case["text"], client)
            evaluation = evaluate_result(case, result)
        except Exception as exc:
            evaluation = EvaluationResult(
                name=case["name"],
                passed=False,
                failures=[f"runtime error: {exc}"],
            )

        if evaluation.passed:
            passed += 1
            print(f"PASS  {evaluation.name}")
        else:
            print(f"FAIL  {evaluation.name}")
            for failure in evaluation.failures:
                print(f"      {failure}")

    total = len(cases)
    percentage = (passed / total * 100) if total else 0.0
    print(f"\nResult: {passed}/{total} passed ({percentage:.1f}%).")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
