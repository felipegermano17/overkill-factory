# Referencia Tecnica Da Overkill Factory

Esta pagina e a referencia tecnica compacta do kernel publico atual. Ela nao e um segundo manual. Ela responde como a Factory existe neste repositorio, como se conecta ao Hermes, quais contratos e comandos importam e o que a prova publica prova ou nao prova.

## Kernel Publico Atual

O kernel publico neste checkout esta na versao `3.0.2`.

Contagens atuais depois de sincronizar `origin/main`:

- 26 fases compiladas em `docs/factory-workflow.catalog.json`,
- 14 classes de rota em `factory/templates/factory-route-registry.json`,
- 8 motores de metodo em `factory/templates/method-engine-registry.json`,
- 17 areas operacionais em `factory/templates/factory-operating-system-registry.json`,
- 40 workers publicos em `factory/agents/worker-registry.public.json`,
- 17 capability packs em `factory/agents/capability-packs.public.json`,
- 251 schemas JSON em `factory/schemas/`,
- 163 templates JSON em `factory/templates/`,
- 102 arquivos de teste Python em `factory/tests/`.

Esses sao fatos do repositorio, nao claims de entrega de produto. Coerencia local nao e conclusao viva no Hermes.

## Estrutura Do Repositorio

- `README.md`: entrada publica curta em ingles.
- `README.pt-BR.md`: entrada publica curta em portugues.
- `docs/en/factory-manual.md`: manual humano primario.
- `docs/en/technical-reference.md`: referencia tecnica e operacional.
- `docs/pt-BR/`: espelho em portugues.
- `docs/assets/public-map/overkill-factory-map-v1.0.3.html`: mapa visual completo criado com Archify.
- `factory/scripts/`: comandos, validadores, provas e auditorias.
- `factory/schemas/`: schemas JSON dos artefatos oficiais.
- `factory/templates/`: templates JSON e Markdown.
- `factory/agents/`: worker registry, bindings, permissoes e capability packs.
- `factory/adapters/hermes/`: integracao com Hermes.
- `factory/examples/` e `factory/fixtures/`: exemplos publicos e fixtures.
- `factory/tests/`: testes de regressao do kernel publico.

Documentacao vive em `docs/`. Tecnologia vive em `factory/`.

## Kernel Do Repo Versus Runtime Hermes

O repositorio e o kernel formal. Ele guarda contratos, schemas, templates, registries, comandos, validadores, exemplos, fixtures e testes.

Hermes e o runtime. Hermes controla cards vivos, sessoes, execucao de workers, Kanban, anexos, comentarios, processos, gateway e evidencias operacionais.

Essa divisao importa:

- o repo prova que o kernel publico esta coerente,
- Hermes prova o que aconteceu numa execucao viva,
- docs publicas explicam o modelo,
- docs publicas nao provam entrega privada,
- a bridge pode coletar ou encaminhar eventos do operador,
- a bridge nao pode virar a Factory, fechar gates, executar workers ou aprovar decisoes humanas.

Hermes controla estado de runtime. A Factory fornece controle, contratos, gates, validadores, limites de worker e expectativas de evidencia.

## Comandos Principais

Rode comandos a partir de `factory/`:

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Comandos uteis:

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

A superficie de comando existe para tornar o metodo testavel. Sem comandos, a Factory seria filosofia. Com comandos, vira contrato que pode falhar.

## As 26 Fases Compiladas

O workflow compilado e a fonte factual da forma publica das fases:

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

O importante nao e a numeracao. O importante e que cada fase transforme entrada em saida consumivel pela proxima fase.

## Classes De Rota

Rotas respondem: que tipo de trabalho e esse?

Classes atuais:

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

Rota importa porque a prova muda por tipo de trabalho. Bug precisa reproducao e regressao. Release precisa rollback e autoridade. UX precisa screenshot e jornada. Seguranca precisa fronteira de ameaca. Produto novo precisa Product SOT e cobertura de escopo.

## Motores De Metodo

Motores de metodo respondem: como esse tipo de trabalho sera provado?

Motores atuais:

- `spec_first_sdd`
- `test_first_tdd`
- `behavior_first_bdd`
- `discovery_research`
- `security_first_threat_model`
- `design_first_product_experience`
- `legacy_diagnosis`
- `incident_first`

Metodo nao e etiqueta. Ele precisa materializar Method Contract, artefatos, gates, workers, requisitos de prova e atalhos proibidos.

## Areas Operacionais

A Factory tem 17 areas operacionais:

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

Elas nao sao departamentos decorativos. Elas nomeiam as responsabilidades necessarias para impedir improviso agentico.

## Workers

O registry publico define 40 workers publicos, incluindo:

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

Worker nao e personagem. Precisa de registry, limite de autoridade, gatilho, contrato de entrada, escopo de ferramenta, contrato de saida, politica de evidencia, veto conditions e binding Hermes quando vira executavel.

## Cobertura De Dominios De Seguranca

Trabalho de seguranca precisa ser explicito porque seguranca publica nao pode depender de um "security review" generico. Os dominios machine-checkable atuais sao:

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

Esses nomes importam porque workers e validadores usam os dominios para provar que a cobertura de seguranca tem dono, em vez de ficar implicita.

## Capability Packs

Capability pack responde: a Factory tem kit para este dominio?

Packs atuais incluem web/SaaS, CLI/TUI, cloud-native, agent runtime, Solana AI Kit, mobile, desktop, game, AI/ML, fintech/payments, regulated domain, analytics, browser extension, operator onboarding, public docs, media de artefato do operador e hardware/IoT.

Alguns packs sao core. Outros sao templates que precisam ativacao antes de execucao material. Pack template nao e claim de entrega.

## Artefatos Criticos

Os artefatos principais sao:

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

A lista e longa porque producao e real. As docs publicas ficam pequenas porque o usuario nao deveria precisar ler todo schema para entender o sistema.

## Regras De Evidencia

A Factory nao aceita linguagem como prova.

Evidencia pode ser teste, build, lint, typecheck, schema validation, readback de arquivo, screenshot, jornada no browser, saida de CLI, resposta curl, logs, CI, PR, URL deployada, revisao de seguranca, revisao independente, operator delivery receipt, estado Hermes e Receipt Five.

A evidencia precisa ser reconciliada com a claim. Screenshot nao prova backend. Teste unitario nao prova UX. PASS local nao autoriza producao. PASS review-only nao autoriza release.

## Human Gates

Human gates sao exigidos para autoridade real:

- producao,
- mainnet,
- fundos,
- assinatura,
- secrets,
- billing,
- acoes destrutivas,
- arquitetura de alto risco,
- aceitar risco residual,
- publicar material sensivel,
- mudanca estrategica de escopo.

Human gate valido declara decisao, opcoes, consequencias, recomendacao, evidencia, risco, o que a aprovacao autoriza, o que nao autoriza e resposta esperada.

Operator delivery receipt prova que a pergunta chegou ao operador. Um "waiting for owner" escondido no Kanban nao basta.

## Public Safety

GitHub publico e superficie de produto. Nao pode virar lixeira de contexto interno.

Validadores importantes:

```bash
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
```

Docs publicas nao devem vazar paths privados, conversas internas, tokens, screenshots privadas, temporarios, IDs de board privado ou promessas sem suporte.

## Mapa Visual

Mapa visual publico:

[Overkill Factory visual map](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)

Arquivo local:

`docs/assets/public-map/overkill-factory-map-v1.0.3.html`

Ele foi criado com Archify e e explicacao de apoio. O mapa nao e fonte da verdade e nao prova runtime.

## Limite De Prova

`doctor` ou `run minimal` passando significa que o kernel publico esta coerente para rodar checks publicos.

Nao prova:

- produto real entregue,
- workers vivos executaram,
- board Hermes privado esta correto,
- deploy esta saudavel,
- release publico esta completo,
- readiness de mainnet, assinatura, custodia ou movimentacao de fundos,
- humano aprovou.

Prova real de produto exige estado Hermes vivo, card real, worker result, evidencia especifica, readback, revisao independente, Receipt Five e aprovacao humana quando obrigatoria.
