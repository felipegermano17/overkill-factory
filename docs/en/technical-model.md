# Technical Model

Overkill Factory is implemented as a Python package, CLI, contract library, Hermes adapter surface, public worker registry, and documentation site.

It is intentionally not a replacement for Hermes.

## Repository shape

```text
README.md              public English entry
README.pt-BR.md        public Portuguese entry
docs/                  canonical public documentation and public catalogs
factory/               implementation, contracts, tests, examples, legacy docs
```

Inside `factory/`:

- `scripts/` contains `factoryctl.py` and validators;
- `schemas/` contains JSON schemas for contracts;
- `templates/` contains canonical example/contract templates;
- `agents/` contains public worker registries, profiles, readiness, and bindings;
- `adapters/hermes/` contains integration code for Hermes runtime boundaries;
- `examples/` and `fixtures/` contain public examples and validation fixtures;
- `tests/` protects behavior and public claims;
- `legacy-docs/` preserves non-canonical older documentation.

## Public kernel counts

The current executable surface inspected for this documentation contains:

- 244 schemas;
- 156 JSON templates;
- 97 tests;
- 40 public workers;
- 14 route classes;
- 8 method engines;
- 17 operating-system areas;
- 26 compiled workflow phases.

## `factoryctl`

`factoryctl` is the public control helper. It validates contracts, creates local proof artifacts, compiles workflow plans, generates worker packets, checks public JSON artifacts, and runs smoke paths.

Important commands:

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
python3 scripts/factoryctl.py validate-runtime-contracts
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py operating-systems
python3 scripts/factoryctl.py method-engines
```

`factoryctl` can prove local contract coherence. It does not replace Hermes runtime proof.

## Runtime boundary

Hermes owns runtime state. Overkill Factory owns method contracts and checks.

That means:

- a local JSON file is not a real running board;
- a generated packet is not completed work;
- a worker profile is not a worker result;
- a passing local smoke is not a production release;
- a human gate cannot be faked by a script.

## Operating-system registry

The factory groups critical areas into operating-system entries:

- **Deterministic Control Plane OS** (`deterministic_control_plane_os`): owner `factory-orchestrator`, status `active`. Own the reducer-first factory spine: phase graph, commands, events, decision outbox, replay and promotion boundaries.
- **Product Truth and Research OS** (`product_truth_research_os`): owner `source-ledger-worker`, status `active`. Own deep product starts before Product SOT: sources, claims, conflicts, brownfield study, research decisions and operator understanding.
- **Method OS** (`method_os`): owner `factory-orchestrator`, status `active`. Turn method routing into deterministic method engines rather than broad method-family labels.
- **Product Architecture OS** (`product_architecture_os`): owner `product-architect`, status `active`. Own architecture candidates, trust boundaries, integration shape, data boundaries and technical decisions before decomposition.
- **Product Experience, Design and Brand OS** (`product_experience_design_brand_os`): owner `product-face`, status `active`. Own UX, information architecture, brand/identity, design system, component proof, accessibility and visual regression for product surfaces.
- **Work Unit and Execution Dispatch OS** (`work_unit_execution_dispatch_os`): owner `decomposition-planner`, status `active`. Own vertical work units, dispatch readiness, Hermes materialization plans, worker packets and execution ordering.
- **Authority and Autonomy OS** (`authority_autonomy_os`): owner `factory-orchestrator`, status `active`. Decide when the factory proceeds, repairs, asks the operator, blocks or escalates without turning speed into unsafe YOLO.
- **Hermes Worker Runtime OS** (`hermes_worker_runtime_os`): owner `factory-orchestrator`, status `blocked_pending_runtime_proof`. Own live worker operability: profile readiness, Hermes binding freshness, dispatch, no-idle, worker results and reconciliation.
- **Evidence and Receipt OS** (`evidence_receipt_os`): owner `evidence-reconciler`, status `active`. Own proof tiers, evidence freshness, artifact readback, Receipt Five reconciliation and product-specific proof bundles.
- **Capability Pack and Provider OS** (`capability_provider_os`): owner `factory-orchestrator`, status `active`. Own domain detection, capability pack activation, provider readiness, specialist acquisition and fail-closed pack execution.
- **Agent and Profile Authority OS** (`agent_profile_authority_os`): owner `factory-orchestrator`, status `active`. Own worker identity, permissions, profile linting, binding readiness and the rule that agents execute contracts instead of deciding the line.
- **Security OS** (`security_os`): owner `security-orchestrator`, status `active`. Own threat modeling, secrets, supply chain, privacy, runtime hardening, specialist security routing and risk evidence.
- **Quality and Verification OS** (`quality_verification_os`): owner `qa-verification-worker`, status `active`. Own tests, QA plans, repair loops, visual verification, accessibility, product quality and independent evidence before done.
- **Operator Experience OS** (`operator_experience_os`): owner `overkill-factory-gerente`, status `active`. Make one manager interface enough for Telegram-first operation: start, status, decisions, changes, briefings and proof.
- **Release and Operations OS** (`release_operations_os`): owner `release-ops-worker`, status `active`. Own production readiness, release decision, rollback, monitoring, incident support and human R4 authority.
- **Velocity, Cost and Throughput OS** (`velocity_cost_throughput_os`): owner `factory-orchestrator`, status `active`. Govern throughput, parallel lanes, retry budgets, token and time budgets, batching, dedupe and status cadence.
- **Factory Learning OS** (`factory_learning_os`): owner `skill-eval-distiller`, status `hardened_existing`. Turn learnback, Hermes /learn drafts and repeated findings into inactive, reviewable, testable factory improvements.

These entries are not marketing categories. They name ownership, contracts, required proof, and failure boundaries.

## Method engines

Method engines bind a route to proof. A method family cannot authorize execution by itself. The selected engine must produce the right artifacts and gates for the work.

- `spec_first_sdd` — Spec-First SDD Engine: family `spec_first`; used by product_creation, feature_delivery, critical_integration, migration_execution.
- `test_first_tdd` — Test-First TDD Engine: family `test_first`; used by feature_delivery, bug_repair, critical_integration, migration_execution.
- `behavior_first_bdd` — Behavior-First BDD Engine: family `behavior_first`; used by product_creation, feature_delivery, ux_product_experience.
- `discovery_research` — Discovery and Research Engine: family `discovery_first`; used by product_creation, research_validation, brownfield_discovery.
- `security_first_threat_model` — Security-First Threat Model Engine: family `security_first`; used by security_remediation, release_promotion, critical_integration, agent_quality_change.
- `design_first_product_experience` — Design-First Product Experience Engine: family `design_first`; used by ux_product_experience, product_creation, feature_delivery.
- `legacy_diagnosis` — Legacy Diagnosis Engine: family `legacy_diagnosis`; used by brownfield_discovery, migration_execution, bug_repair.
- `incident_first` — Incident-First Engine: family `incident_first`; used by incident_response, bug_repair, security_remediation.
