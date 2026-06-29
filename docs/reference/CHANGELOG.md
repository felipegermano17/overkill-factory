# Changelog

All notable public changes should be recorded here.

The format follows Keep a Changelog principles and uses semantic versioning for
public releases.

## Unreleased

- Replace the mistaken markdown public map with a simpler V3 update to the
  existing published visual map, keeping the public GCS URL as the entrypoint.
- Remove the unfinished Codex Bridge plugin from the Factory V3 public surface:
  repo-local marketplace, project hooks, plugin package, plugin docs, bridge
  skill package, plugin test and Codex-specific operator channel are no longer
  part of the current product claim.
- Reframe the operator bridge as a narrow start/inbox contract owned by
  `factory/scripts/factory_bridge.py`, not a product plugin or shadow runtime.

## 3.0.2 - 2026-06-29

- Add a literal 17-item master-plan Definition of Done audit that separates
  local implementation support from external live proof, so Telegram/operator
  gaps cannot be hidden behind a generic 100% score.
- Add operator-facing artifacts for the remaining implementable DoD surface:
  manager intake smoke, manager profile live/dry-run smoke, progress card,
  delivery receipt, Product Face Result proof, learnback proposal, Telegram
  start dry-run/live smoke, and a dependency-free PDF plus text fallback for
  human gate packages.
- Harden V3 release readiness to require the literal DoD audit command in the
  Factory Perfect Run release policy.

## 3.0.1 - 2026-06-29

- Activate the V3 master plan operationally instead of leaving it as release
  bookkeeping: worker profiles, Hermes profile bindings and the worker registry
  now carry `v3.0.0-master-plan-100` activation metadata, required checks,
  evidence policy and manager-only operator routing.
- Add a strict `factory-master-plan-completion` audit covering waves 0-9 with
  code, tests, commands, runtime refs, agent refs, operator refs and evidence
  refs for every wave.
- Add Factory Perfect Run proof commands, including a deterministic E2E record
  and a live Hermes Kanban smoke that creates, comments, blocks, unblocks and
  completes a disposable runtime card with Receipt Five metadata.
- Make `factoryctl v3-production-activation-check --live-hermes` the explicit
  activation path, and harden V3 release readiness so release is blocked when
  Factory Perfect Run evidence or commands are missing.
- Make the Hermes adapter enforce V3 runtime truth, canonical frontier/no-idle
  boundaries, manager/agent freshness, artifact-first human gates and Receipt
  Five readback before reporting V3 production activation.

## 3.0.0 - 2026-06-29

- Promote the public kernel to the V3 release line after the V3 master update
  plan landed in PR #534.
- Add executable V3 readiness guards for the master update plan, Hermes-first
  runtime truth spine, canonical frontier/no-idle autonomy, gerente/agent
  freshness and V3 release readiness.
- Add a simplified public map at `docs/visuals/overkill-factory-map-v1.0.3.html` so external
  operators can understand the repository through a clear first-value path
  instead of the older complex visual map.
- Make the central boundaries executable: Hermes/Kanban own runtime state,
  queues, dispatch, task lifecycle and boards; Overkill Factory owns method,
  gates, rules, schemas, audits, validations and release checks.
- Prevent the historical stale-gerente failure mode by requiring manager and
  affected agent skills, profiles, configs and bindings to stay current with
  factory contracts before E2E or release.
- Consolidate waves 4-9 into a V3 release readiness policy covering
  artifact-first human gates, Receipt Five anti-overclaim, Product SOT/method/
  architecture boundaries, capability/security/release authority, Solana AI Kit
  routing and the Factory Perfect Run bar.

## 2.0.15 - 2026-06-28

- Add a schema-backed Decomposition Coverage Review between Product Creation
  Plan and Product Implementation Readiness. Product Implementation Readiness
  cannot pass unless the review is `PASS`, references the Product Creation Plan
  and covers every planned work unit.
- Move the workflow contract to the correct F11/F12 boundary: F11 creates the
  complete Product Creation Plan; F12 runs independent multi-operator coverage
  review and only then creates readiness for execution.
- Align worker registry, worker profiles, Hermes bindings and public agent docs
  with the workflow phases so required workers cannot depend on agent memory or
  free-form interpretation.
- Strengthen `factory/scripts/validate_worker_profiles.py` so workflow-required workers
  must have registry/profile phase coverage, aliases must resolve to real
  bindings, and decomposition/readiness artifacts require the right workers.

## 2.0.14 - 2026-06-27

- Make the Factory Run Graph more Hermes-native: downstream backbone phase cards
  are created with native parent dependencies, and materialized work-unit cards
  become parents of the next phase/closure card while that next phase is still
  in the native dependency-wait state.
- Fail closed on phase ordering drift: no-idle now reports a
  `factory_phase_invariant_violation` before remediation when the Kanban graph
  shows a later phase running while an earlier required phase is blocked, and
  late work-unit dependencies cannot be attached after the downstream phase is
  already `ready`, `running` or `done`.
- Treat typed Hermes blocks as a structured contract: free-text "human gate" or
  "decision package" wording no longer pages the operator unless the block kind
  is explicitly `needs_input`; dependency, capability and transient blocks stay
  factory-owned.
- Make all-board watchdog scans audit-only by default. Discovered boards no
  longer receive remediation or dispatch unless explicitly named or the operator
  opts in with `--allow-discovered-board-mutation`.
- Add the `discovery_brief` contract and strengthen phase-source validation so
  catalog output artifacts, phase graph exit refs and schemas cannot drift.
- Extend public docs, install guidance and Codex skills with the same
  Kanban-native dependency rule and public repo surface cleanup policy.

## 2.0.13 - 2026-06-27

- Promote the Kanban-native runtime mantra into the public Codex
  `overkill-factory` skill so operators and agents receive the same rule as the
  architecture docs: prefer durable Hermes Kanban graph state, dependencies,
  typed blocks and native dispatch over sidecar loops or agent interpretation.

## 2.0.12 - 2026-06-27

- Preserve the declared-artifact repair runtime hotfix in the public release:
  `declared_artifact_readback_repair` tasks with `repair_type` and
  `result=PASS` metadata are now treated as self-evidenced, preventing another
  repair loop without requiring a new remediation card.

## 2.0.11 - 2026-06-27

- Materialize the Factory Run Graph when a new project starts: F1 is the root
  runnable card, downstream backbone phases are created as native Hermes Kanban
  cards, and future phases are linked with explicit `dependency` edges instead
  of being invented later by agent memory or no-idle recovery.
- Make the runtime mantra executable and documented: less mirabolante, more
  Kanban-native, more Hermes-native, more deterministic and easier to trust.
- Demote no-idle/watchdog authority to integrity audit and graph repair; normal
  route authority now belongs to the materialized graph plus the phase engine.
- Add release-preflight runtime autonomy regressions and public-safety coverage
  for the new start graph behavior.

## 2.0.10 - 2026-06-27

- Harden runtime autonomy after the Todo Web Local end-to-end factory test:
  no-idle can close over-time running tasks when Hermes has terminal
  worker-result metadata, post-repair review tasks fail closed when dependency
  links do not persist, and Receipt Five closeout separates public artifacts
  from private runtime evidence.

## 2.0.9 - 2026-06-26

- Republish the public visual map as `v1.0.3` so the current documentation can
  validate against a fresh public URL instead of waiting for stale storage cache
  on the previous `v1.0.2` asset.

## 2.0.8 - 2026-06-26

- Replace the public planning-bundles surface with generated factory reference
  documentation produced from workflow, worker, profile, OS, method, schema,
  template and public-surface contracts.
- Publish visual map `v1.0.2` with simpler operator language while preserving
  required fidelity terms, risk tiers and public-boundary checks.
- Remove dated public audit/plan artifacts from `docs/` and promote useful
  Telegram/operator and context-spine rules into current guides.
- Update CI, release validation, README docs and the Codex `overkill-factory`
  skill so generated documentation drift fails closed.

## 2.0.7 - 2026-06-26

- Clarify and test the real Hermes dependency semantics proven by live smoke:
  durable dependency waiting comes from parent edges or current `todo`
  `dependency_wait` state; a no-parent `dependency` block can recompute to
  `ready` and must remain dispatchable instead of becoming a fake wait.
- Add regression coverage so a `ready` task with historical `dependency_wait`
  event history is not mistaken for a current native dependency wait; normal
  ready/reconcile rules still decide the next action.

## 2.0.6 - 2026-06-26

- Preserve native Hermes `dependency_wait` before phase-engine repair planning:
  current `todo` dependency waits stay in the Hermes dependency lane instead
  of becoming generic factory remediation.
- Add regressions proving typed Hermes dependency/loop events win over the
  board reconciler unless an earlier deterministic phase invariant already
  blocks execution.

## 2.0.5 - 2026-06-26

- Fix no-idle typed block loop handling against the real Hermes #52848 runtime:
  `block_loop_detected` cards move to `triage`, so no-idle now queries and
  enriches `triage` before classifying loop-breaker state.
- Add regression coverage for the real Hermes event shape
  `events[].kind = block_loop_detected` with `payload.kind = transient`, and
  surface `triage` counts in watchdog loop reports.

## 2.0.4 - 2026-06-26

- Adapt Factory V2 to Hermes Kanban typed block reasons from upstream #52848:
  add `hermes_typed_block_policy`, require native `dependency`, `needs_input`,
  `capability` and `transient` semantics, and validate `block_loop_detected`
  / `dependency_wait` handling.
- Update Hermes live adapter, transition hook and no-idle watchdog so generic
  blocks no longer become human pages: dependency waits remain native waits,
  same-cause loops route triage, capability blocks require acquisition, and
  transient blocks route repair/retry.

## 2.0.3 - 2026-06-26

- Complete the public Factory V2 runtime-spine contract set with profile
  compatibility aliases, skill provider registry, Product Method Runtime,
  operator delivery, Product Experience evidence stack, Security OS matrix,
  Hermes blocked-first protocol and reference-derived negative fixtures.
- Add `factoryctl validate-v2-runtime-contracts`,
  `validate-agent-skill-boundaries`, `validate-reference-superiority`,
  `capability-acquisition-run` and `validate-capability-acquisition-run`.
- Make missing capability handling executable: the factory now writes a
  `capability_acquisition_run` receipt from skill providers, capability packs
  and reference search refs, and it can block only after `search_completed=true`.
- Update the Hermes Kanban compatibility contract for the current native
  primitives: `gateway start`, dispatch/watch/tail/runs/diagnostics and
  notify-subscribe/list/unsubscribe.
- Wire the new V2 validators and capability acquisition receipt into release
  preflight, public docs, README and the Codex `overkill-factory` skill.
- Extend V2 traceability and doc-implementation obligations so public claims
  fail validation when they are stronger than the implemented artifacts,
  tests and negative fixtures.

## 2.0.2 - 2026-06-26

- Harden Factory V2 against raw-study simplification: add phase graph,
  V2 study traceability, worker authority, Product Experience control plane,
  capability acquisition, Hermes reducer mutation proof and scoped readiness
  contracts with CLI validation and regression coverage.
- Require embedded runtime/security contracts on factory cards and first-class
  Solana AI Kit/onchain work-package receipts for Solana-domain execution.
- Expand the canonical Operating System registry from 11 broad areas to 17
  executable ownership systems, including capability provider, Product
  Experience, agent authority, velocity/cost and factory learning.
- Update the public README, CLI reference, factory/schemas/templates docs and Codex
  skill surface so V2 is described as a deterministic control plane, not as an
  agent-driven vFinal playbook.

## 2.0.1 - 2026-06-26

- Promote the live Hermes no-idle gate fix into the public Factory V2 release
  ([#447](https://github.com/felipegermano17/overkill-factory/issues/447)).
- Create a fresh lineage-bound remediation card when the deterministic
  no-idle remediation idempotency key points to a terminal stale task, instead
  of reporting that remediation exists while the board still has no runnable
  frontier.
- Keep factory runtime/code-review PASS records from being treated as Product
  SOT owner-review evidence, and avoid recreating Product SOT owner decision
  packages after a recorded owner decision closes the gate.

## 2.0.0 - 2026-06-26

- Add the Factory V2 deterministic control plane: workflow compiled plan,
  factory command inbox, hash-chained run events, factory run state, decision
  outbox, promotion packet and reference-superiority claim contracts
  ([#445](https://github.com/felipegermano17/overkill-factory/issues/445)).
- Add `factory/scripts/factory_v2_kernel.py` and `factoryctl` commands for compiling the
  workflow catalog and validating V2 run, command, event log, decision outbox,
  promotion packet and compiled workflow artifacts.
- Add public templates and regression coverage for V2 control-plane contracts.
- Harden the operator bridge so status/question/decision/change/exception/
  handoff modes require explicit runtime targets, corrupt inbox records are
  reported instead of hidden, existing-project refs require explicit runtime
  prefixes and human gate responses require `human_gate_record_ref`.
- Stop public JSON validation from treating transient `.tmp/factory-runs`
  runtime evidence as public release surface.
- Document the Factory V2 control plane and update README/CLI surfaces for the
  new release line.

## 1.5.16 - 2026-06-25

- Require Product SOT human gates to deliver a canonical localized Product SOT
  as the primary human artifact
  ([#440](https://github.com/felipegermano17/overkill-factory/issues/440)).
- Keep approval JSON, evidence indexes, hashes, schemas, validation receipts and
  worker logs as supporting evidence instead of allowing them to become the SOT
  body.
- Require Telegram/operator-channel delivery through the configured
  manager-facing profile when one exists, and forbid English-only Product SOT
  delivery for a Portuguese operator flow.

## 1.5.15 - 2026-06-25

- Fix post-delivery no-idle classification for Product SOT owner gates
  ([#438](https://github.com/felipegermano17/overkill-factory/issues/438)):
  a `human-gate-clerk` task that has already delivered Markdown/PDF,
  `APPROVAL_REQUEST`, `EVIDENCE_INDEX`, `OWNER_REVIEW` and validation evidence
  is now treated as a real `human_gate_required` state, not as another generic
  factory package repair.
- Give delivered human-gate packages precedence over internal package-repair
  heuristics, even when the task text contains words such as "decision package",
  "PDF" or "evidence index".

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
