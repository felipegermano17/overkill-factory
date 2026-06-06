# Overkill Factory V3.6

V3.6 is the first version informed by a completed Hermes dry pilot.

Pilot evidence:

```text
pilot: pilots/quasar-vault-guard-test
Hermes board: overkill-factory-pilot-10
Hermes task: t_a09d1c2e
status: done
Whimsical primary board: XVvfzk
```

This version does not claim production readiness. It upgrades the factory
contracts so agents can survive real Kanban gates, evidence review and
dry-pilot ambiguity.

## New Spine

```text
paper
-> source ledger
-> Product SOT
-> questions
-> architecture
-> Product Face
-> specialist reviews
-> human architecture gate
-> Documentation OS
-> decomposition
-> worker packets
-> Hermes ready gate
-> agent execution
-> worker results
-> closure summary
-> Receipt Five
-> Hermes done gate
-> promotion or block
-> monitoring
-> learning loop
```

## Contract Changes

### 1. Compound Hermes Completion Contract

Receipt Five now supports both Factory 10/Hermes V3.5 and the older Hermes V2
completion gate.

Required when `hermes_kaxis_v2_completion_required=true`:

- evidence paths;
- `verification.passed=true` with commands;
- `sandbox.passed=true` with invariants;
- `rollback.verified=true` with evidence;
- approvals for QA, independent review, security, cybersecurity, CTO and
  Felipe gate.

Why better than a plain Receipt Five: Hermes can reject weak closure even when a
worker writes confident prose.

### 2. Security Result Shape Is First-Class

`security_scan_result` must include:

- `scanner_agent`;
- `tool`;
- `scope`;
- `result`;
- `findings_summary`;
- `evidence_refs`.

Why better than a generic worker result: security is not a normal comment. The
gate needs to know who scanned, what tool ran, what scope was covered and where
the evidence lives.

### 3. Closure Summary Between Results And Receipt

The factory now requires a closure summary for non-trivial cards.

It answers:

- which workers were required by preflight;
- which worker results exist;
- which results are only preflight or bounded;
- which authority is still forbidden.

Why better than relying on the gate report: preflight says what must run. It
does not prove that the worker ran.

### 4. Portable Pilot Package

Pilot packages should include enough tooling to be checked in isolation.

For the dry pilot, this means:

```text
tools/factoryctl.py
README portable commands
Receipt Five portable commands
```

Why better than assuming repo context: Hermes reviewers and future agents can
verify the package from context-lock without guessing where the repo lives.

### 5. Approval Scope Must Be Repeated

Dry-pilot approvals must explicitly say they do not approve:

- production;
- deploy;
- devnet;
- mainnet;
- signing;
- keys;
- funds;
- custody;
- real Quasar program safety.

Why better than a generic approval: agents tend to expand authority unless the
forbidden surface is repeated at the gate, receipt and worker-summary levels.

## Current Score

V3.6 scores 10/10 for a dry-pilot factory proof:

- the paper was synthetic but messy;
- Product Face was included;
- security and Auditor were required;
- Hermes blocked weak contracts;
- local validators were hardened after each block;
- Hermes profile reviewers passed the dry pilot with boundaries;
- the card closed as `done` with Receipt Five.

It is not 10/10 for production readiness. That requires the first real product
paper and real implementation slices.

## Next Hardening

- Add automatic Hermes hooks that run `factoryctl.py` on create/ready/done.
- Auto-create worker subtasks from `requires_execution`.
- Run real Codex Security scans on implementation code.
- Run `solanabr/Auditor` against real Quasar source.
- Add Product Face browser validation as a normal worker, not a manual pilot
  step.
