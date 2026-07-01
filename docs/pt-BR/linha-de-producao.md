# Linha de produção

Documento operacional da Overkill Factory. Objetivo: mostrar o que existe, como a fábrica escolhe rota/método/capacidade e o que cada fase F0-F27 recebe, produz, bloqueia e entrega ao Hermes.

Fontes públicas usadas aqui: `docs/factory-workflow.catalog.json`, `factory/templates/factory-route-registry.json`, `factory/templates/method-engine-registry.json` e `factory/agents/capability-packs.public.json`.

## Fluxo resumido

```text
F0 fonte selada -> F1 entrada -> F2 ledger -> F3 resolução -> F4 outcome -> F5 Product SOT -> F6 rota -> F7 método -> F8 capacidade -> F9 autoridade -> F10 segurança -> F11 planos -> F12 readiness -> F13 ready gate -> F15 execução -> F16 resultados -> F17 verificação -> F18 revisão -> F20 fechamento -> F21 recibo -> F22 auditoria -> F23 produção -> F24 release/bloqueio -> F25 suporte -> F26 learnback -> F27 maturidade
```

## Como a decisão interna funciona

- F6 escolhe rota comparando pedido entendido com `request_types`, `signal_types` e `scope_intents` do registry de rotas. Saída: `route_class` + `selected_method_family`.
- F7 escolhe/monta método. O método precisa virar `method_contract` com artefatos, gates, workers e prova. Nome de método sem contrato não libera F11/F13.
- F8 escolhe capacidade. Superfícies do trabalho são comparadas com packs. `core_ready` pode seguir com workers existentes; `pack_template` precisa ativação; `blocked_until_installed` bloqueia.
- Hermes recebe o estado vivo: card, status, dependência, worker, comentário, anexo, resultado, revisão e transição. No Hermes, o avanço aparece como mudança de estado ligada a card e evidência. Arquivo local não substitui estado vivo.

Termos humanos usados no fluxo: Pedido aparece em F0/F1; Entendimento aparece em F2/F3; Decisão aparece em F9/F24; Recibo aparece em F21. A fábrica não simula autoridade humana: quando uma fase exige decisão, ela prepara contexto, opções, risco, consequência e próximo estado, mas aguarda registro humano.

Matriz pública de segurança usada por perfis: networking, linux-systems, web-security, ethical-hacking, security-tools, cloud-security, detection-monitoring, cryptography, security-operations, future-security, supply-chain, onchain-solana-quasar.

## Rotas existentes

| Rota | Entra quando | Método escolhido | Artefatos mínimos | Gates | Workers |
|---|---|---|---|---|---|
| `product_creation` | request=product_new; signal=product_paper, prd_or_architecture, mixed; scope=full_product | `spec_first` | `source_ledger`, `operator_understanding_confirmation`, `outcome_contract`, `product_sot`, `full_product_sot_scope_coverage`, `+4` | `Source Gate`, `Product SOT Gate`, `Ready Gate` | `factory-orchestrator`, `source-ledger-worker`, `product-sot-planner` |
| `feature_delivery` | request=feature, slice; signal=feature_idea, customer_feedback, mixed; scope=child_slice | `behavior_first` | `source_ledger`, `outcome_contract`, `method_contract`, `spec_graph`, `qa_plan` | `Source Gate`, `Method Gate`, `Ready Gate` | `factory-orchestrator`, `decomposition-planner`, `qa-verification-worker` |
| `bug_repair` | request=bug; signal=bug_report, monitoring_alert, customer_feedback; scope=bug | `test_first` | `source_ledger`, `bug_reproduction`, `diagnosis`, `regression_check`, `receipt_five` | `Reproduction Gate`, `Regression Gate`, `Receipt Gate` | `qa-verification-worker`, `test-automation-builder`, `evidence-reconciler` |
| `incident_response` | request=incident; signal=incident, monitoring_alert; scope=incident | `incident_first` | `incident_support_plan`, `severity_model`, `mitigation_plan`, `evidence_record`, `learnback` | `Severity Gate`, `Mitigation Gate`, `Learnback Gate` | `detection-monitoring-worker`, `release-ops-worker`, `evidence-reconciler` |
| `brownfield_discovery` | request=migration, refactor, integration; signal=existing_repository, refactor_request, integration_request, migration_request; scope=migration, integration | `legacy_diagnosis` | `source_ledger`, `brownfield_os_plan`, `legacy_system_map`, `baseline`, `regression_plan`, `+1` | `Brownfield Baseline Gate`, `Regression Gate`, `Rollback Gate` | `source-ledger-worker`, `product-architect`, `qa-verification-worker` |
| `release_promotion` | request=release; signal=release_request; scope=release | `spec_first` | `production_readiness_plan`, `promotion_ladder`, `rollback_path`, `monitoring_signals` | `Production Readiness Gate`, `Rollback Gate`, `Release Gate` | `release-ops-worker`, `detection-monitoring-worker`, `evidence-reconciler` |
| `research_validation` | request=feature, product_new, security, ux_ui, data_analytics, agent_skill; signal=research_request, external_research_signal, dependency_or_runtime_change, mixed; scope=child_slice, full_product | `research_first` | `specialist_research_plan`, `specialist_decision_packet`, `sdlc_feedback_loop` | `Source Quality Gate`, `Specialist Decision Gate`, `SOT Impact Gate` | `source-ledger-worker`, `product-architect`, `factory-orchestrator` |
| `docs_onboarding` | request=doc; signal=documentation_request; scope=doc | `docs_first` | `user_docs_onboarding_plan`, `reader_success_path`, `docs_verification` | `Docs Utility Gate`, `First Run Gate` | `docs-os-worker`, `qa-verification-worker` |
| `security_remediation` | request=security; signal=security_review_request, dependency_or_runtime_change; scope=child_slice | `security_first` | `security_architecture_plan`, `security_scan_packet`, `review_result` | `Security Architecture Gate`, `Security Review Gate` | `security-orchestrator`, `appsec-owasp-specialist`, `qa-verification-worker` |
| `critical_integration` | request=integration; signal=integration_request, dependency_or_runtime_change; scope=integration | `spec_first` | `integration_contract`, `dependency_gate`, `contract_tests`, `fallback_plan` | `Dependency Gate`, `Contract Test Gate`, `Fallback Gate` | `product-architect`, `backend-api-builder`, `qa-verification-worker` |
| `migration_execution` | request=migration; signal=migration_request, existing_repository; scope=migration | `legacy_diagnosis` | `brownfield_os_plan`, `legacy_system_map`, `migration_plan`, `regression_plan`, `rollback_plan` | `Migration Plan Gate`, `Regression Gate`, `Rollback Gate` | `product-architect`, `data-persistence-builder`, `qa-verification-worker` |
| `ux_product_experience` | request=ux_ui, product_new, feature; signal=ux_ui_request, feature_idea, product_paper; scope=child_slice, full_product | `design_first` | `product_experience_plan`, `product_face_packet`, `project_design_system`, `professional_design_process`, `product_face_result` | `Product Experience Gate`, `Product Face Gate`, `Independent Design Review Gate` | `product-face`, `frontend-builder`, `qa-verification-worker` |
| `analytics_data` | request=data_analytics, product_new, feature; signal=analytics_request, customer_feedback, prd_or_architecture; scope=child_slice, full_product | `analytics_first` | `data_metrics_plan`, `event_contract`, `dashboard_health_proof`, `privacy_limits` | `Data Contract Gate`, `Privacy Gate`, `Metrics Proof Gate` | `detection-monitoring-worker`, `data-persistence-builder`, `qa-verification-worker` |
| `agent_quality_change` | request=agent_skill; signal=agent_skill_or_model_change, dependency_or_runtime_change; scope=child_slice | `agent_eval_first` | `agent_eval_plan`, `reasoning_policy`, `worker_profile_readiness`, `learnback` | `Agent Eval Gate`, `Worker Profile Readiness Gate`, `Learnback Gate` | `skill-eval-distiller`, `agent-runtime-builder`, `qa-verification-worker` |

**Uso prático:** rota define pacote mínimo. Exemplo: `bug_repair` exige reprodução/regressão/recibo; `release_promotion` exige readiness/rollback/monitoramento; `docs_onboarding` exige plano de docs, caminho de sucesso do leitor e verificação de primeira execução.

## Métodos existentes

| Método | Família | Rotas | Artefatos que cria/exige | Gates | Prova que precisa aparecer | Não aceita |
|---|---|---|---|---|---|---|
| `spec_first_sdd` | `spec_first` | `product_creation`, `feature_delivery`, `critical_integration`, `migration_execution` | `method_contract`, `spec_graph`, `product_creation_plan`, `work_unit_contract` | `Ready Gate`, `Review Gate`, `Done Gate` | spec artifacts exist; tasks trace to Product SOT; Receipt Five cites spec evidence | method label without spec artifact; implementation before Product Creation Plan |
| `test_first_tdd` | `test_first` | `feature_delivery`, `bug_repair`, `critical_integration`, `migration_execution` | `test_plan`, `regression_tests`, `verification_commands` | `Ready Gate`, `Review Gate`, `Done Gate` | failing or target test defined before implementation; tests pass after implementation; Receipt Five cites commands | test-first claimed without test artifact; manual check as only regression proof |
| `behavior_first_bdd` | `behavior_first` | `product_creation`, `feature_delivery`, `ux_product_experience` | `scenario_matrix`, `acceptance_examples`, `operator_briefing_package` | `Ready Gate`, `Review Gate`, `Done Gate` | examples map to Product SOT; scenarios checked by QA or Product Face; Receipt Five cites scenario evidence | acceptance examples invented after execution; operator chat used as scenario proof |
| `discovery_research` | `discovery_first` | `product_creation`, `research_validation`, `brownfield_discovery` | `source_resolution_packet`, `product_source_ledger`, `specialist_research_plan`, `operator_understanding_confirmation` | `Source Gate`, `Research Gate`, `Product SOT Gate` | source claims classified; conflicts resolved or blocked; operator understanding confirmed | raw paper becomes Product SOT; repo supplied but not studied |
| `security_first_threat_model` | `security_first` | `security_remediation`, `release_promotion`, `critical_integration`, `agent_quality_change` | `security_architecture_plan`, `threat_model`, `secret_delivery_policy`, `supply_chain_result` | `Security Gate`, `Review Gate`, `Human R4 Gate` | security architecture exists before material implementation; scanner evidence attached; release risk owner recorded | security review replaces security architecture; placeholder secret delivery passes production |
| `design_first_product_experience` | `design_first` | `ux_product_experience`, `product_creation`, `feature_delivery` | `professional_design_process`, `project_design_system`, `product_experience_plan`, `product_face_packet` | `Product Experience Gate`, `Product Face Gate`, `Review Gate` | DESIGN.md or design-system contract exists; Product Face result checks states; screenshots and accessibility evidence attached | visible product passes without screenshots; Product Face Packet treated as proof |
| `legacy_diagnosis` | `legacy_diagnosis` | `brownfield_discovery`, `migration_execution`, `bug_repair` | `brownfield_os_plan`, `repo_archaeology_notes`, `risk_register` | `Source Gate`, `Migration Gate`, `Review Gate` | existing repo studied before SOT; legacy risk mapped; migration rollback identified | old repo treated as fresh product; legacy assumptions copied into Product SOT without source refs |
| `incident_first` | `incident_first` | `incident_response`, `bug_repair`, `security_remediation` | `incident_support_plan`, `reproduction_evidence`, `rollback_or_mitigation_plan` | `Incident Gate`, `Verification Gate`, `Review Gate` | current impact classified; fix or mitigation verified; post-incident learnback captured | incident fixed only by chat status; mitigation accepted without verification |

Famílias de rota sem engine dedicado neste registry: `agent_eval_first`, `analytics_first`, `docs_first`, `research_first`. Elas não podem virar execução por nome. F7 precisa registrar no `method_contract` qual artefato, gate, worker e prova substitui ou complementa o engine ausente.

## Capacidades existentes

| Capacidade | Estado | Superfícies cobertas | Workers | Evidência mínima | Regra operacional |
|---|---|---|---|---|---|
| `web-saas-core` | `core_ready` | `code`, `implementation`, `frontend`, `browser`, `component`, `screen`, `ux`, `product-face`, `responsive`, `mobile-web`, `+25` | `product-face`, `frontend-builder`, `backend-api-builder`, `data-persistence-builder`, `integration-builder`, `test-automation-builder`, `+4` | `factoryctl gate report`, `worker packets`, `Receipt Five` | Available by default for ordinary web/product software when no specialized template-only surface is present. |
| `cli-tui-product-pack` | `core_ready` | `cli`, `tui`, `terminal`, `console`, `command_line`, `command-line` | `docs-os-worker`, `test-automation-builder`, `qa-verification-worker`, `release-ops-worker` | `install/run smoke`, `help output`, `golden transcript`, `error-state transcript`, `+2` | Available by default for CLI/TUI products after Product Face routes the surface to cli_tui and proof coverage is required through the delivery quality profile. |
| `cloud-native-core` | `core_ready` | `infra`, `devops`, `deploy`, `ci`, `cd`, `cicd`, `runtime`, `environment`, `workflow`, `cloud`, `+11` | `infra-devops-builder`, `cloud-infra-security-specialist`, `supply-chain-gate`, `release-ops-worker`, `detection-monitoring-worker`, `remote-proof-runner` | `runtime contract`, `rollback proof`, `monitoring proof` | Available by default for non-secret cloud/runtime wiring; production authority still requires human and release gates. |
| `agent-runtime-core` | `core_ready` | `agent`, `agents`, `agent design`, `llm`, `prompt`, `memory`, `tools`, `mcp`, `hermes`, `factory`, `+4` | `agent-runtime-builder`, `agentic-ai-security-specialist`, `memory-steward`, `skill-eval-distiller`, `qa-verification-worker`, `independent-reviewer` | `agent eval plan`, `permission class`, `security handoff`, `profile/binding refs` | Available by default after agent_eval_plan, permission class and reviewer separation exist. |
| `solana-ai-kit-core` | `core_ready` | `solana`, `solana-quasar`, `quasar`, `anchor`, `pinocchio`, `onchain`, `program`, `instruction`, `pda`, `account-pda`, `+29` | `product-sot-planner`, `product-architect`, `decomposition-planner`, `product-face`, `implementation-worker`, `backend-api-builder`, `+10` | `Solana AI Kit usage receipt for each real PASS Solana-domain worker result`, `onchain work package`, `Auditor result`, `signer boundary`, `+1` | Available when Factory routing declares or infers a Solana-domain surface and Solana AI Kit is the pinned domain-brain provider; Factory gates, signer rules and human approvals still override provider guidance. |
| `mobile-app-pack` | `pack_template` | `ios`, `android`, `react-native`, `expo`, `native-mobile`, `mobile-wallet`, `deep-linking`, `app-store`, `play-store` | `frontend-builder`, `product-face`, `qa-verification-worker`, `wallet-transaction-builder` | `mobile architecture packet`, `device/simulator smoke`, `mobile Product Face result` | Block material mobile execution until the pack is activated or explicitly waived with a human gate. |
| `desktop-app-pack` | `pack_template` | `desktop`, `electron`, `tauri`, `macos`, `windows`, `linux-desktop`, `installer`, `auto-update` | `frontend-builder`, `product-face`, `infra-devops-builder`, `qa-verification-worker` | `desktop runtime decision`, `packaging proof`, `desktop QA proof` | Block desktop execution until the pack is activated for the selected runtime. |
| `game-product-pack` | `pack_template` | `game`, `game-like`, `2d`, `3d`, `threejs`, `phaser`, `unity`, `unreal`, `gameplay`, `asset-pipeline`, `+2` | `product-face`, `frontend-builder`, `qa-verification-worker`, `test-automation-builder` | `game design packet`, `runtime choice`, `playable smoke`, `performance budget` | Block game execution until the game pack is activated for 2D, 3D, web, mobile or onchain game scope. |
| `ai-ml-product-pack` | `pack_template` | `ai`, `ml`, `model`, `rag`, `embedding`, `embeddings`, `vector-search`, `fine-tuning`, `classifier`, `inference`, `+2` | `agent-runtime-builder`, `agentic-ai-security-specialist`, `data-persistence-builder`, `qa-verification-worker`, `skill-eval-distiller` | `model contract`, `eval plan`, `data policy`, `safety review` | Block AI/ML execution until model/data/eval contracts are activated. |
| `fintech-payments-pack` | `pack_template` | `payment`, `payments`, `billing`, `subscription`, `ledger`, `reconciliation`, `fintech`, `fraud`, `kyc`, `aml`, `+1` | `backend-api-builder`, `data-persistence-builder`, `appsec-owasp-specialist`, `crypto-key-management-specialist`, `codex-security`, `human-gate-clerk` | `ledger model`, `risk matrix`, `security scan`, `human gate` | Block fintech/payment execution until the pack is activated and human/security gates exist. |
| `regulated-domain-pack` | `pack_template` | `legal`, `medical`, `healthcare`, `insurance`, `education`, `compliance`, `privacy-regulated`, `regulated` | `product-sot-planner`, `product-architect`, `codex-security`, `human-gate-clerk`, `docs-os-worker` | `domain risk packet`, `compliance owner`, `human gate`, `scope boundaries` | Block regulated-domain execution until a domain compliance pack is created for the exact jurisdiction and product class. |
| `data-analytics-pack` | `pack_template` | `analytics`, `bi`, `dashboard`, `metrics`, `etl`, `data-pipeline`, `warehouse`, `reporting` | `data-persistence-builder`, `backend-api-builder`, `detection-monitoring-worker`, `docs-os-worker` | `metric definitions`, `data quality checks`, `lineage note`, `dashboard proof` | Block analytics-heavy execution until metric/data contracts are activated. |
| `browser-extension-pack` | `pack_template` | `browser-extension`, `chrome-extension`, `extension`, `manifest-v3`, `content-script` | `frontend-builder`, `agentic-ai-security-specialist`, `product-face`, `qa-verification-worker` | `permission review`, `browser smoke`, `packaging proof` | Block extension execution until extension-specific security and packaging proof exist. |
| `operator-onboarding-pack` | `core_ready` | `onboarding`, `operator`, `fresh-install`, `walkthrough`, `hermes-install`, `adapter-install` | `docs-os-worker`, `qa-verification-worker`, `factory-orchestrator`, `public-safety-gate` | `fresh install commands`, `quickstart smoke`, `worker packet output under .tmp`, `public safety scan` | Available by default for public onboarding and operator walkthrough work that does not mutate a real Hermes runtime. |
| `public-docs-knowledge-pack` | `core_ready` | `public-docs`, `docs`, `documentation`, `guide`, `manual`, `knowledge`, `example-gallery` | `docs-os-worker`, `public-safety-gate`, `qa-verification-worker`, `skill-eval-distiller` | `document governance validation`, `public safety scan`, `secret safety scan`, `focused doc tests` | Available by default for documentation and knowledge artifacts when generated evidence stays out of the public repo. |
| `operator-artifact-media-pack` | `core_ready` | `pdf`, `video`, `media`, `operator-artifact`, `operator-briefing`, `screen-recording`, `presentation`, `document` | `docs-os-worker`, `product-face`, `qa-verification-worker`, `release-ops-worker` | `operator-readable artifact smoke`, `public/private boundary scan`, `delivery receipt or publication candidate proof` | Available by default for non-secret operator artifacts after source/private refs are sanitized and delivery receipts are recorded. |
| `hardware-iot-pack` | `blocked_until_installed` | `hardware`, `iot`, `firmware`, `robotics`, `device`, `embedded` | `product-architect`, `security-orchestrator`, `human-gate-clerk` | `hardware safety packet`, `device test plan`, `domain expert review` | Always block until a dedicated hardware/IoT pack is installed for the exact product. |

**Estados de capacidade:** `core_ready` = pronto para preparar execução com workers existentes; `pack_template` = domínio conhecido mas falta instalação/worker/eval/revisão; `blocked_until_installed` = bloqueio real até pack dedicado ou waiver humano.

## Fases F0-F27

## F0 — Fonte selada (`Pre-Start / Sealed Source Envelope`)

**O que é:** Preserva o pedido e a fonte antes de qualquer execução da fábrica.

- Entrada: operator intent or external signal exists before factory execution.
- Artefatos: `factory_bridge_source_envelope`, `factory_bridge_start_request`.
- Opcional: `factory_bridge_handoff`.
- Gate: `Start Boundary`.
- Workers: `overkill-factory-gerente`, `factory-orchestrator`.
- Estado no Hermes: `card.factory_bridge_source_envelope_ref`, `card.factory_bridge_start_request_ref`, `run.board_binding`.
- Avança quando: sealed source envelope exists; factory_bridge_start_request exists; board policy is explicit.
- Bloqueia quando: summarize or reinterpret source material in the bridge; create Hermes board/card directly from bridge; start without explicit runtime target policy.
- Pode fazer: seal source envelope; create start request; select new_project or existing_project explicitly.
- Comandos: `factoryctl validate-factory-run`, `factoryctl validate-card`.
- Contratos: `schemas/factory-bridge-source-envelope.schema.json`, `schemas/factory-bridge-start-request.schema.json`, `schemas/factory-run.schema.json`.

## F1 — Entrada (`Intake`)

**O que é:** Registra a entrada, escolhe a interface do operador e cria o primeiro pacote de leitura.

- Entrada: user material or intent exists; primary operator interface is selected.
- Artefatos: `operator_interface_profile`, `factory_start_conversation`, `universal_signal_intake`, `source_refs`, `source_resolution_packet`.
- Opcional: `reference_quality_packet`.
- Gate: `Source Gate`.
- Workers: `factory-orchestrator`.
- Estado no Hermes: `card.operator_interface_profile_ref`, `card.factory_start_conversation_ref`, `card.universal_signal_intake_ref`, `card.source_refs`, `card.source_resolution_packet_ref`.
- Avança quando: operator_interface_profile exists; factory_start_conversation exists; universal_signal_intake exists; source_refs is non-empty; source_resolution_packet exists.
- Bloqueia quando: route implementation before source resolution; create Product SOT from raw input; require the operator to poll for status.
- Pode fazer: select operator interface; hold conversational start; classify intake; create universal signal intake; create source resolution packet.
- Comandos: `factoryctl operator-interface`, `factoryctl start-conversation`, `factoryctl validate-signal-intake`, `factoryctl source-resolution`, `factoryctl validate-card`.
- Contratos: `schemas/operator-interface-profile.schema.json`, `schemas/factory-start-conversation.schema.json`, `schemas/universal-signal-intake.schema.json`, `schemas/source-resolution-packet.schema.json`.

## F2 — Ledger de fonte (`Source Ledger`)

**O que é:** Separa fatos, afirmações, lacunas e conflitos em um registro rastreável.

- Entrada: intake classified.
- Artefatos: `source_refs`, `product_source_ledger`, `operator_understanding_confirmation`.
- Opcional: `reference_source_registry`.
- Gate: `Source Gate`.
- Workers: `source-ledger-worker`.
- Estado no Hermes: `card.source_refs`, `card.product_source_ledger_ref`, `card.operator_understanding_confirmation_ref`.
- Avança quando: critical claims point to source refs; product source ledger exists; operator understanding confirmation is confirmed when Product SOT is required.
- Bloqueia quando: ask user to reconcile internal source bookkeeping; create outcome contract or Product SOT before understanding is confirmed.
- Pode fazer: record claims; materialize product source ledger; mark gaps and conflicts; ask concise operator understanding confirmation.
- Comandos: `factoryctl source-ledger`, `factoryctl understanding-confirmation`, `factoryctl validate-source-ledger`, `factoryctl validate-understanding-confirmation`, `factoryctl gate-report`.
- Contratos: `schemas/reference-source-registry.schema.json`, `schemas/product-source-ledger.schema.json`, `schemas/operator-understanding-confirmation.schema.json`.

## F3 — Resolução de fonte (`Source Resolution`)

**O que é:** Resolve lacunas ou transforma o que falta em bloqueio/decisão limitada.

- Entrada: source ledger exists.
- Artefatos: `discovery_brief`.
- Opcional: `specialist_research_plan`.
- Gate: `Discovery Gate`.
- Workers: `source-ledger-worker`, `product-sot-planner`.
- Estado no Hermes: `card.discovery_brief`.
- Avança quando: open gaps are resolved, blocked or owner-assigned.
- Bloqueia quando: turn unresolved gaps into execution scope.
- Pode fazer: resolve conflicts; raise bounded human questions.
- Comandos: `factoryctl help-next`.
- Contratos: `schemas/discovery-brief.schema.json`.

## F4 — Resultado do produto (`Product Outcome And Discovery`)

**O que é:** Transforma entendimento confirmado em outcome antes do Product SOT.

- Entrada: material outcome is known; operator understanding is confirmed when Product SOT is required.
- Artefatos: `operator_understanding_confirmation`, `operator_briefing_package`, `outcome_contract`, `discovery_brief`.
- Opcional: `reference_quality_packet`.
- Gate: `Outcome Gate`, `Discovery Gate`.
- Workers: `product-sot-planner`.
- Estado no Hermes: `card.outcome_contract`, `card.discovery_brief`.
- Avança quando: operator understanding confirmation exists when needed; operator briefing package exists for decision artifacts; outcome, user, problem and success signals exist.
- Bloqueia quando: treat outcome candidate as approved Product SOT; draft Product SOT before operator understanding confirmation.
- Pode fazer: draft Product SOT candidate.
- Comandos: `factoryctl understanding-confirmation`, `factoryctl briefing-package`, `factoryctl outcome-contract`, `factoryctl validate-outcome-contract`, `factoryctl validate-card`.
- Contratos: `schemas/operator-understanding-confirmation.schema.json`, `schemas/operator-briefing-package.schema.json`, `schemas/outcome-contract.schema.json`, `schemas/discovery-brief.schema.json`.

## F5 — Verdade do produto (`Product SOT`)

**O que é:** Cria ou atualiza o Product SOT, cobertura de escopo e lock de fase.

- Entrada: outcome and discovery are resolved enough; operator understanding is confirmed when Product SOT is required.
- Artefatos: `product_sot`, `operator_briefing_package`, `full_product_sot_scope_coverage`, `factory_phase_lock`.
- Opcional: `user_facing_autonomy_contract`.
- Gate: `Product SOT Gate`.
- Workers: `product-sot-planner`.
- Estado no Hermes: `card.product_sot`, `card.operator_briefing_package_ref`, `card.full_product_sot_scope_coverage`, `card.factory_phase_lock`.
- Avança quando: product_sot exists and scope is explicit; operator briefing package includes markdown and PDF when a decision is needed; factory_phase_lock.owner_surface_first.product_sot_review_packet_delivered is true before downstream phases; product_sot.handoff.next_artifact points to full_product_sot_scope_coverage.
- Bloqueia quando: execute from paper instead of Product SOT; ask operator to approve Product SOT from a short chat summary only; start architecture, repo cleanup, human gate or worker packet while Product SOT owner package is missing.
- Pode fazer: create or update Product SOT; create Product SOT briefing package; create full Product SOT scope coverage; set factory_phase_lock active_frontier=product_sot until material is delivered; request bounded scope approval only after material is delivered.
- Comandos: `factoryctl product-sot`, `factoryctl briefing-package`, `factoryctl validate-product-sot`, `factoryctl full-scope-coverage`, `factoryctl validate-full-scope-coverage`, `factoryctl help-next`.
- Contratos: `schemas/product-sot.schema.json`, `schemas/operator-briefing-package.schema.json`, `schemas/full-product-sot-scope-coverage.schema.json`, `schemas/factory-phase-lock.schema.json`, `schemas/user-facing-autonomy-contract.schema.json`.

## F6 — Roteador de método (`Agentic Method Router`)

**O que é:** Escolhe a rota e a família de método a partir do Product SOT e do registry.

- Entrada: owner-readable Product SOT review packet exists; Product SOT candidate exists; full Product SOT scope coverage exists.
- Artefatos: `factory_phase_lock`, `method_contract`.
- Opcional: `specialist_decision_packet`.
- Gate: `Method Gate`.
- Workers: `factory-orchestrator`.
- Estado no Hermes: `card.method_contract`.
- Avança quando: selected method, gates, workers and evidence are recorded; factory_phase_lock can advance only after method_contract is materialized.
- Bloqueia quando: ask user to choose internal method machinery; start architecture or repo cleanup before Method Contract.
- Pode fazer: select route and required methods; keep architecture and worker packets frozen until Method Contract is materialized.
- Comandos: `factoryctl method-contract`, `factoryctl validate-method-contract`, `factoryctl gate-report`.
- Contratos: `schemas/factory-phase-lock.schema.json`, `schemas/method-contract.schema.json`.

## F7 — Contrato de método (`Method Contract`)

**O que é:** Materializa método, gates, workers, artefatos e provas antes de planejar execução.

- Entrada: method route chosen; owner-readable Product SOT review material exists.
- Artefatos: `factory_phase_lock`, `method_contract`.
- Opcional: `parallel_lane_contracts`.
- Gate: `Method Gate`.
- Workers: `factory-orchestrator`.
- Estado no Hermes: `card.method_contract`.
- Avança quando: required artifacts and workers are named.
- Bloqueia quando: start implementation with undocumented process choices; materialize future-phase cards while active frontier is still product_sot or method_contract.
- Pode fazer: record required plans, gates and workers.
- Comandos: `factoryctl validate-card`.
- Contratos: `schemas/factory-phase-lock.schema.json`, `schemas/method-contract.schema.json`.

## F8 — Capacidade e superfície (`Pack And Product Experience Selection`)

**O que é:** Escolhe capability packs, superfície de produto, design system e perfil de evidência.

- Entrada: method contract exists.
- Artefatos: `capability_pack_contract`, `product_experience_plan`, `product_face_packet`, `project_design_system`, `professional_design_process`, `surface_evidence_profile`, `product_delivery_quality_profile`.
- Opcional: `product_pack`, `surface_pack`, `reference_quality_waiver`.
- Gate: `Pack Gate`, `Product Experience Gate`, `Surface Pack Gate`.
- Workers: `product-face`, `factory-orchestrator`.
- Estado no Hermes: `card.product_experience_plan`, `card.product_face_packet`, `card.project_design_system`, `card.professional_design_process`, `card.product_delivery_quality_profile_ref`.
- Avança quando: required surfaces are covered or blocked; product_experience_plan exists and names surface_pack; product_face_packet exists and names required states and proof; project_design_system exists and exports an AI-readable DESIGN.md contract; surface_evidence_profile or surface_evidence_profiles are declared; product_delivery_quality_profile_ref or product_delivery_quality_profile is declared; professional_design_process exists before product-facing implementation.
- Bloqueia quando: activate a pack without proof or coverage; start product-facing implementation before surface state coverage; treat generic UI proof as Product Experience proof; move to implementation with unnamed surface pack or proof profile.
- Pode fazer: match capability packs; mark missing capabilities; create Product Experience Plan; create Product Face Packet; create Project DESIGN.md contract; select surface evidence profile.
- Comandos: `factoryctl help-next`, `factoryctl gate-report`, `factoryctl validate-card`.
- Contratos: `schemas/capability-pack-contract.schema.json`, `schemas/product-experience-plan.schema.json`, `schemas/product-face-packet.schema.json`, `schemas/project-design-system.schema.json`, `schemas/professional-design-process.schema.json`, `schemas/product-delivery-quality-profile.schema.json`.

## F9 — Autoridade e risco (`Risk And Authority Gates`)

**O que é:** Registra acesso, orçamento e decisões humanas quando há risco/autoridade real.

- Entrada: risk tier and surfaces are known; factory_phase_lock permits authority review for the current frontier.
- Artefatos: `access_capability`, `budget_contract`.
- Opcional: `privacy_compliance_plan`.
- Gate: `Access Gate`, `Budget Gate`, `Human Gate when required`.
- Workers: `human-gate-clerk`.
- Estado no Hermes: `card.access_capability`, `card.budget_contract`.
- Avança quando: required authority is granted, blocked or not needed.
- Bloqueia quando: infer approval from silence; ask for planning-only continuation approval; ask for architecture or repo cleanup approval while downstream is frozen.
- Pode fazer: prepare bounded approval requests only for real authority, access, risk, release, funds, secrets or irreversible action.
- Comandos: `factoryctl human-gate-record`.
- Contratos: `schemas/access-capability.schema.json`, `schemas/budget-contract.schema.json`.

## F10 — Arquitetura de segurança (`Security Architecture`)

**O que é:** Cria plano de segurança quando risco material existe antes de build.

- Entrada: material security or privacy risk exists; Product SOT owner-review material exists; Method Contract exists; factory_phase_lock active_frontier is architecture or later.
- Artefatos: `factory_phase_lock`, `security_architecture_plan`.
- Opcional: `privacy_compliance_plan`.
- Gate: `Security Architecture Gate`.
- Workers: `security-orchestrator`.
- Estado no Hermes: `card.security_architecture_plan`.
- Avança quando: controls, threats and reviewers are named.
- Bloqueia quando: build material risk before architecture; start security architecture while Product SOT or Method Contract is still missing.
- Pode fazer: route specialist security planning.
- Comandos: `factoryctl worker-packet`.
- Contratos: `schemas/factory-phase-lock.schema.json`, `schemas/security-architecture-plan.schema.json`.

## F11 — Planos executáveis (`Executable Plans`)

**O que é:** Quebra o produto em planos, specs, work units, checks e rollback.

- Entrada: method and required gates are known.
- Artefatos: `software_development_plan`, `spec_graph`, `loop_plan`, `product_creation_plan`.
- Opcional: `agent_eval_plan`.
- Condicional: `data_metrics_plan`, `user_docs_onboarding_plan`.
- Gate: `Ready Gate`.
- Workers: `decomposition-planner`.
- Estado no Hermes: `card.software_development_plan`, `card.spec_graph`, `card.loop_plan`, `card.product_creation_plan`.
- Avança quando: work units, checks, reviewers, dependencies and rollback are named in Product Creation Plan; Product Creation Plan handoff points to decomposition_coverage_review; declared data, metrics, docs and onboarding plans pass strict schema-backed runtime validation.
- Bloqueia quando: execute before plans, coverage review and stop criteria exist; mark decomposition review as passed from the planner that created the decomposition.
- Pode fazer: create work units, verification plan and Product Creation Plan; handoff Product Creation Plan to Decomposition Coverage Review before readiness.
- Comandos: `factoryctl product-creation-plan`, `factoryctl help-next`.
- Contratos: `schemas/software-development-plan.schema.json`, `schemas/spec-graph.schema.json`, `schemas/loop-plan.schema.json`, `schemas/product-creation-plan.schema.json`, `schemas/data-metrics-plan.schema.json`, `schemas/user-docs-onboarding-plan.schema.json`.

## F12 — Prontidão de autonomia (`Autonomy Readiness`)

**O que é:** Verifica cobertura, acesso, ferramenta, ambiente e limites antes de dispatch.

- Entrada: Product Creation Plan exists; Decomposition Coverage Review is PASS.
- Artefatos: `decomposition_coverage_review`, `product_implementation_readiness`, `autonomy_readiness_packet`.
- Opcional: `access_capability`.
- Gate: `Decomposition Coverage Gate`, `Access & Capability Gate`.
- Workers: `independent-reviewer`, `factory-orchestrator`.
- Estado no Hermes: `card.decomposition_coverage_review`, `card.product_implementation_readiness`, `card.autonomy_readiness_packet`.
- Avança quando: Decomposition Coverage Review exists and is PASS; every planned work-unit owner and reviewer signs the decomposition coverage matrix with evidence; Product Implementation Readiness references the PASS Decomposition Coverage Review; tools, accounts, environment and rollback are ready or blocked.
- Bloqueia quando: start autonomous work with missing review, access or limits; let a single reviewer approve the complete decomposition alone; create Product Implementation Readiness from a failed or missing decomposition coverage review.
- Pode fazer: run multi-operator decomposition coverage review from Product Creation Plan; create Product Implementation Readiness only after Decomposition Coverage Review is PASS; confirm tools, environment, limits and rollback.
- Comandos: `factoryctl decomposition-coverage-review`, `factoryctl product-implementation-readiness`, `factoryctl gate-report`.
- Contratos: `schemas/decomposition-coverage-review.schema.json`, `schemas/product-implementation-readiness.schema.json`, `schemas/autonomy-readiness-packet.schema.json`.

## F13 — Ready Gate (`Ready Gate`)

**O que é:** Decide se worker tasks podem ser criadas ou se o card continua bloqueado.

- Entrada: Product Implementation Readiness exists and references a PASS Decomposition Coverage Review.
- Artefatos: `gate_report`.
- Opcional: `factory_help_next`.
- Gate: `Ready Gate`.
- Workers: `factory-orchestrator`.
- Estado no Hermes: `factoryctl gate-report`.
- Avança quando: gate_predicate_result is PASS; ready worker task materialization is allowed only for reviewed work units.
- Bloqueia quando: dispatch blocked workers.
- Pode fazer: create required worker tasks when gate passes.
- Comandos: `factoryctl gate-report`, `factoryctl help-next`.
- Contratos: `schemas/gate-report.schema.json`.

## F15 — Execução runtime (`Runtime Execution`)

**O que é:** Despacha worker packets para execução real no Hermes/runtime.

- Entrada: Ready Gate passed.
- Artefatos: `worker_packets`.
- Opcional: `parallel_lane_contracts`.
- Gate: `Runtime Gate`.
- Workers: `implementation-worker`, `qa-verification-worker`.
- Estado no Hermes: `.tmp/worker-packets`, `Hermes worker tasks`.
- Avança quando: required worker tasks exist in runtime.
- Bloqueia quando: spawn without route readiness.
- Pode fazer: dispatch required worker packets.
- Comandos: `factoryctl worker-packet`.
- Contratos: `schemas/worker-packet.schema.json`.

## F16 — Resultados de workers (`Worker Results`)

**O que é:** Coleta worker results válidos; pacote gerado não conta como execução.

- Entrada: worker packets were executed.
- Artefatos: `worker_results`.
- Opcional: `evidence_graph`.
- Gate: `Done Gate`.
- Workers: `evidence-reconciler`.
- Estado no Hermes: `worker result artifacts`.
- Avança quando: required workers returned valid records.
- Bloqueia quando: treat packet existence as proof.
- Pode fazer: collect worker result records.
- Comandos: `factoryctl evidence-record`.
- Contratos: `schemas/worker-result.schema.json`.

## F17 — Verificação (`Verification`)

**O que é:** Roda checks nomeados e registra resultado verificável.

- Entrada: implementation or proof exists.
- Artefatos: `verification_plan`, `verification_result`.
- Opcional: `qa_verification_plan`, `product_face_result`.
- Gate: `Verification Gate`.
- Workers: `qa-verification-worker`.
- Estado no Hermes: `card.verification_plan`, `receipt.verification_commands`.
- Avança quando: verification commands and results are attached; product-facing work has product_face_result with usage_evidence_matrix before completion.
- Bloqueia quando: claim done without command evidence.
- Pode fazer: run named checks and record outputs.
- Comandos: `factoryctl validate-completion`.
- Contratos: `schemas/qa-verification-plan.schema.json`.

## F18 — Revisão independente (`Independent Review`)

**O que é:** Faz reviewer separado consumir resultado e evidência antes de aprovar.

- Entrada: verification evidence exists.
- Artefatos: `review_result`.
- Opcional: `reviewer_selection_plan`.
- Gate: `Review Gate`.
- Workers: `independent-reviewer`.
- Estado no Hermes: `worker result artifacts`.
- Avança quando: reviewer is different from executor and result is attached.
- Bloqueia quando: allow executor to self-approve.
- Pode fazer: route independent review.
- Comandos: `factoryctl worker-packet`.
- Contratos: `schemas/reviewer-selection-plan.schema.json`.

## F20 — Resumo de fechamento (`Closure Summary`)

**O que é:** Empacota entrega, bloqueios, risco restante e próxima ação.

- Entrada: workers, checks and review are complete or blocked.
- Artefatos: `closure_summary`.
- Opcional: `handoff_packet`.
- Gate: `Closure Gate`.
- Workers: `handoff-packer`.
- Estado no Hermes: `card.closure_summary`.
- Avança quando: closure result and next step are explicit.
- Bloqueia quando: hide unresolved blockers in prose.
- Pode fazer: summarize delivered work and remaining risk.
- Comandos: `factoryctl status-snapshot`.
- Contratos: `schemas/worker-closure-summary.schema.json`.

## F21 — Receipt Five (`Receipt Five`)

**O que é:** Reconcilia pedido, mudança, evidência, revisão e pendências em recibo final.

- Entrada: closure summary is ready.
- Artefatos: `receipt_five`.
- Opcional: `evidence_graph`.
- Gate: `Done Gate`.
- Workers: `evidence-reconciler`.
- Estado no Hermes: `card.receipt_five`, `receipt artifact`.
- Avança quando: changed, artifacts, commands, review and next action exist; product-facing receipts include Product Face result evidence refs.
- Bloqueia quando: mark done without Receipt Five.
- Pode fazer: reconcile receipt with evidence.
- Comandos: `factoryctl validate-completion`.
- Contratos: `schemas/receipt-five.schema.json`.

## F22 — Auditoria de conclusão (`Completion Audit`)

**O que é:** Compara trabalho prometido e trabalho entregue sem inflar prova local.

- Entrada: receipt exists.
- Artefatos: `completion_audit`.
- Opcional: `factory_completion_audit`.
- Gate: `Completion Audit`.
- Workers: `evidence-reconciler`.
- Estado no Hermes: `card.completion_audit`.
- Avança quando: audit result is PASS, BLOCKED or PENDING with reasons.
- Bloqueia quando: close skipped method or evidence requirements.
- Pode fazer: compare required work with delivered work.
- Comandos: `factoryctl validate-completion`.
- Contratos: `schemas/completion-audit.schema.json`.

## F23 — Operação de produção (`Production Operations`)

**O que é:** Prepara release, rollback, health check, monitoramento e dono.

- Entrada: completion audit allows promotion.
- Artefatos: `production_readiness_plan`.
- Opcional: `incident_support_plan`.
- Gate: `Release Gate`.
- Workers: `release-ops-worker`.
- Estado no Hermes: `card.production_readiness_plan`.
- Avança quando: owner, rollback, health checks and approval rule exist.
- Bloqueia quando: release without owner, rollback or approval.
- Pode fazer: prepare release, rollback and monitoring.
- Comandos: `factoryctl gate-report`.
- Contratos: `schemas/production-readiness-plan.schema.json`.

## F24 — Release ou bloqueio (`Release Or Block`)

**O que é:** Registra decisão de promover ou bloquear com evidência e próximo passo.

- Entrada: production operations plan exists.
- Artefatos: `release_decision`.
- Opcional: `blocker_economics`.
- Gate: `Release Gate`, `Human Gate when required`.
- Workers: `release-ops-worker`, `human-gate-clerk`.
- Estado no Hermes: `release decision artifact`.
- Avança quando: release or block has owner, evidence and next action.
- Bloqueia quando: promote without production-strict evidence.
- Pode fazer: release with authority or block with next action.
- Comandos: `factoryctl help-next`.
- Contratos: `schemas/gate-report.schema.json`.

## F25 — Suporte e monitoramento (`Monitoring Support`)

**O que é:** Define gatilhos de incidente, triagem, escalonamento e suporte.

- Entrada: release or production block is decided.
- Artefatos: `incident_support_plan`.
- Opcional: `monitoring_notes`.
- Gate: `Support Gate`.
- Workers: `release-ops-worker`.
- Estado no Hermes: `card.incident_support_plan`.
- Avança quando: incident triggers, triage and escalation exist.
- Bloqueia quando: ship without support owner when support is material.
- Pode fazer: activate monitoring or support path.
- Comandos: `factoryctl validate-card`.
- Contratos: `schemas/incident-support-plan.schema.json`.

## F26 — Learnback (`Learnback`)

**O que é:** Transforma falha repetida em proposta sem autoativar mudança crítica.

- Entrada: work closed, blocked or released.
- Artefatos: `factory_learning_proposal`.
- Opcional: `execution_learnback_record`.
- Gate: `Learning Gate`.
- Workers: `skill-eval-distiller`.
- Estado no Hermes: `factory/templates/factory-learning-proposal.json`.
- Avança quando: proposal is accepted, rejected or gated.
- Bloqueia quando: auto-activate critical factory changes.
- Pode fazer: convert repeated failure into proposal.
- Comandos: `factoryctl validate-card`.
- Contratos: `schemas/factory-learning-proposal.schema.json`.

## F27 — Auditoria de maturidade (`Factory Maturity Audit`)

**O que é:** Audita lacunas do processo e cria melhoria public-safe quando necessário.

- Entrada: learnback exists or repeated blind spot is detected.
- Artefatos: `factory_maturity_scorecard`.
- Opcional: `owner_issue_intake_report`.
- Gate: `Maturity Gate`.
- Workers: `skill-eval-distiller`.
- Estado no Hermes: `card.factory_maturity_scorecard`.
- Avança quando: blind spots and actions are recorded.
- Bloqueia quando: commit raw study or private evidence.
- Pode fazer: open public-safe improvement issue.
- Comandos: `factoryctl status-snapshot`.
- Contratos: `schemas/factory-maturity-scorecard.schema.json`.

## Bloqueios e retomada

| Bloqueio | Fase comum | O que fica registrado | Como retoma |
|---|---|---|---|
| Fonte faltando | F0-F3 | item ausente, dono, decisão necessária, fonte parcial | anexar fonte, registrar lacuna aceita ou reduzir escopo |
| Product SOT fraco | F4-F5 | campo fraco, cobertura ausente, owner package pendente | atualizar `product_sot`, `full_product_sot_scope_coverage` e lock |
| Método nominal | F6-F7 | rota sem `method_contract`, engine ausente, prova não definida | materializar contrato ou bloquear rota |
| Capacidade ausente | F8-F12 | pack template, worker faltante, permissão/eval/acesso ausente | ativar pack, instalar worker, registrar waiver ou reduzir escopo |
| Autoridade pendente | F9/F24 | decisão, risco, consequência, próximo estado | decisão humana registrada; a fábrica não simula autoridade |
| Execução sem prova | F15-F17 | worker packet existe, mas sem `worker_result` ou verificação | executar worker, anexar evidência, voltar para revisão |
| Revisão inválida | F18 | reviewer igual ao executor ou evidência insuficiente | reviewer independente ou unidade de reparo |
| Fechamento incompleto | F20-F22 | recibo/auditoria sem ligação com pedido, evidência, revisão e pendência | completar Receipt Five ou fechar como parcial/bloqueado |

## Evidência consumida

```text
unidade de trabalho -> card Hermes -> resultado do worker -> revisão -> decisão/fechamento
```

- Evidência disponível: log, diff, screenshot, comando, relatório ou decisão existe, mas ainda não moveu estado.
- Evidência consumida: gate, reviewer ou Receipt Five leu o material e mudou estado: avança, repara, bloqueia, reabre, aceita risco ou fecha.
- Prova local mostra coerência local. Não mostra execução viva no Hermes.
- Worker packet mostra preparação. Não mostra execução.
- Card criado mostra registro. Não mostra conclusão.
