# INTENT.md — Local Voice + LLM Smart Home (Home Assistant) v0→v1

## 0) Purpose (Why this exists)
Build a local-first smart home voice assistant that is less brittle than Alexa-style command parsing by using a local LLM for natural language understanding, while keeping reliability and safety by **not** letting the LLM directly control devices.

This project is also a “vibe coding” practice vehicle: ship in small increments, keep each step testable, and evolve from:
- (A) Conversational control
→ (B) House-state reasoning
→ (C) Agentic multi-step planning & automations

## 1) Non-Goals (for now)
- No cloud dependencies required for core functionality.
- No training / fine-tuning models.
- No “LLM writes raw Home Assistant service calls” without a deterministic safety layer.
- No complex multi-room voice hardware yet (single mic endpoint is enough).
- No always-on wake-word at v0 unless it’s easy.

## 2) High-Level Architecture
Two machines:
- **Home Assistant Node (Raspberry Pi):** Runs Home Assistant OS + device integrations.
- **AI Brain (RTX PC):** Runs local LLM + speech pipeline + middleware service.

Data flow (v0):
Voice (or typed text) → STT (optional) → Middleware → LLM (intent extraction) → Executor (rules/validation) → Home Assistant API → Response → TTS (optional)

Key principle:
**LLM produces structured intent, not device commands.**
Executor is authoritative.

## 3) Core Capabilities by Phase

### Phase A — Conversational Control (v0.1–v0.4)
Goal: reliably do basic actions from natural language.

Capabilities:
- Turn on/off lights, switches
- Set brightness, color temperature (optional)
- Set thermostat target (optional)
- Query simple state (“are the kitchen lights on?”)
- Confirm/clarify when ambiguous (“which room?”)

Interfaces:
- v0.1: text input (CLI or simple web endpoint)
- v0.2: add STT
- v0.3: add TTS
- v0.4: add wake-word (optional)

### Phase B — House-State Reasoning (v0.5–v0.7)
Goal: assistant can explain and make suggestions using HA state.

Capabilities:
- “Why is it cold?” → checks thermostat + door/window sensors (if present)
- “What’s on right now?” → summarizes active devices/rooms
- Basic conversational memory (session-level)
- Context injection: current time, room defaults, user preferences

### Phase C — Agentic Automations (v0.8–v1.0)
Goal: multi-step plans and automation proposals with approval workflow.

Capabilities:
- “Set a bedtime routine” → proposes steps, asks approval, then creates HA automation
- “If it gets above 78, cool the house” → creates rule-based automation
- Tool use: fetch HA entity registry, check states, plan, then execute safely
- “Dry-run mode” to preview actions

## 4) Safety Model (must-have)
Rules:
- LLM output must conform to a strict schema.
- Executor validates schema + allowed intents + allowed entity domains.
- Executor applies guardrails:
  - time-of-day constraints (optional later)
  - max brightness changes / rate limits
  - confirmation required for risky actions (locks, alarms, garage doors) — disabled entirely in v0
- Logging of all interpreted intents and resulting HA calls.
- Fail closed: if parse fails, ask clarifying question, do nothing.

## 5) Tech Stack (initial)
AI Brain (RTX PC):
- LLM: Ollama (local)
- Intent extraction: structured JSON schema enforced
- Middleware: Python FastAPI (or Flask for absolute minimalism)
- Optional:
  - STT: whisper.cpp
  - TTS: Piper
  - Wake word: Porcupine / OpenWakeWord (later)

HA Node:
- Home Assistant OS
- Long-lived access token for API calls
- Entities organized and named cleanly

## 6) “Done” Definition for v0 (Phase A)
A “done” v0 means:
- I can type: “turn on the living room lights”
- System returns: acknowledgement + executes the correct HA action
- If I type something ambiguous: “turn on the lights”
  - system asks: “Which room?” or uses a configured default
- Logs show:
  - raw input
  - LLM structured intent output
  - validated execution plan
  - HA API result

No voice required for v0 “done”. Text-only is acceptable.

## 7) Data Contracts (Schemas)

### 7.1 Intent Schema (LLM output)
All LLM output must be valid JSON matching:

{
  "intent": "turn_on" | "turn_off" | "set_brightness" | "set_temperature" | "query_state",
  "target": {
    "room": "string | null",
    "entity_id": "string | null",
    "device_type": "light | switch | thermostat | null"
  },
  "params": {
    "brightness_pct": "number | null",
    "temperature_f": "number | null"
  },
  "confidence": "number (0..1)",
  "needs_clarification": "boolean",
  "clarification_question": "string | null"
}

Notes:
- Either room or entity_id must be provided unless needs_clarification=true
- device_type is optional but helpful

### 7.2 Executor Output (internal)
{
  "action": "call_service" | "respond_only",
  "ha_domain": "light|switch|climate",
  "ha_service": "turn_on|turn_off|set_temperature|turn_on",
  "ha_data": { ... },
  "user_response": "string"
}

## 8) Milestones and Small Steps (Vibe Coding Plan)

### Milestone 0 — Repo + Skeleton (1 commit)
- Create repo structure
- Add INTENT.md (this file)
- Add README.md with “how to run”
- Add .env.example

### Milestone 1 — HA Connectivity Test (v0.1)
- Simple script that calls HA API to list states
- Confirm token works
- Confirm latency and error handling
Deliverable: `python tools/ha_ping.py` prints basic info.

### Milestone 2 — Text Command Endpoint (v0.2)
- FastAPI endpoint: POST /command { "text": "..." }
- Hardcode mapping for 1–2 entities (no LLM yet)
Deliverable: “turn on living room lamp” works via deterministic mapping.

### Milestone 3 — LLM Intent Extraction (v0.3)
- Integrate Ollama call
- Prompt forces JSON schema
- Validate JSON parsing + confidence threshold
Deliverable: “turn on the living room lights” produces intent JSON.

### Milestone 4 — Executor + Guardrails (v0.4)
- Convert intent → HA call deterministically
- Block disallowed domains
- Clarify if missing target
Deliverable: safe execution + clarification loop.

### Milestone 5 — Entity Resolution (v0.5)
- Pull HA entity list and build a local index
- Resolve room names → entity_ids
Deliverable: user can say room names without hardcoding entity_id.

### Milestone 6 — Voice (optional next)
- Add whisper.cpp STT pipeline
- Add piper TTS
Deliverable: speak command, system executes and replies.

## 9) Repo Structure (proposed)
/app
  main.py              # API entrypoint (FastAPI)
/app/llm
  ollama_client.py
  prompts.py
  schema.py
/app/ha
  ha_client.py
  entity_index.py
/app/core
  executor.py
  guardrails.py
  logging.py
/tools
  ha_ping.py
/tests
  test_schema.py
  test_executor.py
.env.example
README.md
INTENT.md

## 10) Testing Strategy (minimum viable)
- Unit tests:
  - schema validation
  - executor mapping for each intent
  - entity resolver for room/entity name matching
- Manual tests:
  - happy path (direct room)
  - ambiguous path (needs clarification)
  - malformed JSON from LLM (fail closed)
  - HA offline (graceful error response)

## 11) Prompts & Prompt Rules
Prompt must:
- demand strict JSON
- forbid extra keys
- include examples
- instruct model to set needs_clarification=true when unsure
- never guess an entity_id if unknown; use room/device_type or ask

## 12) Open Questions (safe defaults)
- Default room behavior:
  - If user says “turn on lights” with no room:
    - ask clarification unless a default room is configured
- Risky domains:
  - locks/garage/alarm disabled in v0
- Temperature units:
  - prefer Fahrenheit (configurable)

## 13) Success Criteria
Phase A success:
- 90%+ correct execution for basic lighting commands in your own home
- zero “random actions” from hallucinations (fail closed)
- smooth clarification prompts

Phase B success:
- assistant can answer “why” questions using HA state context

Phase C success:
- assistant proposes multi-step plans and only executes after approval