# Referência

Esta página reúne os fatos curtos usados pelo manual.

## Comandos principais

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

## Paths do repositório

- `docs/en/` — documentação canônica em inglês.
- `docs/pt-BR/` — documentação canônica em português.
- `docs/factory-workflow.catalog.json` — catálogo público de workflow consumido pelo compilador.
- `docs/promise-implementation-map.public.json` — mapa público de promessa para implementação.
- `docs/public-surface.manifest.json` — manifesto da superfície pública.
- `factory/scripts/factoryctl.py` — helper público de controle.
- `factory/schemas/` — schemas de contratos.
- `factory/templates/` — templates e registries de contratos.
- `factory/agents/` — registries públicos de workers, profiles e bindings.
- `factory/tests/` — suíte de validação.
- `factory/legacy-docs/` — documentação antiga não canônica.

## Tabela de fases

| Fase | Nome | Gates | Workers |
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

## Classes de rota

- `product_creation`: tipos de pedido product_new; família de método `spec_first`; gates Source Gate, Product SOT Gate, Ready Gate.
- `feature_delivery`: tipos de pedido feature, slice; família de método `behavior_first`; gates Source Gate, Method Gate, Ready Gate.
- `bug_repair`: tipos de pedido bug; família de método `test_first`; gates Reproduction Gate, Regression Gate, Receipt Gate.
- `incident_response`: tipos de pedido incident; família de método `incident_first`; gates Severity Gate, Mitigation Gate, Learnback Gate.
- `brownfield_discovery`: tipos de pedido migration, refactor, integration; família de método `legacy_diagnosis`; gates Brownfield Baseline Gate, Regression Gate, Rollback Gate.
- `release_promotion`: tipos de pedido release; família de método `spec_first`; gates Production Readiness Gate, Rollback Gate, Release Gate.
- `research_validation`: tipos de pedido feature, product_new, security, ux_ui, data_analytics, agent_skill; família de método `research_first`; gates Source Quality Gate, Specialist Decision Gate, SOT Impact Gate.
- `docs_onboarding`: tipos de pedido doc; família de método `docs_first`; gates Docs Utility Gate, First Run Gate.
- `security_remediation`: tipos de pedido security; família de método `security_first`; gates Security Architecture Gate, Security Review Gate.
- `critical_integration`: tipos de pedido integration; família de método `spec_first`; gates Dependency Gate, Contract Test Gate, Fallback Gate.
- `migration_execution`: tipos de pedido migration; família de método `legacy_diagnosis`; gates Migration Plan Gate, Regression Gate, Rollback Gate.
- `ux_product_experience`: tipos de pedido ux_ui, product_new, feature; família de método `design_first`; gates Product Experience Gate, Product Face Gate, Independent Design Review Gate.
- `analytics_data`: tipos de pedido data_analytics, product_new, feature; família de método `analytics_first`; gates Data Contract Gate, Privacy Gate, Metrics Proof Gate.
- `agent_quality_change`: tipos de pedido agent_skill; família de método `agent_eval_first`; gates Agent Eval Gate, Worker Profile Readiness Gate, Learnback Gate.

## Glossário

- **Hermes Kanban**: chão de runtime que controla boards, cards, dispatch, comentários, logs, dependências e transições.
- **Overkill Factory**: método de produção de produto e kernel de contratos em volta do Hermes.
- **Product SOT**: fonte da verdade do produto usada por planejamento e execução downstream.
- **Method Contract**: ligação entre rota, method engine, artefatos, gates, workers e prova.
- **Worker packet**: pedido de execução limitado para um worker especialista.
- **Human gate**: decisão real de operador com artefato, evidência, risco e consequência.
- **Receipt Five**: pacote final de evidência para release ou bloqueio.
- **Readback**: verificação de que artefatos declarados ainda existem e podem ser inspecionados.
- **No-idle**: proteção que detecta runtime parado ou falso progresso.
