# Changelog

All notable public changes should be recorded here.

The format follows Keep a Changelog principles and uses semantic versioning for
public releases.

## Unreleased

## 1.5.14 - 2026-06-25

- Fix Hermes no-idle handling after a failed review has already been repaired
  ([#436](https://github.com/felipegermano17/overkill-factory/issues/436)):
  superseded blocked review tasks no longer keep the board artificially idle.
- Detect repaired independent-review PASS states that require owner/Product SOT
  approval or rebaseline, and create a targeted `human-gate-clerk` task to
  prepare and deliver the Product SOT decision package before asking the
  operator.
- Make watchdog messaging distinguish post-review Product SOT decision-package
  creation from generic remediation.

## 1.5.13 - 2026-06-25

- Fix Hermes no-idle remediation for failed independent-review blockers:
  internal `review-failed` states with `factoryctl` validator, artifact or
  handoff repair instructions now create a targeted factory-owned repair task
  instead of falling back to stale board reconciliation.
- Route targeted Product SOT review repairs to `product-sot-planner`, bind the
  task to the factory workflow, and allow only native Hermes dispatch to run it.
- Stop the no-idle watchdog from claiming remediation was created when the
  idempotent task is already terminal, and include structured bridge payloads
  for human-gate/input events.

## 1.5.12 - 2026-06-25

- Fix Hermes no-idle classification for pending operator understanding
  confirmation: owner-readable Product SOT understanding packets now become
  `input_required`, not generic factory-owned package remediation.
- Make the no-idle watchdog name the exact Telegram-facing action for this
  state: confirm or correct the understanding before Product SOT.
- Add regressions so `operator_understanding_confirmation` blockers do not
  create more remediation cards or dispatch workers.

## 1.5.11 - 2026-06-25

- Harden Hermes runtime reconciliation so template/example scaffold refs,
  placeholder refs and embedded vFinal template packets do not count as
  materialized runtime evidence.
- Keep public template validation useful while forcing `reconcile-board` and
  no-idle remediation to compute the live frontier from product-specific
  artifacts only.
- Add regressions for template-only boards, real-SOT-with-template-method
  boards and real-method-with-template-architecture boards so the factory
  cannot jump past F1/F6/F10 from inherited scaffold data.
- Add a worker-profile boundary that builders must not approve their own work,
  with public profile validation coverage.

## 1.5.10 - 2026-06-25

- Fix generic blocked Hermes task creation to use an unassigned-create,
  block-readback, assign-readback protocol, preventing native Kanban dispatch
  from racing ahead of a factory gate.
- Preserve native workflow binding during that safe blocked-create path.
- Add regression coverage for the `create_task(blocked=True)` path that failed
  during live runtime smoke validation.

## 1.5.9 - 2026-06-25

- Bind factory-created Hermes tasks to native Kanban workflow state when
  available: `workflow_template_id=overkill-vfinal` plus the deterministic
  `current_step_key` computed by the phase engine.
- Harden no-idle classification so missing decision packages, PDF/readback,
  owner-readable material and repair tasks gated behind their own blocker route
  to factory-owned repair instead of operator approval bureaucracy.
- Route missing Solana AI Kit domain-brain state on Solana/onchain F4+ boards as
  a bounded factory planning repair, not a human approval question.
- Add regression coverage for SQLite workflow binding, factory-owned package
  repair, Kanban graph repair and Solana AI Kit route repair.
- Update Hermes/Telegram-first docs to make no-idle, factory-owned repair and
  native dispatch boundaries explicit.

## 1.5.8 - 2026-06-25

- Keep public JSON validation from treating local no-idle watchdog runtime state
  as a public artifact.
- Add regression coverage so local operational state does not break release
  validation after the factory has been used.

## 1.5.7 - 2026-06-25

- Add `factoryctl reconcile-board`, a deterministic Hermes/Kanban board
  reconciler that selects the active factory card from board state, computes the
  phase engine frontier and emits a single allowed next action.
- Wire Hermes no-idle remediation to the board reconciler so silent boards
  create deterministic next-artifact tasks instead of generic remediation cards.
- Block declared future phases from becoming human-gate requests when the
  computed frontier is still Product SOT or another earlier artifact.
- Add regressions for F9 architecture/gate claims that must reconcile back to
  F5 `operator_briefing_package`, plus no-canonical-card and ready-dispatch
  board states.

## 1.5.6 - 2026-06-25

- Block Solana/onchain `OVERKILL_VFINAL` F4+ routes unless a structured
  `solana-ai-kit-core` domain-brain record is present through universal signal
  intake, capability pack contract, direct domain brain provider state, or a
  valid Solana AI Kit usage receipt.
- Add transition-plan regression coverage so Hermes/adapter promotion cannot
  move Solana architecture, specialist planning, worker routing or execution
  from prose-only Solana/Quasar mentions.

## 1.5.5 - 2026-06-24

- Add the deterministic Factory Phase Engine state contract, schema and
  `factoryctl phase-engine` command so materialized artifacts, not agent prose or
  declared card phase, decide the current frontier.
- Expose `phase_engine` inside `factoryctl help-next` and block declared later
  phases such as F9 when owner-readable Product SOT material, Method Contract or
  other required artifacts are still missing.
- Harden Hermes bridge start and no-idle remediation payloads so the factory
  must materialize the next artifact computed by the phase engine before
  promotion, and cannot choose a frontier from memory, title, comments or prose.
- Add a public promise-to-implementation map, validator and CI coverage so
  README/docs/release claims must point to implementation, proof and explicit
  boundaries.
- Keep Portuguese README release state in sync and clarify that Solana AI
  Kit is the domain brain while Quasar/Auditor remain implementation or proof
  lanes.

## 1.5.4 - 2026-06-24

- Add `factory_phase_lock` so vFinal cards expose one active frontier,
  downstream freeze, owner-surface-first delivery and next required artifact.
- Block architecture, repo cleanup, human gates, worker packets and execution
  until owner-readable Product SOT material and Method Contract are present.
- Teach `factoryctl help-next` to report phase-lock blockers as factory-owned
  repair work instead of user approval requests.
- Harden Product SOT, Product Architect, Handoff Packer and Human Gate Clerk
  contracts so Hermes profiles cannot promote future-phase work before the
  active frontier is unlocked.

## 1.5.3 - 2026-06-24

- Harden human-gate/no-idle handling so an incomplete gate package or missing
  operator evidence is classified as `input_required`, not as an approval-ready
  human gate.
- Add the `human-gate-packet` contract and require pending human gates to carry
  a structured decision package: operator briefing ref, approval request,
  evidence index, owner review, markdown/PDF decision assets and optional
  explainer slots.

## 1.5.2 - 2026-06-24

- Fix Hermes no-idle classification so dependency-gated `todo` chains behind
  blocked ancestors do not create generic remediation loops.
- Add explicit `input_required`/`operator_input_required` no-idle handling so
  Telegram-first operators are asked for exact missing inputs instead of being
  told the factory has no human action.

## 1.5.1 - 2026-06-24

- Harden authority/autonomy enforcement so planning-only continuation, source
  resolution, Product SOT review, method routing and specialist routing cannot
  become human approval requests unless a real authority trigger is present.
- Remove `understanding` and `plan` from the `approval-request` approval types;
  understanding is confirmation, and planning is briefing/status unless access,
  budget, risk, scope change, release or production authority is required.
- Tighten `human-gate-clerk`, Control Tower and operator docs so Telegram,
  Discord or bridge surfaces distinguish proactive briefing from real human
  gates.
- Add regression tests for F9 planning-only cards, false planning gates,
  approval-request schema boundaries and Control Tower approval examples.

## 1.5.0 - 2026-06-24

- Added the canonical Factory Operating System registry and scorecard for the
  11 OS areas tracked in issues #400-#410.
- Added Method OS engine registry for spec-first SDD, TDD, BDD,
  discovery/research, security-first, design-first, legacy diagnosis and
  incident-first routing.
- Added public-safe Hermes runtime proof generation and scorecard integration.
- Hardened factory start so rich product material requires source inventory,
  brownfield handling, questions and briefing before Product SOT promotion.
- Updated README/docs/CLI reference and public manifest for the OS spine,
  Hermes runtime proof, Telegram-first operation and completion-audit
  boundaries.

## 1.4.0 - 2026-06-23

- Add Telegram-first operator interface, conversational start and deep briefing
  package contracts so new product work confirms understanding before Product
  SOT and pushes PDF/markdown decision packages instead of relying on shallow
  chat summaries or operator polling.
- Add `factoryctl operator-interface`, `factoryctl start-conversation`,
  `factoryctl briefing-package` and `factoryctl understanding-confirmation`
  validation/build commands for public-safe startup flows.
- Require Solana/onchain product signals to route deterministically through the
  `solana-ai-kit-core` domain brain before execution.
- Harden the public validator so confirmed factory starts require a real start
  request ref and confirmed product understanding requires a real operator
  response ref.

## 1.3.0 - 2026-06-23

- Add Fast Autonomy Lane contracts: `fast_autonomy` for reversible low-risk
  work and `yolo_sandbox` for disposable R0/R1 diagnostics, both blocked from
  production, mainnet, funds, signing, secrets, billing, destructive actions
  and human-gate approval.

## 1.2.1 - 2026-06-23

- Harden Hermes `enforce-done --complete-main` so local or scratch completion
  artifacts must be copied to durable attachment storage, read back with a
  matching SHA-256 hash and rewritten to durable logical refs before Hermes
  `complete`.
- Reject metadata-only `kanban-artifact:` and `kanban-attachment:` completion
  evidence unless the receipt carries explicit artifact readback proof.
- Add the Hermes `no-idle` controller, which classifies ready/running/todo/
  blocked state, creates only safe factory-owned remediation cards when the
  board would otherwise sit silently idle, and never dispatches workers itself.
- Add the public Hermes update guard and runbook coverage for safer Hermes
  updates and gateway restarts around active Kanban work.

## 1.2.0 - 2026-06-22

- Require a project-level design-system / `DESIGN.md` contract for
  product-facing frontend work, wire it into Product Face validation, worker
  packets, public templates, schemas and examples.

## 1.1.1 - 2026-06-19

- Document the v1.1.0 Codex Bridge plugin release surface in the public
  changelog and root READMEs.
- Clarify that the v1.0.1 visual map is a supporting visual surface versioned
  separately from the release tag and that Solana AI Kit routing is authoritative
  in capability packs, worker packets and validation.
- Mark intentional maintainer/audit pages as excluded from MkDocs navigation
  warnings.
- Keep local generated build output and runtime bridge inbox records out of
  public validation discovery.
- Pin the Solana AI Kit domain-brain provider to the resolved `v2.0.2` commit
  and record the unsigned upstream tag as a supply-chain gate input.
- Require `remote-proof-runner` for high-risk Solana/onchain cards even when a
  card omits an explicit `runtime_contract.remote_proof_required=true`.
- Extend the validation battery with Solana bank R4 routing scenarios covering
  wallet, signing, funds, mainnet, Product Face, security, key-management,
  release, remote proof and supply-chain gates.
- Harden public-safety and SBOM/source inventory scans against transient local
  paths that appear or disappear while validation is running.
- Add public schemas for generated doctor and quickstart smoke result
  artifacts so local audit output stays contract-validated.

## 1.1.0 - 2026-06-19

- Shipped the public Overkill Factory Bridge Codex plugin package, including
  install docs, inbox resolution, hook trust boundaries and the rule that the
  plugin acts only as an operator bridge, not as Hermes, the factory runtime,
  a gate approver or Receipt Five evidence.
- Replaced the legacy Solana core pack with `solana-ai-kit-core`, backed by
  `solanabr/solana-ai-kit@v2.0.2` as the official Solana domain-brain provider.
- Added deterministic Solana surface inference to worker routing. Worker
  packets now expose `input_contract.surface_router` with declared, inferred
  and effective surfaces plus route reasons.
- Added `domain_brain_provider` to Solana-domain worker packets and dynamically
  inject `solana-ai-kit` into relevant planning, architecture, build, wallet,
  QA, integration and security workers.
- Require `solana_ai_kit_usage_receipt` for real `PASS` results from
  Solana-domain workers, including cases where Solana was inferred from card
  content instead of declared in `surfaces`.
- Expanded public Solana coverage across Anchor, Pinocchio, Token-2022, SPL,
  NFT, Metaplex, DeFi, AMM, staking, governance, RPC, wallet and transaction
  surfaces while keeping Factory gates, Hermes state, Receipt Five, signer
  rules and human approvals above provider guidance.

## 1.0.0 - 2026-06-16

- Added the operator-first CLI path: `factoryctl doctor`, `factoryctl init` and
  `factoryctl run minimal`.
- Added public docs site navigation, CLI reference, Hermes install guide,
  example gallery, release policy and OSS security guide.
- Added Dependabot, CodeQL, Dependency Review and security workflow surfaces.
- Replaced dead public metadata URLs with canonical GitHub metadata, added a
  `.github/` entrypoint README and tightened public-safety scanning around
  metadata-only repository URLs and generated local build output.
- Added factory-owned recovery, status, readiness, truth and blocker paths so
  non-human blocks route back into explicit repair actions instead of hidden
  operator work.
- Added Product Face proof profiles, executable state/journey drivers and
  stricter Product Face PASS validation.
- Added capability-pack activation, full-product worker graph contracts and
  production/release preflight checks for public-safe repository releases.
- Added public-surface synchronization checks so docs and the published visual
  map can be verified against the repository source of truth.

Known boundary: the public repository release validates the factory kernel,
schemas, docs, CLI, examples and public safety. Private runtime/operator console
production readiness still requires operator-owned Hermes evidence and real
approval records outside the public repo.

## 0.1.0

- Initial public alpha package metadata, public quickstart, Hermes adapter,
  worker registry, schemas, examples and validation scripts.
