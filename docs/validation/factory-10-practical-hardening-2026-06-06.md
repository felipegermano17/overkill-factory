# Factory 10 Practical Hardening - 2026-06-06

This pass moved the public factory from strong preflight toward practical
operation. It still does not claim complete autonomous production execution.

## What Improved

### Hermes Transition Plan

`scripts/factoryctl.py transition-plan` now produces an operational decision for
Hermes Kanban transitions.

- `ready` can produce `allow_and_create_worker_tasks`.
- `done` reconciles required worker results and Receipt Five.
- missing required worker results block `done`.
- workers are routed into `blocking-before-ready`,
  `blocking-before-done` or `advisory-review`.

This is better than a gate report alone because Hermes gets a concrete task
graph and closure contract, not just diagnostics.

### Hermes Transition Hook

`adapters/hermes/transition_hook.py` now turns that plan into an executable
runtime hook.

- `ready` writes an idempotent worker ledger.
- repeated `ready` attempts reuse existing worker tasks.
- `done` reconciles worker results and Receipt Five.
- `--enforce` returns a non-zero exit code for blocked transitions.
- CI runs the hook and proves blocked `done` cannot be silently accepted.

This is better than keeping the plan as documentation because Hermes can call
one command and receive a machine-readable action plus durable worker state.

### Public Safety

`source_card_ref` now redacts angle-bracket path-like refs instead of preserving
them raw.

This closes the strongest leak found in the public security review.

### Product Face

`scripts/product_face_proof.py` now exists.

The QVG public pilot now has `PASS` Product Face evidence with desktop and
mobile screenshots, DOM state, console output, accessibility basics, overlap
scan and performance note.

When browser proof is unavailable, the runner writes `WAIVED` with
`blocking_findings=true`. That fallback is better than fake PASS because the
card stays blocked until real screenshots, mobile proof, accessibility and
overlap checks exist.

### Security

Public CI now has:

- least-privilege workflow permissions;
- GitHub Actions pinned by commit SHA;
- unit tests;
- Hermes transition-plan smoke;
- Hermes transition-hook smoke with enforced block check;
- Hermes adapter compatibility check;
- public JSON artifact validation across examples, validation, pilots, agents
  and templates;
- lightweight secret scan;
- public-safety scan.

This CI layer is still not a full Codex Security scan by itself. A separate
full Codex Security scan was later run and recorded under
`validation/security/`.

Worker result reconciliation is now stricter:

- weak JSON shape does not satisfy a required worker;
- `FAIL`, `PENDING`, blocking findings or empty evidence refs block `done`;
- human gates require approved decision records with evidence;
- Security and Auditor results still have their specific completion checks.

This is better than accepting any JSON with a matching `record_type` because
autonomous agents cannot silently convert a request-shaped or partial result
into completion evidence.

### Remote Proof

`scripts/remote_proof_smoke.py` runs a clean local tempdir proof and writes a
`remote_proof_result` receipt.

This is not Crabbox/Testbox, but it is a real clean-environment fallback with
TTL, no-secrets policy, cleanup, command receipts and blocking result.

The runner no longer uses shell execution for configured commands. This reduces
the chance that a worker packet or card text can become command injection.

### Public Artifact Hygiene

This pass removed the silent public-safety exception for `LICENSE` and
`NOTICE.md`, neutralized personal ownership text, added schemas for worker
registry, Hermes worker ledger and closure summaries, and made public JSON
without `$schema` fail unless it is explicitly raw capture data.

This is better than relying on a green scanner that skips risky files, because
the scanner now represents the real public policy more closely.

## Still Not 10/10

- Product-specific Codex Security scans still need to run per real
  implementation.
- Auditor has not run against real public Quasar source.
- Hermes dashboard `ready` parity is live-smoke proven. Dashboard/API `done`
  parity is now live-smoke proven for missing Product Face result and weak
  Auditor preflight. Hermes still needs worker-dispatched completion proof,
  live wiring from Kanban events to the public hook and automatic result
  ingestion.
- Remote Proof is local-clean fallback, not provider-backed Crabbox/Testbox.
- Supply-chain posture still lacks dependency review and SBOM/provenance.
- Current Git history still contains old private/internal markers from earlier
  commits; public launch should use an orphan branch, new repository or
  coordinated history rewrite.
- Full Product Face browser proof now passes locally, but CI still does not run
  Playwright browser capture.

## Current Practical Score

Estimated public-factory score after this pass: 9.65/10 for contracts,
preflight, executable Hermes hook, stricter worker-result reconciliation,
Product Face proof, dashboard/API no-bypass smokes, local remote proof, action
pinning and public-safety controls.

It is not 10 because the missing items above require real runtime integration or
real target code, plus a clean public publication path for Git history.
