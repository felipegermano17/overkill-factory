# Overkill Factory Technical Reference

This page is the compact technical reference for the current public kernel. It is not a second manual. It answers how the Factory exists in this repository, how it connects to Hermes, what contracts and commands matter, and what the public proof does and does not prove.

## Current Public Kernel

The public kernel in this checkout is version `3.0.2`.

Current counts from the repository after syncing `origin/main`:

- 26 compiled phases in `docs/factory-workflow.catalog.json`,
- 14 route classes in `factory/templates/factory-route-registry.json`,
- 8 method engines in `factory/templates/method-engine-registry.json`,
- 17 operating-system areas in `factory/templates/factory-operating-system-registry.json`,
- 40 public workers in `factory/agents/worker-registry.public.json`,
- 17 capability packs in `factory/agents/capability-packs.public.json`,
- 251 JSON schemas in `factory/schemas/`,
- 163 JSON templates in `factory/templates/`,
- 102 Python test files in `factory/tests/`.

These are repository facts, not product-delivery claims. Local coherence is not live Hermes completion.

## Repository Layout

- `README.md`: short public entrypoint in English.
- `README.pt-BR.md`: short public entrypoint in Portuguese.
- `docs/en/factory-manual.md`: primary human manual.
- `docs/en/technical-reference.md`: this technical and operational reference.
- `docs/pt-BR/`: Portuguese mirror.
- `docs/assets/public-map/overkill-factory-map-v1.0.3.html`: complete visual map built with Archify.
- `factory/scripts/`: commands, validators, proof builders and audits.
- `factory/schemas/`: JSON schemas for official artifacts.
- `factory/templates/`: JSON and Markdown templates for official artifacts.
- `factory/agents/`: public worker registry, profile bindings, permission classes and capability packs.
- `factory/adapters/hermes/`: Hermes integration layer.
- `factory/examples/` and `factory/fixtures/`: public examples and test fixtures.
- `factory/tests/`: regression tests for the public kernel.

Documentation lives in `docs/`. Technology lives in `factory/`.

## Repo Kernel Versus Hermes Runtime

The repository is the formal kernel. It stores contracts, schemas, templates, registries, commands, validators, examples, fixtures and tests.

Hermes is the runtime floor. Hermes owns live cards, sessions, worker execution, Kanban state, attachments, comments, process state, gateway state and operational evidence.

The split matters:

- the repo can prove that the public kernel is coherent,
- Hermes can prove what happened in a live run,
- public documentation can explain the model,
- public documentation cannot prove private runtime delivery,
- the bridge can collect or forward operator events,
- the bridge must not become the Factory, close gates, execute worker work or approve human decisions.

Hermes owns runtime state. The Factory supplies control, contracts, gates, validators, worker boundaries and evidence expectations around it.

## Main Command Surface

Run commands from `factory/`:

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Useful commands:

```bash
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
python3 scripts/factoryctl.py validate-workflow-compiled-plan .tmp/factory-workflow-compiled-plan.json
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py method-engines
python3 scripts/factoryctl.py operating-systems
python3 scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md
python3 scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python3 scripts/factoryctl.py receipt-five-classify
python3 scripts/factoryctl.py human-gate-package
```

The command surface exists to make the method testable. Without commands, the Factory would be philosophy. With commands, it becomes contracts that can fail.

## The 26 Compiled Phases

The compiled workflow is the factual source for public phase shape:

1. F0 - Pre-Start / Sealed Source Envelope
2. F1 - Intake
3. F2 - Source Ledger
4. F3 - Source Resolution
5. F4 - Product Outcome And Discovery
6. F5 - Product SOT
7. F6 - Agentic Method Router
8. F7 - Method Contract
9. F8 - Pack And Product Experience Selection
10. F9 - Risk And Authority Gates
11. F10 - Security Architecture
12. F11 - Executable Plans
13. F12 - Autonomy Readiness
14. F13 - Ready Gate
15. F15 - Runtime Execution
16. F16 - Worker Results
17. F17 - Verification
18. F18 - Independent Review
19. F20 - Closure Summary
20. F21 - Receipt Five
21. F22 - Completion Audit
22. F23 - Production Operations
23. F24 - Release Or Block
24. F25 - Monitoring Support
25. F26 - Learnback
26. F27 - Factory Maturity Audit

The important idea is not the numbering. The important idea is that each phase must transform input into an output the next phase can consume. A phase that produces only a generic report is not a good phase.

## Route Classes

Routes answer: what kind of work is this?

Current route classes:

- `product_creation`
- `feature_delivery`
- `bug_repair`
- `incident_response`
- `brownfield_discovery`
- `release_promotion`
- `research_validation`
- `docs_onboarding`
- `security_remediation`
- `critical_integration`
- `migration_execution`
- `ux_product_experience`
- `analytics_data`
- `agent_quality_change`

Route matters because proof changes by work type. A bug needs reproduction and regression. A release needs rollback and authority. UX needs screenshots and journey proof. Security needs threat boundaries. Product creation needs Product SOT and scope coverage.

## Method Engines

Method engines answer: how should this type of work be proven?

Current method engines:

- `spec_first_sdd`
- `test_first_tdd`
- `behavior_first_bdd`
- `discovery_research`
- `security_first_threat_model`
- `design_first_product_experience`
- `legacy_diagnosis`
- `incident_first`

The method is not a label. It must materialize a Method Contract, required artifacts, required gates, required workers, proof requirements and forbidden shortcuts.

## Operating-System Areas

The Factory has 17 internal operating-system areas:

- Deterministic Control Plane OS
- Product Truth and Research OS
- Method OS
- Product Architecture OS
- Product Experience, Design and Brand OS
- Work Unit and Execution Dispatch OS
- Authority and Autonomy OS
- Hermes Worker Runtime OS
- Evidence and Receipt OS
- Capability Pack and Provider OS
- Agent and Profile Authority OS
- Security OS
- Quality and Verification OS
- Operator Experience OS
- Release and Operations OS
- Velocity, Cost and Throughput OS
- Factory Learning OS

These are not departments for show. They name the responsibilities needed to stop agentic work from becoming improvisation.

## Worker Roles

The public registry defines 40 public workers, including:

- `factory-orchestrator`
- `source-ledger-worker`
- `product-sot-planner`
- `product-architect`
- `product-face`
- `decomposition-planner`
- `implementation-worker`
- `frontend-builder`
- `backend-api-builder`
- `data-persistence-builder`
- `qa-verification-worker`
- `independent-reviewer`
- `evidence-reconciler`
- `human-gate-clerk`
- `release-ops-worker`
- `public-safety-gate`
- `supply-chain-gate`
- `solana-quasar-builder`
- `solana-quasar-auditor`
- `wallet-transaction-builder`
- `codex-security`
- `appsec-owasp-specialist`
- `agentic-ai-security-specialist`
- `cloud-infra-security-specialist`
- `crypto-key-management-specialist`

A worker is not a character name. It needs registry identity, authority limit, trigger, input contract, tool scope, output contract, evidence policy, veto conditions and Hermes binding when it becomes executable.

## Security Domain Coverage

Security work is explicit because public safety cannot depend on a generic "security review." The current machine-checkable security domains are:

- `networking`
- `linux-systems`
- `web-security`
- `ethical-hacking`
- `security-tools`
- `cloud-security`
- `detection-monitoring`
- `cryptography`
- `security-operations`
- `future-security`
- `supply-chain`
- `onchain-solana-quasar`

These names matter because workers and validators use them to prove that security coverage is owned instead of implied.

## Capability Packs

Capability packs answer: does the Factory have a kit for this domain?

Current pack names include web/SaaS, CLI/TUI, cloud-native, agent runtime, Solana AI Kit, mobile, desktop, game, AI/ML, fintech/payments, regulated domain, analytics, browser extension, operator onboarding, public docs, operator artifact media and hardware/IoT.

Some packs are core. Some are templates that must be activated before material execution. A template pack is not a delivery claim.

## Critical Artifacts

The main artifacts are:

- Universal Signal Intake
- Source Resolution Packet
- Product Source Ledger
- Operator Understanding Confirmation
- Product Understanding Packet
- Outcome Contract
- Product SOT
- full Product SOT scope coverage
- Method Contract
- Product Creation Plan
- Decomposition Coverage Review
- Product Implementation Readiness
- Ready Work Unit Packets
- Hermes Materialization Plan
- Worker Packet
- Worker Result
- Product Face Result
- Security Architecture Plan
- Human Gate Package
- Operator Delivery Receipt
- Evidence Bundle
- Review Result
- Receipt Five
- Completion Audit
- Learnback Proposal

The list is long because production is real. The public docs stay short because the user should not have to read every schema before understanding the system.

## Evidence Rules

The Factory does not accept language as proof.

Evidence can be:

- test output,
- build output,
- lint or typecheck result,
- schema validation,
- readback of created files,
- screenshot,
- browser journey,
- CLI command output,
- curl response,
- logs,
- CI status,
- pull request state,
- deployed URL check,
- security review,
- independent review,
- operator delivery receipt,
- Hermes card state,
- Receipt Five.

Evidence must be reconciled to the claim. A screenshot does not prove backend behavior. A unit test does not prove UX. A local PASS does not authorize production. A review-only PASS does not authorize release.

## Human Gates

Human gates are required for real authority:

- production,
- mainnet,
- funds,
- signing,
- secrets,
- billing,
- destructive actions,
- high-risk architecture,
- accepting residual risk,
- publishing sensitive material,
- strategic scope changes.

A valid human gate should state the decision, options, consequences, recommendation, evidence, risk, what approval authorizes, what approval does not authorize and the exact expected answer.

The operator delivery receipt proves the question reached the operator. A hidden "waiting for owner" note in Kanban is not enough.

## Public Safety

Public GitHub is a product surface. It must not become a dump for internal context.

Important validators include:

```bash
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
```

Public docs must not leak private paths, raw internal conversations, tokens, screenshots, temporary artifacts, private board IDs or unsupported promises.

## Visual Map

The public visual map is here:

[Overkill Factory visual map](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)

The local file is:

`docs/assets/public-map/overkill-factory-map-v1.0.3.html`

It is built with Archify and is a supporting explanation. The map is not the source of truth and does not prove runtime readiness.

## Proof Boundary

A local `doctor` or `run minimal` pass means the public kernel is coherent enough to run its public checks.

It does not prove:

- a real product was delivered,
- live workers executed,
- a private Hermes board is correct,
- a deployment is healthy,
- a public release is complete,
- mainnet readiness, signing, custody or funds movement,
- human approval was given.

Real product proof needs live Hermes state, a real card, worker result, specific evidence, readback, independent review, Receipt Five and human gate approval when required.
