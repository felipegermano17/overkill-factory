# Reference

This page collects the short-form facts used by the manual.

## Main commands

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py method-engines
python3 scripts/factoryctl.py operating-systems
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
```

## Repository paths

- `docs/en/` — canonical English documentation.
- `docs/pt-BR/` — canonical Portuguese documentation.
- `docs/factory-workflow.catalog.json` — public workflow catalog consumed by the compiler.
- `docs/promise-implementation-map.public.json` — public promise-to-implementation map.
- `docs/public-surface.manifest.json` — public surface manifest.
- `factory/scripts/factoryctl.py` — public control helper.
- `factory/schemas/` — contract schemas.
- `factory/templates/` — contract templates and registries.
- `factory/agents/` — public worker/profile/binding registries.
- `factory/tests/` — validation suite.
- `factory/legacy-docs/` — non-canonical older documentation.

## Phase table

| Phase | Name | Gates | Workers |
| --- | --- | --- | --- |
| F0 | Pre-Start / Sealed Source Envelope | Start Boundary | overkill-factory-gerente, factory-orchestrator |
| F1 | Intake | Source Gate | factory-orchestrator |
| F2 | Source Ledger | Source Gate | source-ledger-worker |
| F3 | Source Resolution | Discovery Gate | source-ledger-worker, product-sot-planner |
| F4 | Product Outcome And Discovery | Outcome Gate, Discovery Gate | product-sot-planner |
| F5 | Product SOT | Product SOT Gate | product-sot-planner |
| F6 | Agentic Method Router | Method Gate | factory-orchestrator |
| F7 | Method Contract | Method Gate | factory-orchestrator |
| F8 | Pack And Product Experience Selection | Pack Gate, Product Experience Gate, Surface Pack Gate | product-face, factory-orchestrator |
| F9 | Risk And Authority Gates | Access Gate, Budget Gate, Human Gate when required | human-gate-clerk |
| F10 | Security Architecture | Security Architecture Gate | security-orchestrator |
| F11 | Executable Plans | Ready Gate | decomposition-planner |
| F12 | Autonomy Readiness | Decomposition Coverage Gate, Access & Capability Gate | independent-reviewer, factory-orchestrator |
| F13 | Ready Gate | Ready Gate | factory-orchestrator |
| F15 | Runtime Execution | Runtime Gate | implementation-worker, qa-verification-worker |
| F16 | Worker Results | Done Gate | evidence-reconciler |
| F17 | Verification | Verification Gate | qa-verification-worker |
| F18 | Independent Review | Review Gate | independent-reviewer |
| F20 | Closure Summary | Closure Gate | handoff-packer |
| F21 | Receipt Five | Done Gate | evidence-reconciler |
| F22 | Completion Audit | Completion Audit | evidence-reconciler |
| F23 | Production Operations | Release Gate | release-ops-worker |
| F24 | Release Or Block | Release Gate, Human Gate when required | release-ops-worker, human-gate-clerk |
| F25 | Monitoring Support | Support Gate | release-ops-worker |
| F26 | Learnback | Learning Gate | skill-eval-distiller |
| F27 | Factory Maturity Audit | Maturity Gate | skill-eval-distiller |

## Route classes

- `product_creation`: request types product_new; method family `spec_first`; gates Source Gate, Product SOT Gate, Ready Gate.
- `feature_delivery`: request types feature, slice; method family `behavior_first`; gates Source Gate, Method Gate, Ready Gate.
- `bug_repair`: request types bug; method family `test_first`; gates Reproduction Gate, Regression Gate, Receipt Gate.
- `incident_response`: request types incident; method family `incident_first`; gates Severity Gate, Mitigation Gate, Learnback Gate.
- `brownfield_discovery`: request types migration, refactor, integration; method family `legacy_diagnosis`; gates Brownfield Baseline Gate, Regression Gate, Rollback Gate.
- `release_promotion`: request types release; method family `spec_first`; gates Production Readiness Gate, Rollback Gate, Release Gate.
- `research_validation`: request types feature, product_new, security, ux_ui, data_analytics, agent_skill; method family `research_first`; gates Source Quality Gate, Specialist Decision Gate, SOT Impact Gate.
- `docs_onboarding`: request types doc; method family `docs_first`; gates Docs Utility Gate, First Run Gate.
- `security_remediation`: request types security; method family `security_first`; gates Security Architecture Gate, Security Review Gate.
- `critical_integration`: request types integration; method family `spec_first`; gates Dependency Gate, Contract Test Gate, Fallback Gate.
- `migration_execution`: request types migration; method family `legacy_diagnosis`; gates Migration Plan Gate, Regression Gate, Rollback Gate.
- `ux_product_experience`: request types ux_ui, product_new, feature; method family `design_first`; gates Product Experience Gate, Product Face Gate, Independent Design Review Gate.
- `analytics_data`: request types data_analytics, product_new, feature; method family `analytics_first`; gates Data Contract Gate, Privacy Gate, Metrics Proof Gate.
- `agent_quality_change`: request types agent_skill; method family `agent_eval_first`; gates Agent Eval Gate, Worker Profile Readiness Gate, Learnback Gate.

## Glossary

- **Hermes Kanban**: the runtime floor that owns boards, cards, dispatch, comments, logs, dependencies, and state transitions.
- **Overkill Factory**: the product-production method and contract kernel that sits around Hermes.
- **Product SOT**: the product source of truth used for downstream planning and execution.
- **Method Contract**: the binding between a route, method engine, artifacts, gates, workers, and proof.
- **Worker packet**: a bounded execution request for a specialist worker.
- **Human gate**: a real operator decision with artifact, evidence, risk, and consequence.
- **Receipt Five**: the final evidence package for release or block.
- **Readback**: verification that claimed artifacts still exist and can be inspected.
- **No-idle**: guardrail that detects stalled or false-progress runtime states.
