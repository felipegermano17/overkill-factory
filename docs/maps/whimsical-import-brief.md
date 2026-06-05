# Whimsical Import Brief

The Whimsical MCP was not exposed in the current Codex session, so the editable
Whimsical board cannot be created or updated from here yet.

Use `docs/maps/factory-10-flow.mmd` as the source of truth for the visual flow.
When Whimsical MCP is available, create a left-to-right flowchart named:

```text
Overkill Factory - Factory 10 Product Line
```

## Layout

Use one main horizontal spine:

```text
F0 -> F1 -> F2 -> F3 -> F4 -> F5 -> F6 -> F7 -> F8 -> F9 -> F10 -> F11 -> F12 -> F13 -> F14 -> F15 -> F16 -> F17 -> F18 -> VNext
```

Attach the worker lane below the matching phases:

- Product Face Validator under F5 and F13.
- Solana/Quasar Auditor Runner under F7 and F13.
- Codex Security Runner under F8 and F13.
- Independent Reviewer under F14.
- Human Gate Clerk under F9, F15, and F16.

Attach the runtime lane below F11 through F16:

- `factoryctl.py gate-report`
- worker packet creation
- Hermes ready gate
- Hermes done gate
- Receipt Five
- non-zero exit code when blocked

## Visual Rule

Every node must include the technical name and a plain-language explanation in
the same node, not as a hidden note. The map has to be understandable without a
voice-over.

## Blocking Note

Do not mark GitHub issue #1 closed until an actual Whimsical link exists and is
verified.
