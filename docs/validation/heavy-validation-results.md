# Heavy Validation Results

Date: 2026-06-06

This validation battery now combines a real Hermes Kanban smoke with a
multi-context preflight and worker-routing battery. It does not claim production
readiness, real deployment safety, real onchain program safety, or real
specialist execution for production work.

## Public Scenarios

| Scenario | Gate Status | Required Workers | Blocked Workers | Read |
|---|---:|---:|---:|---|
| Agentic Browser Memory R3 | ready_for_worker_execution | 13 | 0 | Correctly routes Codex Security, agentic AI security, AppSec, memory, remote proof, handoff and human gate. |
| Cloud Release R4 | ready_for_worker_execution | 15 | 0 | Correctly routes cloud/infra, crypto/key management, release ops, monitoring, public safety, remote proof and human gate. |
| Product Face SaaS R2 | ready_for_worker_execution | 8 | 0 | Correctly routes Product Face, QA, independent review, AppSec/OWASP and security orchestration after the card includes a security scan packet. |
| Public Repo Release R2 | blocked | 15 | 7 | Correctly blocks because security, release, human gate, supply chain and monitoring evidence are not attached. |
| Solana/Quasar R3 | ready_for_worker_execution | 12 | 0 | Correctly routes Auditor, Codex Security, crypto/key, supply chain, remote proof and human gate. This remains preflight until real Quasar source exists. |

## Live Hermes Kanban Smoke

Public evidence:

- `validation/hermes-live/live-smoke-summary.md`
- `validation/hermes-live/materialize-solana-r3.json`
- `validation/hermes-live/enforce-done-missing-results.json`
- `validation/hermes-live/enforce-done-pass.json`
- `validation/hermes-live/worker-result-index.json`

Observed result:

- Hermes board alias: `public-live-smoke-board` (real operational ID redacted);
- Hermes main task alias: `public-main-task` (real operational ID redacted);
- required worker tasks created: 12;
- worker tasks completed: 12;
- negative done enforcement: blocked without worker results;
- positive done enforcement: allowed with 12 valid worker result records;
- main card final state: `done`.

This proves real Kanban materialization, dependency wiring and worker-result
reconciliation. It does not prove real Codex Security, Quasar Auditor, release,
Product Face or human approval execution.

## Real Product Face Proof

Public evidence:

- `validation/product-face/qvg-product-face-result.json`
- `validation/product-face/product-face-report.md`
- `validation/product-face/state.json`
- `validation/product-face/console.json`
- `validation/product-face/screenshots/desktop.png`
- `validation/product-face/screenshots/mobile.png`

Observed result:

- target: `pilots/quasar-vault-guard-test/product-face/prototype.html`;
- result: `PASS`;
- screenshots: desktop and mobile;
- console: no browser console/page errors;
- a11y basis: DOM-level accessible-name, title, language, image-alt and landmark checks;
- overlap basis: DOM rectangle intersection scan;
- evidence kind: real static prototype proof;
- reusable for production product approval: `false`.

This proves that Product Face is no longer just a contract in the factory: the
runner can produce browser-backed evidence. It still does not prove production
UI quality, full WCAG compliance or runtime performance.

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
- Worker result reconciliation now binds evidence to the expected worker ID,
  card ID and slice ID, so a result from another worker/card cannot satisfy a
  blocking gate.
- Worker and human-gate records now declare `evidence_kind` and
  `reusable_for_product`; synthetic smoke evidence is explicitly non-reusable
  for real product approval.
- The Hermes transition hook is fail-closed by default for every blocking
  action, including `block_and_create_before_ready_tasks`; `--report-only` is
  only for observation/CI capture.
- Public Hermes smoke artifacts now use redacted aliases for board/task IDs.
  Real operational IDs stay out of the public repository.

### Still Not Proven

- Full Codex Security scan with threat model, discovery, validation,
  attack-path analysis and final report.
- Production Product Face execution on a real UI. The current proof is browser
  backed but limited to the static Quasar Vault Guard prototype.
- Real Auditor execution against real Quasar source.
- Real Solana/Quasar build, tests, compute profiling and fuzz/property tests.
- Real remote proof in Crabbox/Testbox or a clean container with artifact,
  cleanup and cost receipt.
- Disposable Hermes update smoke against a real checkout with dashboard/API
  bypass checks.
- Full automatic Hermes dispatcher execution with real specialist profiles.
  The live adapter materializes and reconciles the task graph, but the public
  smoke completed synthetic worker tasks manually.
- Shared CLI/dashboard/API enforcement. The adapter proves the contract; Hermes
  still needs the hook wired into every transition surface so no bypass exists.

## Adversarial Review Scores

| Review Area | Score Before Fixes | Main Reason |
|---|---:|---|
| Security | 8.8 | Stronger OWASP/AppSec routing and public scans; still needs real Codex Security reports. |
| Product Face | 9.3 | Browser-backed proof exists for the static prototype; production UI proof and full a11y remain open. |
| Agent/Hermes Operability | 9.2 | Real Hermes board, worker graph and done enforcement proven; dispatcher hooks still need hard integration. |
| Solana/Quasar/Auditor | 8.6 | Strong routing and live smoke; still no real Quasar code audit. |

Estimated score after fixes in this pass: 9.5/10 for factory process,
operability and public repository safety.

It is not 10 yet because the next jump requires real specialist executions,
not more synthetic smoke: real Codex Security, real Auditor/Quasar, real remote
proof, and Hermes transition hooks wired into every bypassable surface.

## Next Validation Gates

1. Run a full Codex Security scan and persist markdown/HTML reports.
2. Run Product Face proof against the next production-like UI, not only the
   static prototype.
3. Build or import a small Quasar program and run the real Auditor path.
4. Add supply-chain CI: workflow permissions, secret scan, dependency audit,
   SBOM/provenance or explicit waiver.
5. Run remote proof in a clean disposable environment.
6. Test Hermes update compatibility against a disposable Hermes checkout.
7. Wire the live adapter into Hermes CLI/dashboard/API transition paths.
8. Run the same live smoke with real dispatched specialist profiles instead of
   synthetic worker completions.
