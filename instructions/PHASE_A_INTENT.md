# PHASE_A_INTENT.md — Phase A (Conversational Control) Build Plan

## 0) Goal of Phase A
Deliver a reliable “conversational control” loop for Home Assistant where **typed input** (voice later) is translated into **strict JSON intent objects**.

**This document is only Phase A.**  
No agentic planning, no “why” reasoning, no automations creation yet.

## 1) Phase A Success Criteria (Definition of Done)
Phase A is “done” when:

1. User provides a typed command (string).
2. System returns a valid JSON object matching the **Intent Schema** every time.
3. For straightforward requests, intent is correct ≥90% in your home’s vocabulary.
4. For ambiguous/unsafe requests, the model sets `needs_clarification=true` and provides a clear `clarification_question`.
5. No free-form LLM text is accepted. If parsing fails, the system fails closed (asks to rephrase).

> Phase A ends at “LLM → intent JSON”.  
> Home Assistant execution is Phase A.2+ (later phases below), but not required for Phase A.1.

---

## 2) Phase A Phases (numbered)

### A.1 — Intent Extraction from Typed Input (LLM-only)
**Purpose:** Convert user text → strict intent JSON.

**Inputs**
- `text`: string (typed command)

**Outputs**
- `intent_json`: strict JSON matching schema (no extra keys)

**Key behaviors**
- Map natural language into one of the supported intents.
- If target is missing/ambiguous: set `needs_clarification=true`.
- Confidence reflects how sure the model is, not vibes.

**Constraints**
- Must output JSON only.
- Must follow schema exactly.
- Must not invent entity_ids unless user provided one.

**Done when**
- 20+ test prompts return valid JSON and correct intent classification
- ambiguous prompts reliably trigger clarification

---

### A.2 — JSON Validation + Repair Loop (Deterministic)
**Purpose:** Keep the system safe and predictable when the model misbehaves.

**Inputs**
- raw LLM output string

**Outputs**
- validated `Intent` object (or a safe clarification response)

**Rules**
- Parse JSON strictly.
- Validate against schema (Pydantic/JSONSchema).
- If invalid:
  - Attempt one “repair” prompt (LLM) OR
  - Fail closed with “Please rephrase” (simpler, recommended for v0)

**Done when**
- Invalid/malformed outputs never reach downstream logic
- System always returns either a valid `Intent` or a clarification prompt

---

### A.3 — Local Test Harness (CLI) + Golden Tests
**Purpose:** Make “vibe coding” measurable: fast feedback loops.

**Deliverables**
- CLI tool: `python -m app.cli "turn on the living room lights"`
- Test suite with 30–50 prompts:
  - happy paths
  - ambiguity cases
  - “unsafe” domains (locks/garage) should request clarification or refuse (configurable)

**Done when**
- You can run `pytest` and see pass/fail for intent extraction accuracy and schema validity

---

### A.4 — Entity Vocabulary + Room Name Normalization (Lightweight)
**Purpose:** Teach the system your house language before HA integration.

**Inputs**
- A small config file you control, e.g. `house_vocab.yaml`:
  - room aliases (“family room” == “living room”)
  - device type aliases (“lamp” -> “light”)

**Outputs**
- Normalized fields in intent:
  - `room` standardized
  - `device_type` standardized

**Done when**
- “family room lights” consistently maps to `room="living_room"`

---

### A.5 — (Optional) HA Stub Resolver (No Execution Yet)
**Purpose:** Prepare for HA integration without actually toggling anything.

**Behavior**
- If room/device_type known, produce a “resolved target” preview:
  - e.g. list likely entities that match, but do not call HA

**Done when**
- You can see how a command would resolve *before* you let it touch your real devices


## 3) Supported Intents for Phase A
Limit scope hard to keep it shippable:

- `turn_on`
- `turn_off`
- `set_brightness`
- `set_temperature` (optional; can defer)
- `query_state`

Explicitly excluded in Phase A:
- locks
- alarms
- garage doors
- purchasing
- “routines”
- multi-step actions

---

## 4) Intent Schema (Phase A)
All LLM outputs must conform exactly:

```json
{
  "intent": "turn_on | turn_off | set_brightness | set_temperature | query_state",
  "target": {
    "room": "string | null",
    "entity_id": "string | null",
    "device_type": "light | switch | thermostat | null"
  },
  "params": {
    "brightness_pct": "number | null",
    "temperature_f": "number | null"
  },
  "confidence": "number",
  "needs_clarification": "boolean",
  "clarification_question": "string | null"
}