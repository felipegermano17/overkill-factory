# Modelo Operacional

Esta página descreve a fábrica operando, não a árvore interna de pastas.

O modelo mental simples é: a fábrica recebe um sinal, protege a verdade, escolhe uma rota segura, cria trabalho limitado, executa pelo Hermes, verifica evidência e libera, bloqueia ou aprende.

## 1. Um sinal entra

Um sinal pode ser paper de produto, bug, ideia de feature, incidente, repositório, pedido de release, pedido de UX, integração, migração, questão de segurança, analytics ou mudança em agente/runtime.

O route registry atual expõe estas classes de rota:

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

A rota importa porque um bug não deve ser tratado como produto greenfield, e um release não deve ser tratado como discovery. O método e os gates mudam conforme a rota.

## 2. Fonte vem antes de interpretação

A fábrica primeiro captura e resolve o material de fonte. Ela não deve transformar um paper longo em resumo raso e chamar isso de verdade.

A sequência esperada é:

- capturar o source envelope;
- classificar o sinal;
- resolver referências de fonte;
- construir um source ledger;
- identificar conflitos ou material faltante;
- confirmar entendimento com o operador quando a verdade de produto importa.

Só depois disso a fábrica pode criar artefatos de definição de produto usados por workers downstream.

## 3. Verdade de produto vira escopo executável

Product SOT é a definição de produto usada como fonte de verdade pela fábrica. Não é um resumo casual. É o artefato ao qual método, arquitetura, planejamento, decomposição, implementação e revisão precisam se conectar.

Uma execução de produto também precisa cobrir o escopo completo do Product SOT. Isso impede que uma primeira fatia vire silenciosamente o produto inteiro.

## 4. Método é escolhido por contrato

O registry de method engines contém:

- `spec_first_sdd` — Spec-First SDD Engine: família `spec_first`; usado por product_creation, feature_delivery, critical_integration, migration_execution.
- `test_first_tdd` — Test-First TDD Engine: família `test_first`; usado por feature_delivery, bug_repair, critical_integration, migration_execution.
- `behavior_first_bdd` — Behavior-First BDD Engine: família `behavior_first`; usado por product_creation, feature_delivery, ux_product_experience.
- `discovery_research` — Discovery and Research Engine: família `discovery_first`; usado por product_creation, research_validation, brownfield_discovery.
- `security_first_threat_model` — Security-First Threat Model Engine: família `security_first`; usado por security_remediation, release_promotion, critical_integration, agent_quality_change.
- `design_first_product_experience` — Design-First Product Experience Engine: família `design_first`; usado por ux_product_experience, product_creation, feature_delivery.
- `legacy_diagnosis` — Legacy Diagnosis Engine: família `legacy_diagnosis`; usado por brownfield_discovery, migration_execution, bug_repair.
- `incident_first` — Incident-First Engine: família `incident_first`; usado por incident_response, bug_repair, security_remediation.

Nome de método não basta. A fábrica precisa ligar a rota escolhida a artefatos, gates, workers e provas. Por exemplo, trabalho test-first precisa de prova de teste. Trabalho design-first precisa de prova de Product Experience. Trabalho security-first precisa de threat modeling e evidência de segurança.

## 5. Planejamento cria execução limitada

Product Creation Plan e work units transformam verdade de produto em pacotes executáveis. Um worker packet deve dizer ao especialista o que fazer, o que não fazer, qual evidência devolver e qual autoridade ele tem.

É aqui que a fábrica evita a falha clássica: "agente, construa tudo". O worker recebe um trabalho limitado, não uma missão vaga.

## 6. Hermes executa o trabalho de runtime

Hermes Kanban continua sendo a fonte de verdade do runtime. Cards, dependências, status de workers, comentários, workspaces e transições vivem ali.

A fábrica pode validar contratos e preparar pacotes, mas a autoridade de execução vem do estado do runtime. Se o runtime diz que um card está bloqueado, a fábrica precisa respeitar isso e reparar o bloqueio ou entregar o gate humano correto.

## 7. Revisão é separada de execução

Um evento `done` de worker não é prova automática. A fábrica espera readback, verificação e revisão independente quando necessário.

Executor e reviewer devem ser identidades separadas em trabalho material. Revisão pode passar, falhar ou criar reparo. Uma revisão que passa mas não reduz o card original ainda é falha de orquestração.

## 8. Gates humanos são explícitos

Gate humano não é desculpa para parar. É um pacote real de decisão. O operador deve receber o artefato, a decisão necessária, os riscos, as evidências e as opções recomendadas.

Bloqueios internos de revisão são responsabilidade da fábrica, salvo quando exigem autoridade explícita do operador.

## 9. Receipt Five fecha o ciclo

Receipt Five é o pacote de evidências de conclusão ou bloqueio. Ele deve responder:

- o que foi pedido;
- o que foi construído ou decidido;
- qual evidência prova;
- o que foi revisado;
- o que continua bloqueado ou arriscado;
- qual é o próximo estado operacional.

Sem esse pacote, `done` não é uma afirmação de nível fábrica.

## 10. Learnback melhora a fábrica

Uma execução finalizada pode revelar métodos melhores, skills faltantes, validadores fracos ou novos padrões de falha. Learnback transforma isso em melhoria revisável, não em mudança silenciosa da fábrica.
