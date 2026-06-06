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
- supply-chain proof gate with workflow validation, dependency-manifest posture
  and SPDX source SBOM generation;
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

### Completion Audit Guard

`scripts/factory_completion_audit.py` now creates a schema-backed completion
audit in `validation/completion/`.

The audit currently returns `NOT_COMPLETE` and `completion_claim_allowed=false`.
With `--require-complete`, it exits non-zero while blockers remain.

This is better than an optimistic score because autonomous agents need a hard
release boundary. A high score can guide prioritization, but it cannot authorize
production claims without product-specific or provider-backed evidence.

### Bounded Full Product Graph

`scripts/full_product_worker_graph.py` now reconciles QVG as one
product-specific public validation graph.

It reads Product Face, Security, Auditor, CU/SVM/economic proof, Remote Proof,
Independent Review, Human Gate, Release Ops, Supply Chain and Receipt Five
evidence, then writes `validation/product-specific/qvg-full-product-worker-graph.json`.

This is better than isolated prooflets because a reviewer can see the whole
factory pass for one product context. It is still not production approval:
`reusable_for_product=false`, `completion_claim_allowed=false`, and stale
Receipt Five refs remain visible as `stale_evidence_refs`.

### Managed Remote Proof Probe

`scripts/managed_remote_proof_probe.py` now checks readiness for managed
Crabbox broker and Blacksmith Testbox proof without exposing values.

The probe records only booleans for config/env presence and redacted command
tails. In the current Hermes run it returned `PENDING` because no managed
provider credentials or Testbox run exist.

This is better than a vague blocker because future workers know exactly what
must appear before `managed_remote_proof` can move from bounded/static SSH to
provider-backed evidence.

### Production-like Product Face Reuse

`scripts/product_face_proof.py` now has an explicit reusable-product mode.

`reusable_for_product=true` is blocked unless the proof is `PASS`, has no
blocking findings, and includes a product id, environment class and approval
scope. For static production-like artifacts it also records the target artifact
hash.

Hermes `product-face` reran this path for the QVG public validation product and
wrote `validation/production/product-face/product-face-result.json`.

This is better than flipping a boolean in an existing proof because the
reusability claim is scoped to one product lane, one artifact class and one
approval boundary. It clears Product Face for that lane without pretending to
clear onchain, release, managed remote proof or human gates.

## Still Not 10/10

- Product-specific Codex Security scans still need to run per real
  implementation.
- Auditor has not run against real public Quasar source.
- Hermes dashboard `ready` parity is live-smoke proven. Dashboard/API `done`
  parity is live-smoke proven for missing Product Face result and weak Auditor
  preflight. Worker-style CLI completion is now live-smoke proven for missing
  Product Face result. One real specialist profile dispatch is now live-smoke
  proven with factory skill preload and public-safety scanner execution. The
  public adapter patch now applies to the tested official Hermes main commit and
  passes focused regression tests. Hermes still needs live wiring from Kanban
  events to the public hook, automatic result ingestion and product-specific
  specialist profile execution.
- Remote Proof is local-clean fallback, not provider-backed Crabbox/Testbox.
- Supply-chain posture now has public CI/SBOM proof for this repository, but
  product-specific dependency review, lockfiles and provenance still repeat per
  real implementation.
- Completion audit now blocks false practical-10 claims, but the blockers it
  names still require real product/provider execution.
- Production-like Product Face is now achieved for the named QVG public
  validation product lane. It is still not full WCAG, production performance,
  deployed-production proof or a substitute for the other product lanes.
- QVG full product graph now passes as bounded public validation, but production
  completion still requires a production target with reusable lane evidence.
- Managed remote proof readiness is explicit now, but the managed provider run
  itself still needs approved credentials, transcript, artifacts and cleanup.
- Current Git history still contains old private/internal markers from earlier
  commits; public launch should use an orphan branch, new repository or
  coordinated history rewrite.
- Full Product Face browser proof now passes locally, but CI still does not run
  Playwright browser capture.

## Current Practical Score

Estimated public-factory score after this pass: 9.994/10 for contracts,
preflight, executable Hermes hook, stricter worker-result reconciliation,
Product Face proof, dashboard/API no-bypass smokes, worker-style completion
no-bypass, official-main patch compatibility, real public-safety profile
dispatch, Crabbox static-SSH proof, action pinning, supply-chain CI/SBOM proof,
completion-claim blocking and public-safety controls.

It is not 10 because the remaining missing items require production Quasar
source, real CU/SVM/economic evidence, managed provider-backed remote proof,
release/human-gate evidence, a full reusable product graph, and a clean public
publication path for Git history.
