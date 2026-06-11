# Worker Profiles

This page is the public operator guide for the agent layer. Exact machine
contracts live in:

- `agents/worker-registry.public.json`;
- `agents/worker-profiles.public.json`;
- `agents/hermes-profile-bindings.public.json`;
- `agents/capability-packs.public.json`;
- `agents/worker-permission-classes.public.json`;
- `docs/agents/capability-packs.md`;
- `docs/agents/factory-stage-agent-map.md`;
- `docs/agents/permission-model.md`;
- `docs/agents/live-agent-configuration.md`.

## Coverage

The factory covers the full production line by separating workers into eight
ownership groups:

| Group | Coverage |
| --- | --- |
| Orchestration and source | phase, source, memory and routing before product truth is claimed. |
| Product planning and architecture | Product SOT, architecture, Product Face and documentation before decomposition. |
| Builders | frontend, backend, data, onchain, wallet, integration, tests, infra and agent runtime. |
| Proof and review | QA, AutoReview, remote proof, evidence reconciliation, independent review and handoff. |
| Security and release safety | AppSec, agentic AI security, cloud, key management, supply chain, public safety and monitoring. |
| Human authority | human gate records and release authority boundaries. |
| Control Tower | read-only cockpit projection and Discord/Hermes bridge behavior. |
| Learning | skill and eval distillation after repeated evidence. |

This is phase coverage, not a promise that every product type is already
covered by an executable specialist.

Product-type coverage is handled by capability packs in
`agents/capability-packs.public.json`. `factoryctl` blocks execution when a
card asks for a surface that is not covered by a ready core pack or an activated
optional pack.

This is how we know the agents cover a specific card: each phase has an owner,
each risk surface has a specialist, each product surface has capability-pack
coverage, each worker has a receipt field, and `factoryctl` can route required
packets from the card contract.

For stage-by-stage ownership, use `docs/agents/factory-stage-agent-map.md`.
That map is the public bridge between the canonical process and the executable
worker names. It also names the proof that blocks the next stage.

## Product-Type Packs

Ready packs:

| Pack | Coverage |
| --- | --- |
| `web-saas-core` | ordinary web, SaaS, API, data, auth, integration, tests, docs, release and monitoring work. |
| `cloud-native-core` | CI/CD, runtime, cloud, monitoring, rollback and production operations boundaries. |
| `agent-runtime-core` | Hermes, Factory, profiles, skills, memory, tools, MCP and autonomous workflow changes. |
| `solana-quasar-core` | Quasar-first Solana/onchain program work, wallet transaction boundaries and onchain QA. |

Template packs that must be activated before execution:

| Pack | Missing specialist direction |
| --- | --- |
| `mobile-app-pack` | native/mobile builder and mobile QA. |
| `desktop-app-pack` | desktop runtime, packaging and update-path builder. |
| `game-product-pack` | game runtime, game design and game QA specialists. |
| `ai-ml-product-pack` | AI/ML product builder and model eval worker. |
| `fintech-payments-pack` | payments ledger builder and fintech risk specialist. |
| `regulated-domain-pack` | domain compliance specialist. |
| `data-analytics-pack` | analytics/data-quality builder. |
| `browser-extension-pack` | browser extension builder and permission proof. |
| `hardware-iot-pack` | hardware/IoT specialist with physical safety proof. |

See `docs/agents/capability-packs.md` for the full rule.

## How To Read The Table

- Responsibility: what the worker owns.
- When it enters: factory phase or routing moment.
- Receives: the inputs it expects.
- Delivers: the receipt field or result it must produce.
- Must not: the authority boundary.
- Evidence: what proves the worker actually ran.
- Tooling: the typical tool or Hermes profile route.

| Worker | Responsibility | When it enters | Receives | Delivers | Must not | Evidence | Tooling |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `factory-orchestrator` | Keeps phase, risk, routing, method contract, capability coverage, readiness and blocker state coherent. | F0-F18. | phase, risk, surfaces, done definition, method contract, capability coverage, autonomy readiness. | `orchestration_result`. | Approve gates or waive findings. | gate report, routing decision, method route, readiness blockers, next actions. | Hermes Kanban, `factoryctl gate-report`. |
| `source-ledger-worker` | Separates source facts, inference, decisions, conflicts, stale material and gaps. | F0-F1. | source refs, source state, source conflicts and prior decisions. | `source_ledger_result`. | Promote unsourced decisions. | source map, source resolution notes, promoted/rejected claims, conflict list, gap list. | repo search, browser capture when needed. |
| `product-sot-planner` | Owns Outcome/Discovery and drafts the Product SOT candidate. | F2-F3. | source refs, outcome contract, discovery notes, assumptions, scope, acceptance criteria. | `product_sot_result`. | Treat a candidate as approval or turn assumptions into scope silently. | outcome contract, discovery notes, assumption ledger, SOT candidate, open questions. | planning templates, decision packet. |
| `product-architect` | Creates candidate architecture, risk routing and security architecture route when needed. | F4-F6. | scope, risk, runtime contract, dependency map, security architecture plan. | `architecture_result`. | Bypass architecture, security route or human gates. | architecture packet, trust boundaries, tradeoffs, risk matrix, ADR refs. | architecture review workflow. |
| `product-face` | Defines and validates visible product surfaces across web, mobile, desktop, game-like and agentic interfaces. | F5 and F13. | Product Face packet, paths, acceptance criteria, journey proof needs. | `product_face_result`. | Approve product alone. | screenshots, states, journeys, a11y notes, overlap/performance notes. | browser, screenshots, Product Face proof. |
| `docs-os-worker` | Turns approved architecture into durable docs and contracts. | F10. | done definition, acceptance criteria, paths, doc shape. | `documentation_os_result`. | Authorize implementation. | docs index, ADR refs, contract refs, doc-shape routing. | documentation workflow. |
| `decomposition-planner` | Creates the Hermes work graph, Spec Graph, Loop Plan and bounded work-unit contracts. | F11. | done definition, risk, runtime, security, software development plan, loop plan, Spec Graph, lane/worktree isolation. | `decomposition_result`. | Skip required gates or launch parallel lanes without boundaries. | card graph, dependencies, gate mapping, Spec Graph, Loop Plan, work-unit contract refs, reviewer selection refs. | factory card schema, Hermes planning. |
| `implementation-worker` | Fallback implementation worker when no specialist builder fits. | F12. | scoped implementation card. | `implementation_result`. | Replace a matching specialist builder. | diff refs, tests, handoff notes. | Hermes implementation profile. |
| `frontend-builder` | Builds screens, components and responsive UI. | F12-F13. | Product Face packet, paths, acceptance criteria. | `frontend_build_result`. | Self-validate Product Face. | diff refs, UI tests, state notes. | frontend tooling, browser. |
| `backend-api-builder` | Builds API, service, validation and auth/session behavior. | F12-F13. | API contract, paths, acceptance criteria. | `backend_api_build_result`. | Change security scope alone. | contract tests, API checks, diff refs. | backend test tooling. |
| `data-persistence-builder` | Builds schema, migrations, storage and data access. | F12-F13. | schema scope, rollback notes, paths. | `data_persistence_result`. | Hide migration or data risk. | migration diff, rollback note, tests. | database/local test tooling. |
| `solana-quasar-builder` | Builds scoped Solana program work using Quasar. | F12-F13. | onchain package, paths, done definition. | `solana_quasar_build_result`. | Use Anchor assumptions, deploy, sign or touch funds. | Quasar build/test refs, signer map. | Quasar toolchain. |
| `solana-quasar-qa-engineer` | Verifies onchain behavior, negative tests and compute units. | F13-F15. | onchain package, paths, done definition. | `solana_quasar_qa_result`. | Waive Auditor or security findings. | local/devnet refs, negative tests, CU notes. | Quasar QA, simulation. |
| `wallet-transaction-builder` | Builds wallet connection, signing prompts and transaction states. | F12-F13. | Product Face packet, security contract, scope. | `wallet_transaction_result`. | Touch real keys or funds. | transaction-state tests, signer boundary notes. | wallet fixtures, browser. |
| `integration-builder` | Connects approved surfaces into an end-to-end flow. | F12-F13. | scope, runtime, upstream outputs. | `integration_build_result`. | Patch around missing upstream evidence. | E2E refs, connected surface list. | integration tests, browser, API checks. |
| `test-automation-builder` | Converts acceptance criteria into repeatable tests or evals. | F12-F13 and F18. | criteria, done definition, paths. | `test_automation_result`. | Redefine acceptance alone or hide flakes. | test refs, command logs, coverage gaps. | unit, integration, E2E, eval harness. |
| `infra-devops-builder` | Prepares CI, runtime and deploy wiring. | F12 and F16. | runtime contract, rollback, scope. | `infra_devops_result`. | Release production alone or store secrets. | config diff, smoke result, rollback notes. | CI/CD and environment tooling. |
| `agent-runtime-builder` | Builds Hermes/factory adapter, profile, skill and routing changes. | F12 and F18. | runtime contract, security contract, scope, agent eval plan. | `agent_runtime_result`. | Expand tools silently or self-approve safety. | adapter tests, profile/binding refs, eval result refs. | Hermes adapter and profile tooling. |
| `qa-verification-worker` | Verifies objective proof before done. | F13-F15. | criteria, done definition, paths, QA mode plan. | `qa_verification_result`. | Waive risk or ignore failures. | commands, outputs, artifacts, pass/fail, mode coverage. | test, screenshot and log tools. |
| `independent-reviewer` | Reviews evidence produced by a different executor. | F14. | executor, reviewer, done definition, reviewer selection plan. | `independent_review_result`. | Review its own work or replace human gates. | review report, selected coverage, findings, residual risk. | independent Hermes/Codex profile. |
| `autoreview-gate` | Runs structured pre-landing review. | F14-F15. | diff scope, done definition. | `autoreview_result`. | Approve release alone. | review report, finding status. | AutoReview workflow. |
| `remote-proof-runner` | Runs clean or heavy proof with TTL and cleanup evidence. | F13-F16. | runtime, paths, done definition. | `remote_proof_result`. | Receive secrets by default. | logs, artifacts, timing, cleanup, cost note. | Crabbox, Testbox or container fallback. |
| `evidence-reconciler` | Reconciles Closure Summary, Receipt Five and Completion Audit against current worker results. | F13-F16. | done definition, worker artifacts, transition ref, closure summary, completion audit. | `receipt_five_reconciliation_result`. | Approve gates, waive findings or invent missing proof. | effective result index, supersession ledger, missing/blocking list, closure summary, completion audit verdict. | Receipt Five indexer. |
| `handoff-packer` | Creates replayable state packets for transfer or pause. | F9-F15. | paths, done definition, constraints. | `handoff_packet_result`. | Invent approval or evidence. | state, constraints, artifact refs, next action. | handoff workflow. |
| `security-orchestrator` | Routes Security Architecture Plan, privacy/compliance route and the right security specialists. | F4-F16. | security architecture plan, security contract, privacy/compliance route, risk, scan packet. | `security_orchestration_result`. | Treat generic security comments as evidence or postpone architecture security to final scan. | specialist matrix, owner mapping, blocking policy, required security gates. | security control matrix. |
| `codex-security` | Runs scoped security scans and reports findings. | F8 and F13. | scan packet, paths, forbidden actions. | `security_scan_result`. | Waive blocking findings. | scan result, scope, tool, evidence refs. | Codex Security or equivalent scanner. |
| `appsec-owasp-specialist` | Covers web, API, auth, session and validation controls. | F7, F14, F15. | scan packet, paths, criteria. | `appsec_owasp_result`. | Accept unsafe errors or untested auth. | control matrix, test refs, residual risks. | OWASP Web/API/AppSec review. |
| `agentic-ai-security-specialist` | Covers prompt, tool, memory and browser risk. | F1, F7, F12, F14. | security contract, runtime, forbidden actions. | `agentic_ai_security_result`. | Treat external text as trusted instructions. | tool allowlist, memory trust tier, injection controls. | agentic AI security review. |
| `cloud-infra-security-specialist` | Reviews cloud, IAM, KMS, CI/CD, DNS and rollback risk. | F7 and F16. | scan packet, runtime, rollback. | `cloud_infra_security_result`. | Mutate production or accept broad access. | least-privilege notes, rollback proof, monitoring plan. | cloud/IaC security checks. |
| `crypto-key-management-specialist` | Reviews secrets, signing, custody and key lifecycle. | F7 and F16. | security contract, forbidden actions, risk. | `crypto_key_management_result`. | Touch real keys or funds. | key boundary map, custody model, waiver notes. | key-management checklist. |
| `solana-quasar-auditor` | Audits or preflights Solana/Quasar work. | F7, F13, F15. | onchain package, paths, risk. | `auditor_result`. | Deploy, sign, touch funds or call preflight a code-audit pass. | Auditor report, PDA/signers/CPI/CU checks. | Auditor and Quasar-aware review. |
| `supply-chain-gate` | Checks dependency, CI, secret and provenance risk. | F11, F13, F16. | paths, runtime, scan packet. | `supply_chain_result`. | Waive release blockers. | dependency report, secret scan, workflow review, SBOM or waiver. | supply-chain tooling. |
| `detection-monitoring-worker` | Owns Data/Metrics planning plus logs, alerts, incident ownership and rollback signals. | F4 and F16-F17. | data metrics plan, event contract, dashboard contract, rollback, security, done definition. | `detection_monitoring_result`. | Approve release alone or claim product success without measurable signal. | metric contract, event plan, dashboard or health proof, monitoring plan, alert owner, incident notes. | observability review. |
| `human-gate-clerk` | Prepares and records real human decisions for authority, access, budget, waiver and release scope. | F9, F15, F16. | gate packet, evidence, rollback, access capability, budget contract, waiver request. | `human_gate_record`. | Invent approval or merge access, budget and release into one vague decision. | decision, approval scope, actor role, durable runtime event, evidence refs. | Hermes decision record. |
| `release-ops-worker` | Prepares release channel, production operations packet, smoke and rollback readiness. | F16-F17. | done definition, rollback, human gate packet, release plan, production operations plan. | `release_ops_result`. | Release without gate, owner, rollback or monitoring. | release channel evidence, release plan, rollback proof, production smoke, monitoring refs. | release workflow. |
| `public-safety-gate` | Blocks private or secret residue before public release. | F16-F17. | paths, forbidden actions, done definition. | `public_safety_result`. | Approve product risk. | public safety scan, redaction notes. | `public_safety_scan.py`. |
| `memory-steward` | Classifies memory and context as a trust surface. | F0-F1 and F18. | source refs, source state, security contract. | `memory_steward_result`. | Turn memory into truth. | trust tier, freshness, source refs, poisoning controls. | memory review workflow. |
| `skill-eval-distiller` | Owns Agent Quality, Learnback and Factory Maturity audits, then turns repeated success or failure into skills, evals, templates, checklists or pack/worker changes. | F8 and F18. | expected evidence, done definition, source refs, agent eval plan, factory maturity scorecard, worker coverage map. | `skill_eval_result`. | Promote one-off work as a closed skill, ignore blind spots or grant broad authority. | agent quality plan, repetition evidence, eval cases, before/after result, factory maturity scorecard, missing coverage register, permission class. | skill and eval workflow. |
| `control-tower-projection-worker` | Projects Hermes state into the operator cockpit. | F19. | runtime state, projection contract, staleness boundary. | `project_projection_result`. | Change state, approve gates or hide blocked work. | projection result, source state ref, staleness note. | Control Tower projection contract. |
| `discord-control-tower-bridge` | Maps Hermes and Discord events. | F19 and F29. | mapping, runtime event, bridge health contract. | `control_tower_bridge_result`. | Decide product direction, execute workers or mutate cards directly. | mapping proof, round-trip proof, bridge health. | Discord Control Tower bridge. |

## Runtime Rule

A worker is operable only when all four layers exist:

1. process role in `agents/worker-registry.public.json`;
2. agent profile in `agents/worker-profiles.public.json`;
3. Hermes binding in `agents/hermes-profile-bindings.public.json`;
4. card-specific worker packet from `scripts/factoryctl.py`.

Profile names alone are not enough. The binding must also define skill refs,
queue policy, result schema, receipt field and evidence path policy.

## Minimal Agent Setup

Preview local Hermes profile materialization:

```bash
python scripts/materialize_hermes_profiles.py --profiles-dir ./.hermes-profiles
```

Apply it only after reading the preview:

```bash
python scripts/materialize_hermes_profiles.py --profiles-dir ./.hermes-profiles --apply
```

Run validation after any profile, registry or binding change:

```bash
python scripts/validate_worker_profiles.py
python scripts/validate_public_json_artifacts.py
python -m unittest tests.test_worker_profiles -q
```
