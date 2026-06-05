# Execution Plan

This plan continues after item 1 from the original next-step list was completed.

## Done Already

### 1. Promote Hermes Patch To Durable Code

Completed.

Evidence:

```text
Hermes branch: codex/kaxis-factory-10-gates
Commit: d297c0c78900d6858384297895ef4392e6fb85b9
Tests: 72 passed
Patch: adapters/hermes/patches/0001-add-kaxis-factory-10-kanban-gates.patch
```

## Now

### 2. Update Methodology And Mind Map To Factory 10

Deliverables:

- `docs/methodology/overkill-factory-v0.md`
- `docs/maps/factory-10-flow.mmd`
- Whimsical linear map with Factory 10 gates.

Acceptance:

- The flow must be sequential.
- Every technical node must have a simple explanation.
- Product Face, Codex Security, Auditor, anti-self-review, Receipt Five, R3/R4
  human gate, and exit-code enforcement must be visible.

### 3. Automate Critical Workers

Workers to implement:

- Codex Security Runner.
- Solana/Quasar Auditor Runner.
- Product Face Validator.
- Independent Reviewer.
- Human Gate Clerk.

Acceptance:

- Each worker has a card contract.
- Each worker knows when it runs.
- Each worker writes machine-readable evidence.
- Hermes adapter can block done if the evidence is missing.

### 4. Run The First Real Product Through The Factory

Input:

- One real raw product paper.

Acceptance:

- Product SOT created.
- Architecture reviewed.
- Product Face Packet created.
- Onchain Package created when applicable.
- Security Scan Packet created.
- Decomposition generated.
- At least one real slice executed through Hermes.
- Done uses Receipt Five.

### 5. Generate V3.6 From The Pilot

Acceptance:

- List what was too heavy.
- List what was too vague.
- List what agents misread.
- List what humans had to clarify.
- Update contracts and methodology.

## Immediate Next Work Order

1. Publish Overkill Factory repository. Done.
2. Install the Codex skill locally. Done.
3. Create or update the Whimsical flow map. Mermaid source updated; Whimsical
   MCP is still required for the editable Whimsical board.
4. Start worker automation specs. Done as `scripts/factoryctl.py`,
   `docs/automation/worker-automation-v0.md`, worker packet schema, gate report
   schema, and generated examples.
5. Choose the first real product paper for the pilot. Waiting for input paper.

## Current Remaining External Inputs

- Whimsical MCP/tool access for the editable board.
- A real raw product paper for the first pilot.
- Hermes runtime hook that calls `factoryctl.py` automatically when cards move
  toward `ready` or `done`.
