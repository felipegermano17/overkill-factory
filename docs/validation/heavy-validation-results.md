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
| Solana/Quasar R3 | ready_for_worker_execution | 12 | 0 | Correctly routes Auditor, Codex Security, crypto/key, supply chain, remote proof and human gate. Quasar source toolchain proof now exists; product-specific Auditor execution remains open. |

## Live Hermes Kanban Smoke

Public evidence:

- `validation/hermes-live/live-smoke-summary.md`
- `validation/hermes-live/materialize-solana-r3.json`
- `validation/hermes-live/enforce-done-missing-results.json`
- `validation/hermes-live/enforce-done-pass.json`
- `validation/hermes-live/worker-result-index.json`
- `validation/hermes-live/dashboard-ready-gate-smoke.md`
- `validation/hermes-live/dashboard-done-gate-smoke.md`
- `validation/hermes-live/worker-dispatched-done-gate-smoke.md`
- `validation/hermes-live/real-profile-dispatch-smoke.md`
- `validation/hermes-live/official-main-patch-smoke.md`
- `validation/hermes-live/official-head-recheck-2026-06-06.md`
- `validation/hermes-live/multi-profile-dispatch-summary.md`
- `validation/hermes-live/multi-profile-dispatch-fixed/product-face/qvg-product-face-result.json`
- `validation/hermes-live/multi-profile-dispatch-fixed/security/security_scan_result.json`
- `validation/hermes-live/multi-profile-dispatch-fixed/auditor/auditor_result.json`
- `validation/hermes-live/multi-profile-dispatch-fixed/remote-proof/remote-proof-result.json`
- `validation/hermes-live/multi-profile-dispatch-browser/product-face/qvg-product-face-result.json`
- `validation/hermes-live/multi-profile-dispatch-browser/remote-proof/remote-proof-result.json`
- `validation/remote-proof/crabbox-static-ssh-proof-2026-06-06.json`
- `validation/remote-proof/crabbox-static-ssh-proof-2026-06-06.md`
- `validation/quasar-product-like-proof/qvg-quasar-runtime-proof.json`
- `validation/quasar-product-like-proof/qvg-quasar-cu-fuzz-property-proof.json`
- `validation/quasar-product-like-proof/qvg-product-like-auditor-result.json`
- `validation/quasar-product-like-proof/qvg-product-like-auditor-report.md`
- `validation/quasar-product-like-proof/hermes-qvg-code-audit-summary.md`
- `validation/quasar-product-like-proof/hermes-cu-fuzz-property-summary.md`
- `validation/quasar-product-like-proof/product-face/qvg-product-like-product-face-result.json`
- `validation/quasar-product-like-proof/product-face/hermes-product-face-summary.md`
- `validation/quasar-product-like-proof/product-face/screenshots/desktop.png`
- `validation/quasar-product-like-proof/product-face/screenshots/mobile.png`
- `validation/release-human-gate/qvg-human-gate-record.json`
- `validation/release-human-gate/qvg-human-gate-record.md`
- `validation/release-human-gate/qvg-release-ops-result.json`
- `validation/release-human-gate/qvg-release-ops-result.md`
- `validation/release-human-gate/hermes-release-human-summary.md`
- `validation/supply-chain/supply-chain-proof.json`
- `validation/supply-chain/source-sbom.spdx.json`
- `validation/supply-chain/supply-chain-proof.md`
- `validation/supply-chain/hermes-supply-chain-summary.md`
- `validation/completion/factory-10-completion-audit.json`
- `validation/completion/factory-10-completion-audit.md`
- `validation/completion/hermes-completion-audit-summary.md`

Observed result:

- Hermes board alias: `public-live-smoke-board` (real operational ID redacted);
- Hermes main task alias: `public-main-task` (real operational ID redacted);
- required worker tasks created: 12;
- worker tasks completed: 12;
- negative done enforcement: blocked without worker results;
- positive done enforcement: allowed with 12 valid worker result records;
- dashboard direct ready enforcement: invalid product-facing card received
  HTTP 409 and remained blocked;
- dashboard/API done enforcement: product-facing completion without
  `product_face_result` received HTTP 409 and remained `ready`;
- dashboard/API Auditor enforcement: onchain/Solana/Quasar completion with
  preflight-only Auditor PASS received HTTP 409 and remained `ready`;
- worker-style CLI completion enforcement: product-facing completion without
  `product_face_result` returned non-zero, kept the task `running`, preserved
  the active run and emitted a completion-blocked event;
- real specialist dispatch: `public-safety-gate` was spawned by Hermes,
  preloaded the `overkill-factory` skill, ran `public_safety_scan.py`, wrote
  worker evidence and closed with Receipt Five metadata;
- real multi-profile dispatch: Product Face, Codex Security,
  Solana/Quasar Auditor and Remote Proof profiles were spawned by Hermes on a
  disposable public clone and closed with evidence records;
- first multi-profile run found a real Product Face fallback contract bug, then
  the clean rerun proved the fixed schema/waiver path with public JSON
  validation passing;
- Product Face browser rerun: after adding the system-Chrome launch fallback,
  the `product-face` profile captured desktop and mobile screenshots, console,
  DOM state, a11y basics, overlap checks and performance notes with result
  `PASS`;
- Remote Proof after browser-backed Product Face: the `remote-proof-runner`
  profile produced a passing local clean-tempdir receipt and public JSON
  validation still passed;
- Crabbox static-SSH remote proof: Crabbox `v0.26.0` was installed with release
  checksum verification, then ran a real static SSH proof against a clean public
  clone, synced `488` files through `ssh+rsync`, executed public JSON, secret
  and public-safety scans remotely, and returned exit code `0`;
- Security profile dispatch: `codex-security` ran secret safety, public safety,
  unit tests and factory battery with result `PASS`;
- Auditor profile dispatch: `solana-quasar-auditor` loaded the Auditor corpus
  path and emitted a bounded `WAIVED` preflight because real product Quasar
  source is still absent;
- product-like Quasar/Auditor dispatch: a later real Hermes
  `solana-quasar-auditor` worker ran against a clean public clone, built/tested
  the QVG product-like Quasar target in Docker, generated a bounded
  `auditor_result audit_mode=code_audit`, validated it with `factoryctl`, and
  closed with `PASS`;
- product-like CU/fuzz/property dispatch: a real Hermes
  `solana-quasar-auditor` worker reran the Docker-backed Quasar proof after
  adding deterministic property tests, verified the runtime proof source hash
  matched the current source, produced `513` deterministic property/fuzz cases,
  attached a static/symbolic compute profile and kept
  `real_solana_cu_measured=false` so production CU remains a separate gate;
- updated product-like Product Face dispatch: after the Quasar/Auditor evidence
  changed the prototype copy, a real Hermes `product-face` worker reran desktop
  and mobile browser capture on commit `bb03115b77a65caecb557a7e00473cc5742c2ec7`,
  produced screenshots/console/state/report artifacts, passed DOM-level a11y and
  overlap checks, and reran public JSON, public-safety and secret scans with
  `OK`;
- release/human dry-run gate dispatch: a real disposable Hermes board spawned
  `human-gate-clerk`, then promoted and spawned dependent `release-ops-worker`;
  both completed with public-safe worker result artifacts, `PASS` for dry-run
  evidence only, `reusable_for_product=false`, explicit production block status
  and public JSON, public-safety and secret scans returning `OK`;
- supply-chain gate dispatch: a real Hermes `supply-chain-gate` worker ran
  against a clean public clone with the current diff applied, generated a
  structured `supply_chain_result`, produced an SPDX 2.3 source SBOM, confirmed
  GitHub Actions are commit-pinned with `contents: read`, and reran public JSON,
  public-safety, secret-safety, unit tests and `git diff --check` with `PASS`;
- completion audit dispatch: a real Hermes `independent-reviewer` worker ran
  the schema-backed completion audit against a clean public clone with the
  current diff applied, confirmed status `NOT_COMPLETE`, confirmed
  `completion_claim_allowed=false`, confirmed the six remaining blockers, and
  verified that `--require-complete` exits non-zero while public JSON,
  public-safety, secret-safety, unit tests and `git diff --check` pass;
- official-main patch smoke: the public adapter patch applied to official Hermes
  commit `56236b16e383cc656bb8c88429902f4de83f1faf` and focused regression
  tests passed (`119 passed, 1 warning`);
- official HEAD recheck: live `git ls-remote` still points to the same tested
  commit, so no new disposable compatibility smoke was required in this pass;
- main card final state: `done`.

This proves real Kanban materialization, dependency wiring, worker-result
reconciliation and multiple specialist-profile execution paths. It also proves
that Product Face can now run as real browser-backed evidence in Hermes. It does
not prove real product Quasar Auditor, release, provider-backed remote proof or
human approval execution.

## Real Codex Security Scan

Public evidence:

- `validation/security/codex-security-full-scan-2026-06-06.md`
- `validation/security/codex-security-full-scan-2026-06-06.html`
- `validation/security/bandit-scripts-adapters.json`

Observed result:

- threat model: generated for the public factory repository;
- discovery: parent review plus three parallel specialist reviews;
- fixed during scan: 9 security/readiness issues;
- remaining reportable findings after fixes: 0;
- Bandit scope: `scripts` and `adapters`;
- Bandit findings after fixes: 0.

This proves that Codex Security has now been used as a real factory worker for
the factory/gate code. It does not prove product-specific security for a future
real implementation, deploy path, signing path or Quasar source.

## Real Product Face Proof

Public evidence:

- `validation/product-face/qvg-product-face-result.json`
- `validation/product-face/product-face-report.md`
- `validation/product-face/state.json`
- `validation/product-face/console.json`
- `validation/product-face/screenshots/desktop.png`
- `validation/product-face/screenshots/mobile.png`
- `validation/quasar-product-like-proof/product-face/qvg-product-like-product-face-result.json`
- `validation/quasar-product-like-proof/product-face/product-face-report.md`
- `validation/quasar-product-like-proof/product-face/state.json`
- `validation/quasar-product-like-proof/product-face/console.json`
- `validation/quasar-product-like-proof/product-face/screenshots/desktop.png`
- `validation/quasar-product-like-proof/product-face/screenshots/mobile.png`

Observed result:

- target: `pilots/quasar-vault-guard-test/product-face/prototype.html`;
- result: `PASS`;
- screenshots: desktop and mobile;
- console: no browser console/page errors;
- a11y basis: DOM-level accessible-name, title, language, image-alt and landmark checks;
- overlap basis: DOM rectangle intersection scan;
- evidence kind: real static prototype proof;
- reusable for production product approval: `false`.
- latest rerun basis: real Hermes `product-face` worker after product-like
  Quasar/Auditor copy changes, commit
  `bb03115b77a65caecb557a7e00473cc5742c2ec7`;
- latest rerun validations: public JSON artifacts, public safety scan and
  secret safety scan all returned `OK`.

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
- Whimsical MCP fallback is now scripted through `scripts/whimsical_mcp.py`.
  The factory can inspect/read/edit the board through the local MCP endpoint
  even when native MCP tools are not exposed in a future Codex session.
- Whimsical Desktop MCP was exercised live through JSON-RPC, with health,
  board read, flowchart edit and snapshot capture passing. The editable board
  now includes F39 Quasar/Auditor product-like PASS, F40 updated Product Face
  PASS, F41 Crabbox static-SSH PASS and F42 release/human dry-run PASS, and the
  public map snapshot was refreshed after that update.
- Auditor result handling is stricter: `code_audit` now requires corpus count,
  checklists 01-07, known-vector coverage, instruction matrix and state model.
  The worker-result validator now blocks shallow real Auditor PASS records.
- The Solana/Quasar source-resolution note is recorded in
  `docs/validation/auditor-quasar-source-resolution-2026-06-06.md`.
- Quasar runtime proof is now container-backed. The crates.io CLI path failed
  build, while the source-pinned `blueshift-gg/quasar` path passed init, build
  and test. `auditor_result audit_mode=code_audit` now requires a
  `quasar_toolchain_proof` before it can be considered valid.
- Hermes dashboard ready bypass is now covered by a public adapter patch and a
  live smoke: direct `ready` move returns 409 and blocks the invalid card with a
  preserved gate reason.
- Hermes dashboard/API `done` bypass is now covered by a public adapter patch
  and live smokes: missing Product Face result and weak Auditor preflight both
  return 409 and preserve the card before closure.
- Hermes worker-style CLI completion now returns non-zero with the gate reason
  and keeps the active run open until the missing worker result exists.
- Hermes real profile dispatch is now smoke-proven with `public-safety-gate`:
  the worker preloaded the factory skill, ran a real public-safety scanner,
  wrote evidence and completed with Receipt Five.
- Hermes multi-profile dispatch is now smoke-proven with `product-face`,
  `codex-security`, `solana-quasar-auditor` and `remote-proof-runner`. Product
  Face first exposed a fallback validation bug, then passed with browser-backed
  screenshots after the Chrome-channel fallback was added.
- QVG product-like Quasar source now exists and was built/tested by a real
  Hermes `solana-quasar-auditor` worker in a clean Docker container. The same
  worker cloned `solanabr/Auditor`, generated a bounded code-audit result and
  passed deep `factoryctl.validate_auditor_result` validation.
- QVG product-like CU/fuzz/property proof now exists and was run by a real
  Hermes `solana-quasar-auditor` worker. It adds deterministic Rust property
  tests, source-hash reconciliation with the runtime proof, `513` cases,
  public JSON validation and an explicit static/symbolic CU boundary.
- QVG Product Face evidence was rerun after the product-like Quasar/Auditor
  update by a real Hermes `product-face` worker, with fresh desktop/mobile
  screenshots, console/state/report artifacts and repository safety scans.
- Hermes update compatibility now has a disposable official-main smoke: the
  public patch is parseable, applies to the tested official Hermes main commit,
  and passes focused Kanban/dashboard regression tests.
- Hermes release/human gate dry-run is now profile-proven: `human-gate-clerk`
  recorded only a bounded dry-run decision, `release-ops-worker` prepared the
  release-control packet, and both artifacts keep production blocked until a
  fresh product-specific R4 gate, rollback proof, smoke and monitoring evidence
  exist.
- Supply-chain CI/SBOM proof now exists and was run by a real Hermes
  `supply-chain-gate` worker. CI now includes `scripts/supply_chain_proof.py
  --check --no-write`; the proof validates least-privilege workflow permissions,
  full-SHA-pinned external actions, dependency-manifest posture and SPDX source
  inventory, then reruns public JSON, public-safety, secret-safety, tests and
  diff-check.
- Factory completion audit now exists as a schema-backed release boundary.
  A real Hermes `independent-reviewer` worker confirmed it blocks practical
  `10/10` completion claims until production Product Face, production Quasar
  Auditor, production CU/SVM/economic proof, managed remote proof, production
  release human gate evidence and a full product-specific worker graph exist.

### Still Not Proven

- Production Product Face execution on a deployed or production-like UI. The
  current Hermes profile proof is browser backed but still limited to the static
  Quasar Vault Guard prototype.
- Real Auditor execution against production Quasar source. Public product-like
  source now has a bounded code-audit PASS, but production source still needs a
  separate run.
- Product-specific Solana/Quasar compute profiling, SVM/client flows and
  fuzz/property tests. Product-like CU/fuzz/property smoke now passes with
  source-hash reconciliation and `513` deterministic cases, but production real
  CU measurement, SVM/client transaction flow and economic safety remain open.
- Managed Crabbox broker or Blacksmith Testbox proof. Crabbox static-SSH remote
  proof now passes, but managed broker/Testbox credentials were not available
  and must not be simulated.
- Product-specific dependency audits, lockfiles and provenance still repeat per
  real product. The public factory repo has CI/SBOM proof now, but future
  product/runtime dependencies must add their own audit evidence.
- Future Hermes releases still need the same disposable compatibility smoke
  rerun before an update is accepted.
- Full multi-specialist Hermes execution on product work. Product Face,
  Security, Auditor preflight, Remote Proof, Release Ops and Human Gate profile
  dispatch are proven on public/dry-run pilots, but still need product-specific
  execution against real release targets before production use.
- The completion audit correctly blocks a practical `10/10` claim. This is a
  release-safety improvement, not a substitute for clearing the blockers it
  reports.

## Adversarial Review Scores

| Review Area | Score Before Fixes | Main Reason |
|---|---:|---|
| Security | 9.5 | Real Codex Security scan, Bandit, public scanners and fixed findings now exist; product-specific scans still repeat per implementation. |
| Product Face | 9.8 | Hermes profile now captures browser-backed desktop/mobile screenshots and validation evidence, including the updated product-like audit state; production UI proof and full WCAG remain open. |
| Agent/Hermes Operability | 9.997 | Real Hermes board, worker graph, stronger evidence reconciliation, dashboard ready no-bypass, dashboard/API done no-bypass, worker-style CLI completion no-bypass, official-main patch apply, multi-profile dispatch, Crabbox static-SSH remote proof, release/human dry-run, supply-chain gate dispatch and completion-claim blocking are now smoke-proven. |
| Solana/Quasar/Auditor | 9.72 | Product-like Quasar source now builds/tests in Docker, has bounded Auditor code-audit PASS and product-like CU/fuzz/property smoke from real Hermes workers; production source, real CU/SVM flow and economic fuzz/property tests remain open. |

Estimated score after fixes in this pass: 9.992/10 for factory process,
operability, completion-claim discipline and public repository safety.

It is not 10 yet because the next jump requires product-specific or
provider-backed execution, not more public-pilot smoke: production Quasar
source with CU/fuzz/property depth, managed Testbox/broker remote proof, a
production-like Product Face target, production release execution and
production-scoped human gate evidence.

## Next Validation Gates

1. Run Product Face proof against the next production-like UI, not only the
   static prototype.
2. Replace public product-like Quasar proof with production Quasar source when
   the production product exists, then add CU profiling and fuzz/property tests.
3. Rerun supply-chain CI/SBOM proof after every workflow/dependency change; add
   dependency audit, lockfile and provenance evidence as soon as runtime
   dependencies exist.
4. Run managed Crabbox broker or Blacksmith Testbox remote proof with approved
   credentials; static SSH fallback is already proven.
5. Rerun Hermes update compatibility on every future Hermes release.
6. Run release and human-gate worker profiles on product-specific production
   targets with real rollback, smoke, monitoring and approval evidence.
7. Only allow `factory_completion_audit.py --require-complete` to pass after
   the six product-specific/provider-backed blockers have direct evidence.
