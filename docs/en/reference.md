# Reference

This page collects the short-form facts a reader usually needs after reading the manual. It is intentionally human-sized. The full generated kernel reference is maintained under `factory/legacy-docs/generated/`.

## Route classes

- `product_creation`: used for `product_new` requests. Method family `None`; main gates: Source Gate, Product SOT Gate, Ready Gate.
- `feature_delivery`: used for `feature, slice` requests. Method family `None`; main gates: Source Gate, Method Gate, Ready Gate.
- `bug_repair`: used for `bug` requests. Method family `None`; main gates: Reproduction Gate, Regression Gate, Receipt Gate.
- `incident_response`: used for `incident` requests. Method family `None`; main gates: Severity Gate, Mitigation Gate, Learnback Gate.
- `brownfield_discovery`: used for `migration, refactor, integration` requests. Method family `None`; main gates: Brownfield Baseline Gate, Regression Gate, Rollback Gate.
- `release_promotion`: used for `release` requests. Method family `None`; main gates: Production Readiness Gate, Rollback Gate, Release Gate.
- `research_validation`: used for `feature, product_new, security, ux_ui, data_analytics, agent_skill` requests. Method family `None`; main gates: Source Quality Gate, Specialist Decision Gate, SOT Impact Gate.
- `docs_onboarding`: used for `doc` requests. Method family `None`; main gates: Docs Utility Gate, First Run Gate.
- `security_remediation`: used for `security` requests. Method family `None`; main gates: Security Architecture Gate, Security Review Gate.
- `critical_integration`: used for `integration` requests. Method family `None`; main gates: Dependency Gate, Contract Test Gate, Fallback Gate.
- `migration_execution`: used for `migration` requests. Method family `None`; main gates: Migration Plan Gate, Regression Gate, Rollback Gate.
- `ux_product_experience`: used for `ux_ui, product_new, feature` requests. Method family `None`; main gates: Product Experience Gate, Product Face Gate, Independent Design Review Gate.
- `analytics_data`: used for `data_analytics, product_new, feature` requests. Method family `None`; main gates: Data Contract Gate, Privacy Gate, Metrics Proof Gate.
- `agent_quality_change`: used for `agent_skill` requests. Method family `None`; main gates: Agent Eval Gate, Worker Profile Readiness Gate, Learnback Gate.

## Method engines

- `spec_first_sdd`: None. Used when the route needs `spec_first`. Routes: .
- `test_first_tdd`: None. Used when the route needs `test_first`. Routes: .
- `behavior_first_bdd`: None. Used when the route needs `behavior_first`. Routes: .
- `discovery_research`: None. Used when the route needs `discovery_first`. Routes: .
- `security_first_threat_model`: None. Used when the route needs `security_first`. Routes: .
- `design_first_product_experience`: None. Used when the route needs `design_first`. Routes: .
- `legacy_diagnosis`: None. Used when the route needs `legacy_diagnosis`. Routes: .
- `incident_first`: None. Used when the route needs `incident_first`. Routes: .

## Operating-system areas

- `deterministic_control_plane_os`: deterministic_control_plane_os.
- `product_truth_research_os`: product_truth_research_os.
- `method_os`: method_os.
- `product_architecture_os`: product_architecture_os.
- `product_experience_design_brand_os`: product_experience_design_brand_os.
- `work_unit_execution_dispatch_os`: work_unit_execution_dispatch_os.
- `authority_autonomy_os`: authority_autonomy_os.
- `hermes_worker_runtime_os`: hermes_worker_runtime_os.
- `evidence_receipt_os`: evidence_receipt_os.
- `capability_provider_os`: capability_provider_os.
- `agent_profile_authority_os`: agent_profile_authority_os.
- `security_os`: security_os.
- `quality_verification_os`: quality_verification_os.
- `operator_experience_os`: operator_experience_os.
- `release_operations_os`: release_operations_os.
- `velocity_cost_throughput_os`: velocity_cost_throughput_os.
- `factory_learning_os`: factory_learning_os.

## Important paths

- `README.md`: public English entry.
- `README.pt-BR.md`: public Portuguese entry.
- `docs/en/`: English product manual.
- `docs/pt-BR/`: Portuguese product manual.
- `docs/assets/public-map/`: public visual map assets.
- `docs/factory-workflow.catalog.json`: public workflow catalog.
- `docs/promise-implementation-map.public.json`: public promise-to-implementation map.
- `docs/public-surface.manifest.json`: manifest for public surfaces.
- `factory/scripts/factoryctl.py`: main command surface.
- `factory/schemas/`: JSON schemas for records and contracts.
- `factory/templates/`: examples, registries, and template contracts.
- `factory/agents/`: public worker registry, profiles, bindings, and readiness records.
- `factory/tests/`: regression tests.
- `factory/legacy-docs/`: preserved old docs and generated reference material, not canonical public docs.

## Core terms

Product SOT is the product source of truth. It should say what is being built, what is in scope, what is out of scope, what evidence counts, and what would make the run unacceptable.

Method Contract is the chosen way to handle the work. It binds the route to gates, artifacts, workers, and evidence.

Worker Packet is the bounded instruction given to a worker. It includes task, limits, authority, and expected output.

Gate Report explains whether a task can move, why it is blocked, and which evidence or action would unblock it.

Receipt Five is the completion receipt. It connects request, work, evidence, review, remaining risk, and next state.

Human Gate is a real operator decision. It should come with a readable package, not a vague chat question.

Readback means the factory reads and checks the artifact a worker claims to have produced.

No-idle is the guard that detects silent stalls and pushes the next safe action or fails visibly.

## Public claim boundary

The public repository can prove local kernel coherence. It cannot prove a private product delivery. Live product delivery needs an operator-owned Hermes runtime, live worker results, product-specific evidence, review, and human approval where required.

## Useful commands

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py method-engines
python3 scripts/factoryctl.py operating-systems
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
```
