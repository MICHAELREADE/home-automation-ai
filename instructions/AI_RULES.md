# AI_RULES.md

This document defines mandatory behavioral rules for the coding agent and language model used in this repository.

These rules override convenience, verbosity, or creative interpretation.

The goal of this project is safe, deterministic AI-assisted development of a local-first smart home control system.

---

# 1. Architectural Principles

1. The LLM is an **intent extraction layer**, not a device controller.
2. No generated code may directly execute Home Assistant actions without passing through:
   - Schema validation
   - Guardrails
   - Deterministic executor logic
3. All structured outputs must strictly conform to defined schemas.
4. Fail closed when uncertain.
5. Clarification is preferred over guessing.

---

# 2. Structured Output Discipline

When generating intent-related logic:

- Output must be valid JSON.
- No extra keys.
- No omitted required fields.
- No hallucinated entity_ids.
- Confidence must be a float between 0 and 1.
- If ambiguous → `needs_clarification = true`.

If the model cannot comply:
- It must request clarification.
- It must not improvise.

---

# 3. Safety Constraints

The following domains are disallowed in early phases:

- Locks
- Garage doors
- Alarm systems
- Security-critical devices

The agent must not implement support for these without explicit instruction.

---

# 4. Code Generation Rules

All generated code must:

- Be modular.
- Avoid hidden side effects.
- Avoid global mutable state.
- Use explicit typing where appropriate.
- Include docstrings for public functions.
- Include error handling.
- Be testable.

No placeholder logic in production files.

---

# 5. Development Workflow Enforcement

The following rules are mandatory:

## Rule 5.1 — Tests After Every Code Generation Loop

After generating or modifying any code:

1. All relevant tests must be executed.
2. If tests fail:
   - Fix the issue.
   - Re-run tests.
   - Do not proceed until tests pass.

No code generation cycle is complete without passing tests.

---

## Rule 5.2 — Commit rules

After tests pass, and you're told to checkin or commit the work, follow these rules:

1. Create a meaningful commit.
2. Commit message must describe:
   - What changed
   - Why it changed

Do not batch commits across multiple unrelated changes.

Then request confirmation to push to github
---

# 6. Phase A Scope Enforcement

During Phase A:

- Only intent extraction logic is allowed.
- No Home Assistant execution layer unless explicitly instructed.
- No automation creation.
- No multi-step planning.
- No persistent memory layer.

Scope creep is not allowed.

---

# 7. Prompt Discipline

When generating prompts:

- Include examples.
- Demand strict JSON.
- Explicitly instruct the model not to guess.
- Provide ambiguity handling examples.
- Reinforce schema compliance.

---

# 8. Repository Structure Integrity

The following structure must be maintained:

/app
  /llm
  /core
/tests
/tools

No arbitrary file sprawl.
No duplicate logic across layers.

---

# 9. Failure Handling

If:

- Schema validation fails
- JSON parsing fails
- LLM output is malformed
- Confidence is below threshold

The system must:

- Fail closed
- Ask for clarification
- Avoid execution

---

# 10. Long-Term Goal Reminder

This system controls physical devices.

Correctness and safety > cleverness.

Determinism > creativity.

Guardrails > convenience.