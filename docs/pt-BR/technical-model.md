# Modelo Técnico

A Overkill Factory é implementada como pacote Python, CLI, biblioteca de contratos, superfície de adapter Hermes, registry público de workers e site de documentação.

Ela intencionalmente não substitui o Hermes.

## Estrutura do repositório

```text
README.md              entrada pública em inglês
README.pt-BR.md        entrada pública em português
docs/                  documentação canônica e catálogos públicos
factory/               implementação, contratos, testes, exemplos, docs legadas
```

Dentro de `factory/`:

- `scripts/` contém `factoryctl.py` e validadores;
- `schemas/` contém JSON schemas de contratos;
- `templates/` contém templates e registries canônicos;
- `agents/` contém registries públicos de workers, profiles, readiness e bindings;
- `adapters/hermes/` contém integração com fronteiras do runtime Hermes;
- `examples/` e `fixtures/` contêm exemplos públicos e fixtures de validação;
- `tests/` protege comportamento e claims públicas;
- `legacy-docs/` preserva documentação antiga não canônica.

## Números do kernel público

A superfície executável atual inspecionada para esta documentação contém:

- 244 schemas;
- 156 templates JSON;
- 97 testes;
- 40 workers públicos;
- 14 classes de rota;
- 8 method engines;
- 17 áreas de operating system;
- 26 fases compiladas de workflow.

## `factoryctl`

`factoryctl` é o helper público de controle. Ele valida contratos, cria artefatos locais de prova, compila planos de workflow, gera worker packets, checa artefatos JSON públicos e roda caminhos de smoke.

Comandos importantes:

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

`factoryctl` pode provar coerência local de contratos. Ele não substitui prova de runtime Hermes.

## Fronteira de runtime

Hermes controla estado de runtime. Overkill Factory controla método, contratos e checks.

Isso significa:

- um JSON local não é um board real rodando;
- um pacote gerado não é trabalho concluído;
- um worker profile não é resultado de worker;
- um smoke local passando não é release de produção;
- um gate humano não pode ser falsificado por script.

## Registry de operating systems

A fábrica agrupa áreas críticas em entradas de operating system:

- **Deterministic Control Plane OS** (`deterministic_control_plane_os`): dono `factory-orchestrator`, status `active`. Own the reducer-first factory spine: phase graph, commands, events, decision outbox, replay and promotion boundaries.
- **Product Truth and Research OS** (`product_truth_research_os`): dono `source-ledger-worker`, status `active`. Own deep product starts before Product SOT: sources, claims, conflicts, brownfield study, research decisions and operator understanding.
- **Method OS** (`method_os`): dono `factory-orchestrator`, status `active`. Turn method routing into deterministic method engines rather than broad method-family labels.
- **Product Architecture OS** (`product_architecture_os`): dono `product-architect`, status `active`. Own architecture candidates, trust boundaries, integration shape, data boundaries and technical decisions before decomposition.
- **Product Experience, Design and Brand OS** (`product_experience_design_brand_os`): dono `product-face`, status `active`. Own UX, information architecture, brand/identity, design system, component proof, accessibility and visual regression for product surfaces.
- **Work Unit and Execution Dispatch OS** (`work_unit_execution_dispatch_os`): dono `decomposition-planner`, status `active`. Own vertical work units, dispatch readiness, Hermes materialization plans, worker packets and execution ordering.
- **Authority and Autonomy OS** (`authority_autonomy_os`): dono `factory-orchestrator`, status `active`. Decide when the factory proceeds, repairs, asks the operator, blocks or escalates without turning speed into unsafe YOLO.
- **Hermes Worker Runtime OS** (`hermes_worker_runtime_os`): dono `factory-orchestrator`, status `blocked_pending_runtime_proof`. Own live worker operability: profile readiness, Hermes binding freshness, dispatch, no-idle, worker results and reconciliation.
- **Evidence and Receipt OS** (`evidence_receipt_os`): dono `evidence-reconciler`, status `active`. Own proof tiers, evidence freshness, artifact readback, Receipt Five reconciliation and product-specific proof bundles.
- **Capability Pack and Provider OS** (`capability_provider_os`): dono `factory-orchestrator`, status `active`. Own domain detection, capability pack activation, provider readiness, specialist acquisition and fail-closed pack execution.
- **Agent and Profile Authority OS** (`agent_profile_authority_os`): dono `factory-orchestrator`, status `active`. Own worker identity, permissions, profile linting, binding readiness and the rule that agents execute contracts instead of deciding the line.
- **Security OS** (`security_os`): dono `security-orchestrator`, status `active`. Own threat modeling, secrets, supply chain, privacy, runtime hardening, specialist security routing and risk evidence.
- **Quality and Verification OS** (`quality_verification_os`): dono `qa-verification-worker`, status `active`. Own tests, QA plans, repair loops, visual verification, accessibility, product quality and independent evidence before done.
- **Operator Experience OS** (`operator_experience_os`): dono `overkill-factory-gerente`, status `active`. Make one manager interface enough for Telegram-first operation: start, status, decisions, changes, briefings and proof.
- **Release and Operations OS** (`release_operations_os`): dono `release-ops-worker`, status `active`. Own production readiness, release decision, rollback, monitoring, incident support and human R4 authority.
- **Velocity, Cost and Throughput OS** (`velocity_cost_throughput_os`): dono `factory-orchestrator`, status `active`. Govern throughput, parallel lanes, retry budgets, token and time budgets, batching, dedupe and status cadence.
- **Factory Learning OS** (`factory_learning_os`): dono `skill-eval-distiller`, status `hardened_existing`. Turn learnback, Hermes /learn drafts and repeated findings into inactive, reviewable, testable factory improvements.

Essas entradas não são categorias de marketing. Elas declaram dono, contratos, prova exigida e fronteiras de falha.

## Method engines

Method engines ligam uma rota a provas. Uma família de método não autoriza execução sozinha. A engine escolhida precisa produzir artefatos e gates corretos para o trabalho.

- `spec_first_sdd` — Spec-First SDD Engine: família `spec_first`; usado por product_creation, feature_delivery, critical_integration, migration_execution.
- `test_first_tdd` — Test-First TDD Engine: família `test_first`; usado por feature_delivery, bug_repair, critical_integration, migration_execution.
- `behavior_first_bdd` — Behavior-First BDD Engine: família `behavior_first`; usado por product_creation, feature_delivery, ux_product_experience.
- `discovery_research` — Discovery and Research Engine: família `discovery_first`; usado por product_creation, research_validation, brownfield_discovery.
- `security_first_threat_model` — Security-First Threat Model Engine: família `security_first`; usado por security_remediation, release_promotion, critical_integration, agent_quality_change.
- `design_first_product_experience` — Design-First Product Experience Engine: família `design_first`; usado por ux_product_experience, product_creation, feature_delivery.
- `legacy_diagnosis` — Legacy Diagnosis Engine: família `legacy_diagnosis`; usado por brownfield_discovery, migration_execution, bug_repair.
- `incident_first` — Incident-First Engine: família `incident_first`; usado por incident_response, bug_repair, security_remediation.
