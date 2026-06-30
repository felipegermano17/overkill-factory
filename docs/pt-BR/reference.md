# Referência

Esta página reúne os fatos curtos que uma pessoa normalmente precisa depois de ler o manual. Ela é pequena de propósito. A referência completa gerada fica em `factory/legacy-docs/generated/`.

## Classes de rota

- `product_creation`: usado quando o pedido é `product_new`. A família de método é `None` e os portões principais são Source Gate, Product SOT Gate, Ready Gate.
- `feature_delivery`: usado quando o pedido é `feature, slice`. A família de método é `None` e os portões principais são Source Gate, Method Gate, Ready Gate.
- `bug_repair`: usado quando o pedido é `bug`. A família de método é `None` e os portões principais são Reproduction Gate, Regression Gate, Receipt Gate.
- `incident_response`: usado quando o pedido é `incident`. A família de método é `None` e os portões principais são Severity Gate, Mitigation Gate, Learnback Gate.
- `brownfield_discovery`: usado quando o pedido é `migration, refactor, integration`. A família de método é `None` e os portões principais são Brownfield Baseline Gate, Regression Gate, Rollback Gate.
- `release_promotion`: usado quando o pedido é `release`. A família de método é `None` e os portões principais são Production Readiness Gate, Rollback Gate, Release Gate.
- `research_validation`: usado quando o pedido é `feature, product_new, security, ux_ui, data_analytics, agent_skill`. A família de método é `None` e os portões principais são Source Quality Gate, Specialist Decision Gate, SOT Impact Gate.
- `docs_onboarding`: usado quando o pedido é `doc`. A família de método é `None` e os portões principais são Docs Utility Gate, First Run Gate.
- `security_remediation`: usado quando o pedido é `security`. A família de método é `None` e os portões principais são Security Architecture Gate, Security Review Gate.
- `critical_integration`: usado quando o pedido é `integration`. A família de método é `None` e os portões principais são Dependency Gate, Contract Test Gate, Fallback Gate.
- `migration_execution`: usado quando o pedido é `migration`. A família de método é `None` e os portões principais são Migration Plan Gate, Regression Gate, Rollback Gate.
- `ux_product_experience`: usado quando o pedido é `ux_ui, product_new, feature`. A família de método é `None` e os portões principais são Product Experience Gate, Product Face Gate, Independent Design Review Gate.
- `analytics_data`: usado quando o pedido é `data_analytics, product_new, feature`. A família de método é `None` e os portões principais são Data Contract Gate, Privacy Gate, Metrics Proof Gate.
- `agent_quality_change`: usado quando o pedido é `agent_skill`. A família de método é `None` e os portões principais são Agent Eval Gate, Worker Profile Readiness Gate, Learnback Gate.

## Motores de método

- `spec_first_sdd`: None. Entra quando a rota pede `spec_first`. Rotas: .
- `test_first_tdd`: None. Entra quando a rota pede `test_first`. Rotas: .
- `behavior_first_bdd`: None. Entra quando a rota pede `behavior_first`. Rotas: .
- `discovery_research`: None. Entra quando a rota pede `discovery_first`. Rotas: .
- `security_first_threat_model`: None. Entra quando a rota pede `security_first`. Rotas: .
- `design_first_product_experience`: None. Entra quando a rota pede `design_first`. Rotas: .
- `legacy_diagnosis`: None. Entra quando a rota pede `legacy_diagnosis`. Rotas: .
- `incident_first`: None. Entra quando a rota pede `incident_first`. Rotas: .

## Áreas operacionais

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

## Caminhos importantes

- `README.md`: entrada pública em inglês.
- `README.pt-BR.md`: entrada pública em português.
- `docs/en/`: manual do produto em inglês.
- `docs/pt-BR/`: manual do produto em português.
- `docs/assets/public-map/`: assets públicos do mapa visual.
- `docs/factory-workflow.catalog.json`: catálogo público do workflow.
- `docs/promise-implementation-map.public.json`: mapa público de promessa para implementação.
- `docs/public-surface.manifest.json`: manifest das superfícies públicas.
- `factory/scripts/factoryctl.py`: principal superfície de comando.
- `factory/schemas/`: schemas JSON para registros e contratos.
- `factory/templates/`: exemplos, registries e contratos-base.
- `factory/agents/`: registry público de workers, perfis, bindings e readiness records.
- `factory/tests/`: testes de regressão.
- `factory/legacy-docs/`: docs antigas e referência gerada preservadas; não são a documentação pública canônica.

## Termos centrais

Product SOT é a fonte de verdade do produto. Ele deve dizer o que está sendo construído, o que entra no escopo, o que fica fora, que evidência conta e o que tornaria a execução inaceitável.

Method Contract é a forma escolhida para tratar o trabalho. Ele liga a rota a gates, artefatos, workers e evidência.

Worker Packet é a instrução limitada entregue a um worker. Inclui tarefa, limites, autoridade e saída esperada.

Gate Report explica se uma tarefa pode avançar, por que está bloqueada e que evidência ou ação destravaria o caminho.

Receipt Five é o recibo de conclusão. Ele conecta pedido, trabalho, evidência, revisão, risco restante e próximo estado.

Human Gate é uma decisão real do operador. Deve vir com pacote legível, não com pergunta vaga no chat.

Readback quer dizer que a fábrica lê e confere o artefato que o worker disse ter produzido.

No-idle é o guard que detecta parada silenciosa e força o próximo passo seguro ou falha de forma visível.

## Fronteira das claims públicas

O repositório público consegue provar coerência local do kernel. Ele não prova uma entrega privada de produto. Entrega real precisa de runtime Hermes do operador, resultados vivos de workers, evidência específica do produto, revisão e aprovação humana quando necessário.

## Comandos úteis

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
