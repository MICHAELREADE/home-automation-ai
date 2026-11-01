# A.1 - Implementation Steps: Intent Extraction from Typed Input

## TL;DR

Implement a small, testable intent-extraction subsystem that turns typed user text into a validated structured intent JSON object.

Current deliverables:
- strict Pydantic schema
- prompt templates
- pluggable LLM client
- extraction service with single-repair loop
- configuration defaults
- unit tests that mock the LLM

## A.1 Checklist

### 1. Define data models and validation

- [x] File: `app/llm/schema.py`
- [x] Create Pydantic models: `IntentTarget`, `IntentParams`, `IntentResult` matching the Phase A intent schema.
- [x] Add `validate_intent(obj: dict) -> IntentResult` to strictly enforce required fields, allowed values, and `confidence` in `[0.0, 1.0]`.
- [x] Export `get_intent_json_schema()` to embed into prompts.

### 2. Add prompt templates

- [x] File: `app/llm/prompts.py`
- [x] Provide an intent extraction prompt builder and few-shot examples for happy path, ambiguity, and `query_state`.
- [x] Include explicit instructions to return JSON only, avoid extra keys, avoid guessing, and set `needs_clarification=true` when unsure.

### 3. LLM client wrapper

- [x] File: `app/llm/llm_client.py`
- [x] Implement `LLMClient` with `call(prompt: str) -> str`.
- [x] Keep the backend pluggable for mock and HTTP-based local runtimes.
- [x] Add retry/backoff and timeout handling.
- [x] Allow injection of a mock backend in tests.

### 4. Intent extractor service

- [x] File: `app/llm/intent_extractor.py`
- [x] Implement `extract_intent(text: str, client: LLMClient, *, confidence_threshold: float, max_repair: int, fail_closed: bool) -> IntentResult`.
- [x] Build the prompt from user text plus JSON schema.
- [x] Call the LLM client and parse raw JSON output.
- [x] Attempt one repair prompt when the original response is malformed or invalid.
- [x] Validate parsed JSON via `validate_intent`.
- [x] Return clarification responses as-is when `needs_clarification=true`.
- [x] Fail closed on low confidence when `FAIL_CLOSED=True`.
- [x] Reject early-phase unsafe domains such as locks, garage doors, and alarms.

### 5. Typed input handler

- [x] File: `app/core/input_handler.py`
- [x] Implement `handle_typed_input(text: str, client: LLMClient)` as the typed-input integration point.
- [x] Keep it side-effect free with no Home Assistant execution.

### 6. Config and constants

- [x] File: `app/llm/config.py`
- [x] Add defaults for:
  - `INTENT_CONFIDENCE_THRESHOLD=0.75`
  - `MAX_REPAIR_ATTEMPTS=1`
  - `FAIL_CLOSED=True`
- [x] Allow env var overrides.

### 7. Tests

- [x] File: `tests/test_schema.py`
- [x] Cover schema validation, enum enforcement, extra-key rejection, and confidence bounds.
- [x] File: `tests/test_intent_extractor.py`
- [x] Cover valid JSON, malformed JSON with repair, low-confidence fail-closed behavior, and unsafe-domain blocking.
- [x] File: `tests/test_llm_client.py`
- [x] Cover retry/backoff behavior with a flaky backend.

### 8. Verification / How to run

- [x] Add project metadata so local Python tooling can run consistently.
- [x] Run automated tests successfully.
- [x] Add a dedicated manual smoke-test script or CLI entrypoint for A.1.
- [x] Verify end-to-end extraction against a real local LLM backend from the repo workflow, not just mocked tests.

Example local setup:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install pytest pydantic requests
```

Run tests:

```powershell
python -m pytest -q
```

### 9. Edge cases and rules

- [x] Do not invent `entity_id` values.
- [x] Enforce no extra keys through strict schema validation.
- [x] Fail closed on malformed JSON and schema failures.
- [x] Treat unsafe domains as unsupported in Phase A.

### 10. Prompting and repair strategy

- [x] Use a strict prompt with embedded JSON schema and few-shot examples.
- [x] Use a single repair re-prompt when the initial output is malformed or invalid.
- [x] Fail closed with clarification if repair still fails.

## Remaining A.1 Work

- [ ] Add a small CLI harness, for example `python -m app.cli "turn on the living room lights"`.
- [ ] Add Ollama-specific configuration or a thin local runner path so real local inference is part of the standard workflow.
- [x] Add a prompt corpus of at least 20 test inputs for A.1 acceptance checks.
- [x] Record expected behavior for those prompts so A.1 accuracy can be measured, not just smoke-tested.
- [x] Run the corpus against the real local model and review the reported pass rate: 20/20 passed (100.0%) with `qwen2.5:14b-instruct`.

## Decisions

- [x] `FAIL_CLOSED = True`
- [x] `CONFIDENCE_THRESHOLD = 0.75`
- [x] `MAX_REPAIR_ATTEMPTS = 1`
- [x] Validation uses `pydantic`.
- [x] Tests run with mocked LLM responses.
- [x] Local HTTP runtime support exists through the pluggable client.

## Current Status

A.1 implementation and initial acceptance evaluation are complete. The automated tests are green, and the initial 20-case corpus passed at 100.0% against the local Qwen model.
