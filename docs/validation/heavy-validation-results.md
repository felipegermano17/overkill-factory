# Heavy Validation Results

Date: 2026-06-06

This validation battery tested the factory as a multi-context preflight and
worker-routing system. It does not claim production readiness, real deployment
safety, real onchain program safety, or full autonomous Hermes orchestration.

## Public Scenarios

| Scenario | Gate Status | Required Workers | Blocked Workers | Read |
|---|---:|---:|---:|---|
| Agentic Browser Memory R3 | ready_for_worker_execution | 13 | 0 | Correctly routes Codex Security, agentic AI security, AppSec, memory, remote proof, handoff and human gate. |
| Cloud Release R4 | ready_for_worker_execution | 15 | 0 | Correctly routes cloud/infra, crypto/key management, release ops, monitoring, public safety, remote proof and human gate. |
| Product Face SaaS R2 | blocked | 8 | 2 | Correctly blocks because AppSec/security inputs are missing. Product Face routing works, but visual proof is still not executed in this synthetic card. |
| Public Repo Release R2 | blocked | 15 | 7 | Correctly blocks because security, release, human gate, supply chain and monitoring evidence are not attached. |
| Solana/Quasar R3 | ready_for_worker_execution | 12 | 0 | Correctly routes Auditor, Codex Security, crypto/key, supply chain, remote proof and human gate. This remains preflight until real Quasar source exists. |

## Private Real Paper Smoke

A private real product-paper smoke was executed outside the public repository.
Only private artifacts contain the source path, hash and full routing result.

Outcome:

- card validation: OK;
- gate status: ready_for_worker_execution;
- required workers: 22;
- blocked workers: 0;
- public repository impact: none.

The private smoke proves the factory can route a real messy product paper into
planning, architecture, Product Face, onchain, security, review and human-gate
work. It does not prove that those workers executed real audits or production
checks.

## Findings From The Battery

### Fixed During This Pass

- Worker packets no longer write absolute local paths into `source_card_path`.
  Repo-local cards become relative paths; outside cards become `external:<name>`.
- Public safety scan now passes after regenerating worker packets.
- `worker-packet --required-only` generates only required worker packets.
- Gate reports now include `gate_status`, `required_workers` and
  `blocked_workers`.
- `codex-security` now triggers for code, CI, supply-chain, public and agentic
  surfaces, not only R3/R4/security surfaces.
- Remote proof cards now require `ttl`, `cost_owner`, `cleanup_plan`,
  `secret_policy` and `artifact_policy`.
- The public worker registry now covers all 27 workers and is tested against the
  CLI worker set.
- Product Face completion now requires a structured `product_face_result` with
  screenshots, viewports, checked states, journeys, accessibility, overlap,
  performance note and evidence refs.
- Auditor preflight can no longer be represented as a real code-audit PASS.
  Preflight must be marked as `WAIVED` or `PENDING` with explicit boundary.
- Hermes transition-plan fixtures now show the intended runtime contract:
  `ready` creates required worker subtasks by queue class, while `done`
  reconciles worker results and Receipt Five before allowing closure.

### Still Not Proven

- Full Codex Security scan with threat model, discovery, validation,
  attack-path analysis and final report.
- Real Product Face execution with Playwright/browser screenshots, console
  checks, accessibility checks and overlap checks on a real UI.
- Real Auditor execution against real Quasar source.
- Real Solana/Quasar build, tests, compute profiling and fuzz/property tests.
- Real remote proof in Crabbox/Testbox or a clean container with artifact,
  cleanup and cost receipt.
- Disposable Hermes update smoke against a real checkout with dashboard/API
  bypass checks.
- Full automatic Hermes worker orchestration. The current repo prepares
  contracts and packets; Hermes still needs runtime hooks for automatic task
  fan-out and reconciliation.
- Live Hermes transition-plan enforcement. The public fixtures demonstrate
  `allow_and_create_worker_tasks` and blocked done reconciliation, but Hermes
  still needs real event hooks, idempotent subtask persistence, worker-result
  ingestion and shared CLI/dashboard/API enforcement.

## Adversarial Review Scores

| Review Area | Score Before Fixes | Main Reason |
|---|---:|---|
| Security | 6.8 | Good coverage model, weak operational proof and public path leak. |
| Product Face | 7.4 | Good routing, insufficient visual proof contract. |
| Agent/Hermes Operability | 7.6 | Strong preflight, but not automatic Hermes orchestration yet. |
| Solana/Quasar/Auditor | 7.0 | Good Auditor routing, no real Quasar code audit. |

Estimated score after fixes in this pass: 8.6/10 for preflight quality and
public repository safety.

It is not 9.5+ yet because the next jump requires real executions, not more
preflight contracts.

## Next Validation Gates

1. Run a full Codex Security scan and persist markdown/HTML reports.
2. Build or select a small real UI and run Product Face proof with browser
   screenshots, mobile viewport, a11y, console and overlap evidence.
3. Build or import a small Quasar program and run the real Auditor path.
4. Add supply-chain CI: workflow permissions, secret scan, dependency audit,
   SBOM/provenance or explicit waiver.
5. Run remote proof in a clean disposable environment.
6. Test Hermes update compatibility against a disposable Hermes checkout.
7. Implement Hermes hooks for automatic required-worker fan-out and completion
   reconciliation.
8. Add a disposable Hermes smoke that moves one public-safe card toward `ready`,
   verifies generated worker subtasks, attaches bounded worker results, then
   proves `done` blocks until Receipt Five is complete.
