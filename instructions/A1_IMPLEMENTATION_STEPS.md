# A.1 — Implementation Steps: Intent Extraction from Typed Input

TL;DR
Implement a small, testable intent-extraction subsystem that turns typed user text into a validated structured intent JSON object. Deliverables: Pydantic schema, LLM prompt templates, a thin pluggable LLM client, an extraction service with a single-repair loop, configuration, and unit tests that mock the LLM.

1. Define data models and validation
- File: `app/llm/schema.py`
- Create Pydantic models: `IntentTarget`, `IntentParams`, `IntentResult` matching the Phase A Intent Schema.
- Add `validate_intent(obj: dict) -> IntentResult` to strictly enforce required fields, allowed values (intent enums, device_type), and `confidence` ∈ [0.0, 1.0].
- Export `get_intent_json_schema()` to embed into prompts.

2. Add prompt templates
- File: `app/llm/prompts.py`
- Provide `INTENT_EXTRACTION_PROMPT(template_args)` and a few-shot examples (3 examples: happy path, ambiguous, query_state).
- Include explicit instructions: "Respond ONLY with valid JSON matching the provided schema. No explanations, no extra keys. If unsure, set `needs_clarification=true` and provide `clarification_question`."

3. LLM client wrapper
- File: `app/llm/llm_client.py`
- Implement `LLMClient` with `call(prompt: str) -> str`. Keep backend pluggable (`mock`, `local`, `ollama/http`).
- Add retry/backoff and timeout handling. Allow injection of a mock client in tests.

4. Intent extractor service
- File: `app/llm/intent_extractor.py`
- Implement `extract_intent(text: str, client: LLMClient, *, confidence_threshold: float, max_repair: int, fail_closed: bool) -> IntentResult`.
- Flow:
  1. Build prompt (prompt template + user text + JSON schema).
  2. Call LLM via client.
  3. Try parse LLM output as JSON; if parse fails, attempt one repair prompt (re-prompt: "Output only valid JSON matching schema. Previous output was invalid JSON: <raw>").
  4. Validate parsed JSON via `validate_intent`.
  5. If `needs_clarification=true` return result as-is. If `confidence < threshold` then:
     - If `fail_closed` → set `needs_clarification=true` and `clarification_question` (e.g., "Which room did you mean?") or return an `unknown` intent marker.
     - Else attempt single repair (re-call LLM with stricter instruction) then re-validate.

5. Typed input handler (integration point)
- File: `app/core/input_handler.py`
- Implement `handle_typed_input(text: str, client: LLMClient)` to call `extract_intent` and return the validated `IntentResult` (no HA side-effects here).

6. Config and constants
- File: `app/llm/config.py`
- Defaults: `INTENT_CONFIDENCE_THRESHOLD=0.75`, `MAX_REPAIR_ATTEMPTS=1`, `FAIL_CLOSED=True` (override via env vars).

7. Tests
- File: `tests/test_schema.py` — test schema validation, confidence clipping, enum enforcement.
- File: `tests/test_intent_extractor.py` — mock `LLMClient` to return: valid JSON, malformed JSON, low-confidence JSON; assert behavior for repair/fail-closed.
- File: `tests/test_llm_client.py` — test retry/backoff logic with a flaky backend.

8. Verification / How to run
- Install dependencies (example):
```
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install pytest pydantic requests
```
- Run tests:
```
pytest -q
```
- Manual smoke test: create a small script that constructs a `mock` LLMClient and calls `extract_intent("turn on the living room lights")` and inspects the `IntentResult`.

9. Edge cases & rules
- Do NOT invent `entity_id` values. If the user did not provide an `entity_id`, return `room` or `device_type` or set `needs_clarification=true`.
- Enforce no extra keys — reject or strip unknown keys during validation and fail-closed.
- Unsafe domains (locks, garage, alarms) should result in `needs_clarification=true` or be rejected by extractor/executor guardrails; extractor should mark such intents disallowed if detected.

10. Prompting & repair strategy
- Use a strict prompt with embedded JSON Schema snippet and 3 few-shot examples.
- Repair: single re-prompt asking to return only valid JSON; if still invalid, fail-closed and return a clarification request.

Decisions (recorded)
- Default: `FAIL_CLOSED = True` (safer). `CONFIDENCE_THRESHOLD = 0.75`. `MAX_REPAIR_ATTEMPTS = 1`.
- Validation: use `pydantic` for models and JSON schema export.
- LLM: pluggable client; tests run with `mock` backend; recommend `ollama` or local HTTP API for production.

Next steps (short)
- I will create the files listed above and add unit-test skeletons if you approve. Implement core `Intent` Pydantic model first, then `prompts.py`, then `llm_client.py`, then `intent_extractor.py`, followed by tests.
