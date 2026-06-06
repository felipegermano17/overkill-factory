# Execution Plan

This plan continues after item 1 from the original next-step list was completed.

## Done Already

### 1. Promote Hermes Patch To Durable Code

Completed.

Evidence:

```text
Hermes branch: codex/overkill-factory-10-gates
Commit: d297c0c78900d6858384297895ef4392e6fb85b9
Tests: 72 passed
Patch: adapters/hermes/patches/0001-add-overkill-factory-10-kanban-gates.patch
```

## Now

### 2. Update Methodology And Mind Map To Factory 10

Completed.

Deliverables:

- `docs/methodology/overkill-factory-v0.md`
- `docs/maps/factory-10-flow.mmd`
- `docs/maps/whimsical-board.md`
- Whimsical linear flow map with Factory 10 gates.

Acceptance:

- The flow must be sequential.
- Every technical node must have a simple explanation.
- Product Face, Codex Security, Auditor, anti-self-review, Receipt Five, R3/R4
  human gate, and exit-code enforcement must be visible.

### 3. Automate Critical Workers

Completed for V0 contracts and evidence records.

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

### 4. Run The First Test Product Through The Factory

Completed as a dry pilot.

Input:

- `pilots/quasar-vault-guard-test/00-raw-paper.md`

Acceptance:

- Product SOT created.
- Architecture reviewed.
- Product Face Packet created.
- Onchain Package created when applicable.
- Security Scan Packet created.
- Decomposition generated.
- At least one real slice executed through Hermes.
- Done uses Receipt Five.

Evidence:

```text
Hermes board: overkill-factory-pilot-10
Hermes task: public-methodology-card
Status: done
Pilot folder: pilots/quasar-vault-guard-test
```

### 5. Generate V3.6 From The Pilot

Completed for dry-pilot learnings.

Acceptance:

- List what was too heavy.
- List what was too vague.
- List what agents misread.
- List what humans had to clarify.
- Update contracts and methodology.

## Immediate Next Work Order

1. Publish Overkill Factory repository. Done.
2. Install the Codex skill locally. Done.
3. Create or update the Whimsical flow map. Done:
   `docs/maps/whimsical-board.md`.
4. Start worker automation specs. Done as `scripts/factoryctl.py`,
   `docs/automation/worker-automation-v0.md`, worker packet schema, gate report
   schema, and generated examples.
5. Run a test-paper dry pilot. Done:
   `pilots/quasar-vault-guard-test`.

## Current Remaining External Inputs

- A real raw product paper for the first production-intent pilot.
- Hermes runtime hook that calls `factoryctl.py` automatically when cards move
  toward `ready` or `done`.
