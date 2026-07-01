# Fluxo da fábrica e arquitetura técnica com Hermes

Este é o documento denso. Ele substitui as páginas separadas e conceituais sobre fluxo de pedido, experiência do operador, prova, decisões humanas, workers, status, glossário e fronteira Hermes.

A estrutura anterior ficou mais fácil de navegar, mas ainda rasa demais. Esta página é propositalmente mais útil: explica o que a Factory é tecnicamente, como ela se encaixa no Hermes, o que realmente acontece em cada fase, que estado é escrito, o que workers podem fazer, como evidência é consumida e onde o teatro de progresso é bloqueado.

## A versão curta

A Overkill Factory é o contrato de produção em volta do Hermes. Hermes é o chão vivo do runtime: cards, status, dependências, comentários, anexos, workers, estado do board e transições. A Factory é o contrato determinístico que diz no que um pedido precisa se transformar antes do trabalho começar, o que cada worker recebe, que prova precisa voltar, quando review foi consumido, quando uma decisão humana é legítima e o que precisa existir antes de chamar algo de pronto.

Hermes é a fonte de verdade viva do runtime. A Factory não pode manter um segundo estado escondido. Se Hermes diz que o card está bloqueado, a Factory não pode tratar aquilo secretamente como done. Se a Factory tem um artefato local mas Hermes não tem worker result, a afirmação correta é prova local, não entrega viva.

## O que a Factory é tecnicamente

Tecnicamente, a Factory é uma camada de contrato formada por:

- catálogo de fases compilado: `26 compiled phases` em `docs/factory-workflow.catalog.json`;
- classes de rota: `14 route classes` em `factory/templates/factory-route-registry.json`;
- motores de método: `8 method engines` em `factory/templates/method-engine-registry.json`;
- áreas de sistema operacional: `17 operating-system areas` em `factory/templates/factory-operating-system-registry.json`;
- workers públicos: `40 public workers` em `factory/agents/worker-registry.public.json`;
- schemas que definem records válidos;
- templates que materializam contratos e exemplos;
- scripts, principalmente `factory/scripts/factoryctl.py`, que validam, projetam e materializam as partes public-safe do sistema;
- testes que impedem a documentação pública de prometer entrega de runtime sem prova.

Ou seja: “Factory” não é vibe, prompt, Kanban, nem conjunto de documentos. É um conjunto de restrições executáveis em volta de trabalho agentic.

## Como ela se encaixa no Hermes

Hermes possui runtime. Factory possui disciplina de produção.

```text
sinal do operador
  -> contrato de fonte/intake da Factory
  -> phase engine e seleção de método da Factory
  -> board/card/workers no Hermes como runtime vivo
  -> Worker Packet enviado por profile/binding Hermes
  -> Worker Result volta com refs de evidência
  -> readback e gate evaluation da Factory
  -> transição, reparo, decisão humana ou fechamento no Hermes
```

### Dono do runtime

Hermes é dono de:

- identidade do board;
- status do card;
- dependências do card;
- comentários e anexos;
- runtime de atribuição de worker;
- transições vivas de blocked/running/done;
- estado de trabalho visível ao operador.

Factory é dona de:

- regras de preservação da fonte;
- Product SOT e cobertura de escopo;
- seleção de rota e método;
- formato do Worker Packet;
- limites de autoridade do worker;
- predicados de gate;
- exigência de evidência;
- regras de readback;
- consumo de review;
- requisitos do pacote de decisão humana;
- requisitos de fechamento por Receipt Five.

A ponte entre os dois não pode executar trabalho da fábrica. Bridge adapters não executam trabalho da fábrica; eles só carregam sinais de status, start, question, decision, change, exception, handoff ou learnback pela fronteira. Bridge modes como status_bridge, start_bridge, question_bridge, decision_bridge, change_bridge, exception_bridge, handoff_bridge e learnback_forwarding movem intenção, status ou decisão pela fronteira. Eles não substituem fases da Factory e não autorizam conclusão escondida.


### Detalhes da ponte do operador

Durable Operator Inbox é o padrão de caixa de entrada do operador para decisões, status e anexos. Ele precisa apontar para o default Hermes store como fonte de runtime do board/card, não para tracker privado duplicado. Factory Mechanic remains the self-improvement owner para melhorias do processo da Factory; adapters de ponte não podem mutar silenciosamente o método de produção.

The bridge cannot executar trabalho, aprovar gates, mutar a verdade do card por fora do Hermes ou transformar pergunta em autoridade de implementação. Ele só carrega sinais de start, status, question, decision, change, exception, handoff e learnback para dentro da fronteira da Factory.

## O modelo de objetos do runtime

Os objetos principais são:

- source envelope: sinal bruto selado antes da interpretação;
- source ledger: fatos, suposições, decisões, conflitos e lacunas;
- Product SOT: verdade do produto para o trabalho pedido;
- Method Contract: como esse tipo de trabalho será feito e provado;
- factory_phase_lock: fronteira atual e congelamento do downstream;
- Worker Packet: tarefa delimitada enviada ao worker;
- Worker Result: retorno estruturado do worker;
- Gate Report: resultado de predicado para promoção/bloqueio;
- Receipt Five: fechamento com pedido, trabalho, evidência, review e risco restante;
- Status Snapshot: projeção visível ao operador.

Arquivo existir não basta. Worker dizer “feito” não basta. Card andar não basta. A Factory lê campos, valida schemas, abre artefatos referenciados, confere saída de comando, consome review e reconcilia de volta para o Hermes.

## Verdade do produto não é resumo

Resumo raso diz: “construir onboarding”. Verdade do produto diz quem entra no onboarding, o que sucesso significa, o que está fora de escopo, que evidência prova a jornada e quais riscos ainda não foram resolvidos. Product SOT impede cada worker de construir uma interpretação diferente.

Product SOT ruim:

```text
Construir onboarding e deixar bom.
```

Product SOT utilizável:

```text
Usuário: admin novo de workspace.
Objetivo: criar workspace e chegar ao primeiro estado útil do dashboard.
Precisa incluir: criação de conta, nome do workspace, convite, loading, vazio, confirmação.
Fora de escopo: billing, KYC, editor de papéis, migração de email em produção.
Riscos: permissão de conta, entregabilidade de email, estado vazio confuso, overflow mobile.
Prova de aceite: screenshots Product Face, teste de primeira jornada, checagem backend de estado do workspace, review, Receipt Five.
Lacuna aberta: provider de convite em staging.
```

## Worker packets e autoridade

Worker Packet não é “me ajuda aí”. É fronteira executável. Um packet válido contém tarefa, entradas, arquivos/superfícies permitidos, ações proibidas, evidência exigida, campo de resultado, expectativa de reviewer e comportamento quando bloqueado.

Packet ruim:

```text
Construir onboarding e garantir que funciona.
```

Packet bom:

```text
Worker: Product Face reviewer
Tarefa: verificar UI de onboarding contra Product Face Packet.
Entradas: screenshots, lista de viewports, critérios de aceite, seção do Product SOT.
Precisa verificar: vazio, loading, erro, overflow mobile, caminho de primeira execução.
Precisa retornar: pass/fail, refs de evidência, defeitos, recomendação de reparo.
Não pode: aprovar release, mudar escopo, dispensar prova backend, tocar produção.
```

## Evidência, readback e Receipt Five

Prova fraca:

```text
Testes passaram.
```

Prova boa:

```text
O teste de regressão reproduziu o bug de reset de senha antes da correção, passou depois da correção e mapeia para o critério de aceite do Product SOT sobre recuperação de senha.
```

Prova fraca:

```text
Screenshot anexado.
```

Prova boa:

```text
Screenshots cobrem desktop, mobile, loading, vazio, erro e sucesso. Console foi inspecionado. O Product Face reviewer encontrou um defeito, o worker reparou, e o segundo review passou.
```

Receipt Five fecha o ciclo:

1. o que foi pedido;
2. o que foi feito;
3. que evidência prova;
4. quem revisou;
5. o que continua bloqueado, arriscado ou explicitamente fora de escopo.

## Decisões humanas

Decisão humana é necessária para produção, mainnet, fundos, segredos, orçamento, release, waiver, risco residual e mudança de autoridade. Falta de readback, worker antigo, anexo faltando, review não consumido e reparo interno não são decisões humanas; são trabalho da Factory.

Pedido ruim:

```text
Posso fazer deploy?
```

Pedido bom:

```text
Decisão necessária: promover onboarding v2 para staging.
Você está aprovando: deploy da versão X somente para staging.
Evidência: build, saída de testes, screenshots Product Face, review independente.
Risco restante: evento de analytics ainda não testado em carga.
A aprovação não autoriza: produção, billing, KYC, mainnet, segredos ou fundos.
Se recusar: a Factory abre reparo e mantém release bloqueado.
```

## Limites de status e prova

Teste local prova coerência do checkout. Ele não prova entrega viva no Hermes.

O mapa visual explica o sistema. Ele não prova runtime.

Não diga que docs públicas provam runtime. Não diga que comandos locais provam entrega privada de produto. Não diga que worker result prova done antes de readback, review e Receipt Five. Não diga que aprovação genérica cobre produção, mainnet, fundos ou segredos.

## Nomes de registry que maintainers realmente usam

Classes de rota são as categorias públicas de roteamento em `factory/templates/factory-route-registry.json`; uma delas é `product_creation`. Motores de método são as estratégias de execução em `factory/templates/method-engine-registry.json`. Áreas de operating-system são superfícies de dono em `factory/templates/factory-operating-system-registry.json`. Esses nomes importam porque worker packets, gates e testes apontam para eles.

## Domínios de segurança

Trabalho sensível pode rotear para domínios especialistas quando necessário: networking, linux-systems, web-security, ethical-hacking, security-tools, cloud-security, detection-monitoring, cryptography, security-operations, future-security, supply-chain, onchain-solana-quasar.

## Manual operacional fase por fase

As seções abaixo vêm do catálogo público de workflow e são explicadas em termos operacionais. Este é o fluxo real da fábrica, não pitch simplificado.


### F0 — Pre-Start / Sealed Source Envelope

#### O que realmente acontece

Factory has a sealed start packet before the production line begins.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Bridge/intake is a handoff boundary, not factory execution. New projects must create a fresh Hermes board through the factory start path.

#### Condições de entrada

- operator intent or external signal exists before factory execution

#### Artefatos obrigatórios

- factory_bridge_source_envelope
- factory_bridge_start_request

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Start Boundary

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- overkill-factory-gerente
- factory-orchestrator

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- seal source envelope
- create start request
- select new_project or existing_project explicitly

#### Ações bloqueadas

- summarize or reinterpret source material in the bridge
- create Hermes board/card directly from bridge
- start without explicit runtime target policy

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.factory_bridge_source_envelope_ref
- card.factory_bridge_start_request_ref
- run.board_binding

#### Como a conclusão é detectada

- sealed source envelope exists
- factory_bridge_start_request exists
- board policy is explicit

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/factory-bridge-source-envelope.schema.json
- factory/schemas/factory-bridge-start-request.schema.json
- factory/schemas/factory-run.schema.json

Comandos:
- factoryctl validate-factory-run
- factoryctl validate-card

### F1 — Intake

#### O que realmente acontece

Factory has the input, the chosen interface and the conversational start boundary.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Normalize the input into a route contract without treating user prose as approved scope. The interface profile controls proactive status and briefing attachments.

#### Condições de entrada

- user material or intent exists
- primary operator interface is selected

#### Artefatos obrigatórios

- operator_interface_profile
- factory_start_conversation
- universal_signal_intake
- source_refs
- source_resolution_packet

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Source Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- factory-orchestrator

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- select operator interface
- hold conversational start
- classify intake
- create universal signal intake
- create source resolution packet

#### Ações bloqueadas

- route implementation before source resolution
- create Product SOT from raw input
- require the operator to poll for status

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.operator_interface_profile_ref
- card.factory_start_conversation_ref
- card.universal_signal_intake_ref
- card.source_refs
- card.source_resolution_packet_ref

#### Como a conclusão é detectada

- operator_interface_profile exists
- factory_start_conversation exists
- universal_signal_intake exists
- source_refs is non-empty
- source_resolution_packet exists

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/operator-interface-profile.schema.json
- factory/schemas/factory-start-conversation.schema.json
- factory/schemas/universal-signal-intake.schema.json
- factory/schemas/source-resolution-packet.schema.json

Comandos:
- factoryctl operator-interface
- factoryctl start-conversation
- factoryctl validate-signal-intake
- factoryctl source-resolution
- factoryctl validate-card

### F2 — Source Ledger

#### O que realmente acontece

Factory is separating facts, assumptions and gaps, then checking whether it understood the product.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Keep raw extraction private; publish only public-safe refs. The operator confirmation is product understanding, not execution approval.

#### Condições de entrada

- intake classified

#### Artefatos obrigatórios

- source_refs
- product_source_ledger
- operator_understanding_confirmation

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Source Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- source-ledger-worker

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- record claims
- materialize product source ledger
- mark gaps and conflicts
- ask concise operator understanding confirmation

#### Ações bloqueadas

- ask user to reconcile internal source bookkeeping
- create outcome contract or Product SOT before understanding is confirmed

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.source_refs
- card.product_source_ledger_ref
- card.operator_understanding_confirmation_ref

#### Como a conclusão é detectada

- critical claims point to source refs
- product source ledger exists
- operator understanding confirmation is confirmed when Product SOT is required

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/reference-source-registry.schema.json
- factory/schemas/product-source-ledger.schema.json
- factory/schemas/operator-understanding-confirmation.schema.json

Comandos:
- factoryctl source-ledger
- factoryctl understanding-confirmation
- factoryctl validate-source-ledger
- factoryctl validate-understanding-confirmation
- factoryctl gate-report

### F3 — Source Resolution

#### O que realmente acontece

Factory is deciding what can be known safely.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Only authority/access/risk questions should reach the user.

#### Condições de entrada

- source ledger exists

#### Artefatos obrigatórios

- discovery_brief

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Discovery Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- source-ledger-worker
- product-sot-planner

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- resolve conflicts
- raise bounded human questions

#### Ações bloqueadas

- turn unresolved gaps into execution scope

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.discovery_brief

#### Como a conclusão é detectada

- open gaps are resolved, blocked or owner-assigned

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/discovery-brief.schema.json

Comandos:
- factoryctl help-next

### F4 — Product Outcome And Discovery

#### O que realmente acontece

Factory is turning confirmed understanding into a product outcome.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Outcome is still candidate until Product SOT approval or bounded acceptance. Product creation cannot skip understanding confirmation.

#### Condições de entrada

- material outcome is known
- operator understanding is confirmed when Product SOT is required

#### Artefatos obrigatórios

- operator_understanding_confirmation
- operator_briefing_package
- outcome_contract
- discovery_brief

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Outcome Gate
- Discovery Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- product-sot-planner

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- draft Product SOT candidate

#### Ações bloqueadas

- treat outcome candidate as approved Product SOT
- draft Product SOT before operator understanding confirmation

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.outcome_contract
- card.discovery_brief

#### Como a conclusão é detectada

- operator understanding confirmation exists when needed
- operator briefing package exists for decision artifacts
- outcome, user, problem and success signals exist

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/operator-understanding-confirmation.schema.json
- factory/schemas/operator-briefing-package.schema.json
- factory/schemas/outcome-contract.schema.json
- factory/schemas/discovery-brief.schema.json

Comandos:
- factoryctl understanding-confirmation
- factoryctl briefing-package
- factoryctl outcome-contract
- factoryctl validate-outcome-contract
- factoryctl validate-card

### F5 — Product SOT

#### O que realmente acontece

Factory has a candidate source of truth and a deep review package for the product.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: SOT can evolve beyond the input paper; paper is source, not final authority. The operator must not approve from a shallow message when a deep briefing is required.

#### Condições de entrada

- outcome and discovery are resolved enough
- operator understanding is confirmed when Product SOT is required

#### Artefatos obrigatórios

- product_sot
- operator_briefing_package
- full_product_sot_scope_coverage
- factory_phase_lock

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Product SOT Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- product-sot-planner

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- create or update Product SOT
- create Product SOT briefing package
- create full Product SOT scope coverage
- set factory_phase_lock active_frontier=product_sot until material is delivered
- request bounded scope approval only after material is delivered

#### Ações bloqueadas

- execute from paper instead of Product SOT
- ask operator to approve Product SOT from a short chat summary only
- start architecture, repo cleanup, human gate or worker packet while Product SOT owner package is missing

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.product_sot
- card.operator_briefing_package_ref
- card.full_product_sot_scope_coverage
- card.factory_phase_lock

#### Como a conclusão é detectada

- product_sot exists and scope is explicit
- operator briefing package includes markdown and PDF when a decision is needed
- factory_phase_lock.owner_surface_first.product_sot_review_packet_delivered is true before downstream phases
- product_sot.handoff.next_artifact points to full_product_sot_scope_coverage

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/product-sot.schema.json
- factory/schemas/operator-briefing-package.schema.json
- factory/schemas/full-product-sot-scope-coverage.schema.json
- factory/schemas/factory-phase-lock.schema.json
- factory/schemas/user-facing-autonomy-contract.schema.json

Comandos:
- factoryctl product-sot
- factoryctl briefing-package
- factoryctl validate-product-sot
- factoryctl full-scope-coverage
- factoryctl validate-full-scope-coverage
- factoryctl help-next

### F6 — Agentic Method Router

#### O que realmente acontece

Factory is choosing the safest production path.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: The router records decisions; it does not hand method selection to the user.

#### Condições de entrada

- owner-readable Product SOT review packet exists
- Product SOT candidate exists
- full Product SOT scope coverage exists

#### Artefatos obrigatórios

- factory_phase_lock
- method_contract

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Method Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- factory-orchestrator

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- select route and required methods
- keep architecture and worker packets frozen until Method Contract is materialized

#### Ações bloqueadas

- ask user to choose internal method machinery
- start architecture or repo cleanup before Method Contract

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.method_contract

#### Como a conclusão é detectada

- selected method, gates, workers and evidence are recorded
- factory_phase_lock can advance only after method_contract is materialized

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/factory-phase-lock.schema.json
- factory/schemas/method-contract.schema.json

Comandos:
- factoryctl method-contract
- factoryctl validate-method-contract
- factoryctl gate-report

### F7 — Method Contract

#### O que realmente acontece

Factory has recorded how the work will be produced.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Any omitted method needs a reason, not silence.

#### Condições de entrada

- method route chosen
- owner-readable Product SOT review material exists

#### Artefatos obrigatórios

- factory_phase_lock
- method_contract

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Method Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- factory-orchestrator

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- record required plans, gates and workers

#### Ações bloqueadas

- start implementation with undocumented process choices
- materialize future-phase cards while active frontier is still product_sot or method_contract

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.method_contract

#### Como a conclusão é detectada

- required artifacts and workers are named

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/factory-phase-lock.schema.json
- factory/schemas/method-contract.schema.json

Comandos:
- factoryctl validate-card

### F8 — Pack And Product Experience Selection

#### O que realmente acontece

Factory is choosing the capability packs and defining product surfaces, states, experience bar and proof before implementation.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Pack templates are not execution approval. Product-facing work cannot use generic implementation planning as a substitute for Product Experience and Product Face contracts.

#### Condições de entrada

- method contract exists

#### Artefatos obrigatórios

- capability_pack_contract
- product_experience_plan
- product_face_packet
- project_design_system
- professional_design_process
- surface_evidence_profile
- product_delivery_quality_profile

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Pack Gate
- Product Experience Gate
- Surface Pack Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- product-face
- factory-orchestrator

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- match capability packs
- mark missing capabilities
- create Product Experience Plan
- create Product Face Packet
- create Project DESIGN.md contract
- select surface evidence profile

#### Ações bloqueadas

- activate a pack without proof or coverage
- start product-facing implementation before surface state coverage
- treat generic UI proof as Product Experience proof
- move to implementation with unnamed surface pack or proof profile

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.product_experience_plan
- card.product_face_packet
- card.project_design_system
- card.professional_design_process
- card.product_delivery_quality_profile_ref

#### Como a conclusão é detectada

- required surfaces are covered or blocked
- product_experience_plan exists and names surface_pack
- product_face_packet exists and names required states and proof
- project_design_system exists and exports an AI-readable DESIGN.md contract
- surface_evidence_profile or surface_evidence_profiles are declared
- product_delivery_quality_profile_ref or product_delivery_quality_profile is declared
- professional_design_process exists before product-facing implementation

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/capability-pack-contract.schema.json
- factory/schemas/product-experience-plan.schema.json
- factory/schemas/product-face-packet.schema.json
- factory/schemas/project-design-system.schema.json
- factory/schemas/professional-design-process.schema.json
- factory/schemas/product-delivery-quality-profile.schema.json

Comandos:
- factoryctl help-next
- factoryctl gate-report
- factoryctl validate-card

### F9 — Risk And Authority Gates

#### O que realmente acontece

Factory will ask only for bounded authority, access or risk decisions.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Human approval must name scope and evidence.

#### Condições de entrada

- risk tier and surfaces are known
- factory_phase_lock permits authority review for the current frontier

#### Artefatos obrigatórios

- access_capability
- budget_contract

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Access Gate
- Budget Gate
- Human Gate when required

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- human-gate-clerk

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- prepare bounded approval requests only for real authority, access, risk, release, funds, secrets or irreversible action

#### Ações bloqueadas

- infer approval from silence
- ask for planning-only continuation approval
- ask for architecture or repo cleanup approval while downstream is frozen

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.access_capability
- card.budget_contract

#### Como a conclusão é detectada

- required authority is granted, blocked or not needed

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/access-capability.schema.json
- factory/schemas/budget-contract.schema.json

Comandos:
- factoryctl human-gate-record

### F10 — Security Architecture

#### O que realmente acontece

Factory is planning security before build work.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Security review is not a substitute for architecture.

#### Condições de entrada

- material security or privacy risk exists
- Product SOT owner-review material exists
- Method Contract exists
- factory_phase_lock active_frontier is architecture or later

#### Artefatos obrigatórios

- factory_phase_lock
- security_architecture_plan

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Security Architecture Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- security-orchestrator

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- route specialist security planning

#### Ações bloqueadas

- build material risk before architecture
- start security architecture while Product SOT or Method Contract is still missing

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.security_architecture_plan

#### Como a conclusão é detectada

- controls, threats and reviewers are named

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/factory-phase-lock.schema.json
- factory/schemas/security-architecture-plan.schema.json

Comandos:
- factoryctl worker-packet

### F11 — Executable Plans

#### O que realmente acontece

Factory is creating the execution plan.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: The user should see plan status, not internal planning machinery. F11 plans the complete product; F12 independently reviews the coverage before readiness can exist.

#### Condições de entrada

- method and required gates are known

#### Artefatos obrigatórios

- software_development_plan
- spec_graph
- loop_plan
- product_creation_plan

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Ready Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- decomposition-planner

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- create work units, verification plan and Product Creation Plan
- handoff Product Creation Plan to Decomposition Coverage Review before readiness

#### Ações bloqueadas

- execute before plans, coverage review and stop criteria exist
- mark decomposition review as passed from the planner that created the decomposition

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.software_development_plan
- card.spec_graph
- card.loop_plan
- card.product_creation_plan

#### Como a conclusão é detectada

- work units, checks, reviewers, dependencies and rollback are named in Product Creation Plan
- Product Creation Plan handoff points to decomposition_coverage_review
- declared data, metrics, docs and onboarding plans pass strict schema-backed runtime validation

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/software-development-plan.schema.json
- factory/schemas/spec-graph.schema.json
- factory/schemas/loop-plan.schema.json
- factory/schemas/product-creation-plan.schema.json
- factory/schemas/data-metrics-plan.schema.json
- factory/schemas/user-docs-onboarding-plan.schema.json

Comandos:
- factoryctl product-creation-plan
- factoryctl help-next

### F12 — Autonomy Readiness

#### O que realmente acontece

Factory is checking whether it can act safely.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Missing access becomes a bounded request, not vague user labor. Decomposition review is independent of the planner and must pass before readiness or dispatch can exist.

#### Condições de entrada

- Product Creation Plan exists
- Decomposition Coverage Review is PASS

#### Artefatos obrigatórios

- decomposition_coverage_review
- product_implementation_readiness
- autonomy_readiness_packet

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Decomposition Coverage Gate
- Access & Capability Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- independent-reviewer
- factory-orchestrator

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- run multi-operator decomposition coverage review from Product Creation Plan
- create Product Implementation Readiness only after Decomposition Coverage Review is PASS
- confirm tools, environment, limits and rollback

#### Ações bloqueadas

- start autonomous work with missing review, access or limits
- let a single reviewer approve the complete decomposition alone
- create Product Implementation Readiness from a failed or missing decomposition coverage review

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.decomposition_coverage_review
- card.product_implementation_readiness
- card.autonomy_readiness_packet

#### Como a conclusão é detectada

- Decomposition Coverage Review exists and is PASS
- every planned work-unit owner and reviewer signs the decomposition coverage matrix with evidence
- Product Implementation Readiness references the PASS Decomposition Coverage Review
- tools, accounts, environment and rollback are ready or blocked

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/decomposition-coverage-review.schema.json
- factory/schemas/product-implementation-readiness.schema.json
- factory/schemas/autonomy-readiness-packet.schema.json

Comandos:
- factoryctl decomposition-coverage-review
- factoryctl product-implementation-readiness
- factoryctl gate-report

### F13 — Ready Gate

#### O que realmente acontece

Factory can say whether execution may start.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Gate report must separate factory work from user decisions.

#### Condições de entrada

- Product Implementation Readiness exists and references a PASS Decomposition Coverage Review

#### Artefatos obrigatórios

- gate_report

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Ready Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- factory-orchestrator

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- create required worker tasks when gate passes

#### Ações bloqueadas

- dispatch blocked workers

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- factoryctl gate-report

#### Como a conclusão é detectada

- gate_predicate_result is PASS
- ready worker task materialization is allowed only for reviewed work units

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/gate-report.schema.json

Comandos:
- factoryctl gate-report
- factoryctl help-next

### F15 — Runtime Execution

#### O que realmente acontece

Factory is executing through routed workers.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: The user does not manage the worker queue.

#### Condições de entrada

- Ready Gate passed

#### Artefatos obrigatórios

- worker_packets

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Runtime Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- implementation-worker
- qa-verification-worker

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- dispatch required worker packets

#### Ações bloqueadas

- spawn without route readiness

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- .tmp/worker-packets
- Hermes worker tasks

#### Como a conclusão é detectada

- required worker tasks exist in runtime

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/worker-packet.schema.json

Comandos:
- factoryctl worker-packet

### F16 — Worker Results

#### O que realmente acontece

Factory is collecting what workers actually proved.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Generated requests are not execution evidence.

#### Condições de entrada

- worker packets were executed

#### Artefatos obrigatórios

- worker_results

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Done Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- evidence-reconciler

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- collect worker result records

#### Ações bloqueadas

- treat packet existence as proof

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- worker result artifacts

#### Como a conclusão é detectada

- required workers returned valid records

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/worker-result.schema.json

Comandos:
- factoryctl evidence-record

### F17 — Verification

#### O que realmente acontece

Factory is proving the work with checks.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Verification is scoped to the card and cannot be implied.

#### Condições de entrada

- implementation or proof exists

#### Artefatos obrigatórios

- verification_plan
- verification_result

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Verification Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- qa-verification-worker

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- run named checks and record outputs

#### Ações bloqueadas

- claim done without command evidence

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.verification_plan
- receipt.verification_commands

#### Como a conclusão é detectada

- verification commands and results are attached
- product-facing work has product_face_result with usage_evidence_matrix before completion

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/qa-verification-plan.schema.json

Comandos:
- factoryctl validate-completion

### F18 — Independent Review

#### O que realmente acontece

Factory is checking the work with an independent reviewer.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Review may find blockers; it is not ceremony.

#### Condições de entrada

- verification evidence exists

#### Artefatos obrigatórios

- review_result

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Review Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- independent-reviewer

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- route independent review

#### Ações bloqueadas

- allow executor to self-approve

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- worker result artifacts

#### Como a conclusão é detectada

- reviewer is different from executor and result is attached

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/reviewer-selection-plan.schema.json

Comandos:
- factoryctl worker-packet

### F20 — Closure Summary

#### O que realmente acontece

Factory is packaging what happened.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Handoff is replayable state, not a chat summary.

#### Condições de entrada

- workers, checks and review are complete or blocked

#### Artefatos obrigatórios

- closure_summary

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Closure Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- handoff-packer

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- summarize delivered work and remaining risk

#### Ações bloqueadas

- hide unresolved blockers in prose

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.closure_summary

#### Como a conclusão é detectada

- closure result and next step are explicit

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/worker-closure-summary.schema.json

Comandos:
- factoryctl status-snapshot

### F21 — Receipt Five

#### O que realmente acontece

Factory is preparing the done receipt.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Receipt Five is the durable proof boundary.

#### Condições de entrada

- closure summary is ready

#### Artefatos obrigatórios

- receipt_five

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Done Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- evidence-reconciler

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- reconcile receipt with evidence

#### Ações bloqueadas

- mark done without Receipt Five

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.receipt_five
- receipt artifact

#### Como a conclusão é detectada

- changed, artifacts, commands, review and next action exist
- product-facing receipts include Product Face result evidence refs

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/receipt-five.schema.json

Comandos:
- factoryctl validate-completion

### F22 — Completion Audit

#### O que realmente acontece

Factory is checking whether the promised work was actually delivered.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Audit must not inflate contract-level proof into runtime proof.

#### Condições de entrada

- receipt exists

#### Artefatos obrigatórios

- completion_audit

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Completion Audit

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- evidence-reconciler

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- compare required work with delivered work

#### Ações bloqueadas

- close skipped method or evidence requirements

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.completion_audit

#### Como a conclusão é detectada

- audit result is PASS, BLOCKED or PENDING with reasons

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/completion-audit.schema.json

Comandos:
- factoryctl validate-completion

### F23 — Production Operations

#### O que realmente acontece

Factory is preparing production operation or blocking release.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Production readiness is stronger than passing tests.

#### Condições de entrada

- completion audit allows promotion

#### Artefatos obrigatórios

- production_readiness_plan

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Release Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- release-ops-worker

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- prepare release, rollback and monitoring

#### Ações bloqueadas

- release without owner, rollback or approval

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.production_readiness_plan

#### Como a conclusão é detectada

- owner, rollback, health checks and approval rule exist

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/production-readiness-plan.schema.json

Comandos:
- factoryctl gate-report

### F24 — Release Or Block

#### O que realmente acontece

Factory is ready to release or can explain why not.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Blocked is a valid result when evidence is insufficient.

#### Condições de entrada

- production operations plan exists

#### Artefatos obrigatórios

- release_decision

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Release Gate
- Human Gate when required

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- release-ops-worker
- human-gate-clerk

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- release with authority or block with next action

#### Ações bloqueadas

- promote without production-strict evidence

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- release decision artifact

#### Como a conclusão é detectada

- release or block has owner, evidence and next action

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/gate-report.schema.json

Comandos:
- factoryctl help-next

### F25 — Monitoring Support

#### O que realmente acontece

Factory has a support and incident path.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Support is part of production, not afterthought docs.

#### Condições de entrada

- release or production block is decided

#### Artefatos obrigatórios

- incident_support_plan

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Support Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- release-ops-worker

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- activate monitoring or support path

#### Ações bloqueadas

- ship without support owner when support is material

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.incident_support_plan

#### Como a conclusão é detectada

- incident triggers, triage and escalation exist

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/incident-support-plan.schema.json

Comandos:
- factoryctl validate-card

### F26 — Learnback

#### O que realmente acontece

Factory is learning from the run without changing critical rules silently.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Critical factory changes require explicit human approval.

#### Condições de entrada

- work closed, blocked or released

#### Artefatos obrigatórios

- factory_learning_proposal

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Learning Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- skill-eval-distiller

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- convert repeated failure into proposal

#### Ações bloqueadas

- auto-activate critical factory changes

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- factory/templates/factory-learning-proposal.json

#### Como a conclusão é detectada

- proposal is accepted, rejected or gated

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/factory-learning-proposal.schema.json

Comandos:
- factoryctl validate-card

### F27 — Factory Maturity Audit

#### O que realmente acontece

Factory is auditing its own process gaps.

Nesta fase a Factory não está fazendo “gerenciamento de projeto” genérico. Ela está transformando o card atual em um estado mais rígido e verificável por máquina. O phase engine olha o card, os artefatos materializados, os registries de rota/método e a evidência de workers disponível. Depois decide se a fase pode avançar, precisa bloquear ou precisa criar trabalho delimitado dentro do Hermes.

Detalhe de maintainer: Public repo gets proposals and contracts, not raw evidence.

#### Condições de entrada

- learnback exists or repeated blind spot is detected

#### Artefatos obrigatórios

- factory_maturity_scorecard

Esses artefatos não são decoração. Eles são o estado que fases posteriores leem. Se um deles falta, as fases seguintes não podem fingir que o estado existe.

#### Gates obrigatórios

- Maturity Gate

Gate não é checkpoint simpático. É predicado de promoção. Se o predicado não está satisfeito, o card fica bloqueado ou uma rota de reparo é criada.

#### Workers obrigatórios

- skill-eval-distiller

Workers não recebem intenção aberta. Eles recebem um Worker Packet com escopo, entrada, autoridade, evidência exigida e campo de resultado. Hermes profiles materialize worker roles, mas a Factory decide se o worker result é consumível.

#### Próximas ações permitidas

- open public-safe improvement issue

#### Ações bloqueadas

- commit raw study or private evidence

Essas são as regras anti-teatro da fase. Se worker ou operador tenta fazer uma delas, o resultado correto não é “seguir mesmo assim”; é bloquear, reparar ou escalar para a autoridade certa.

#### Onde a saída fica para fases posteriores

- card.factory_maturity_scorecard

#### Como a conclusão é detectada

- blind spots and actions are recorded

Detecção de conclusão é onde documentação rasa costuma mentir. A Factory não pergunta “parece completo?”. Ela pergunta se os campos, artefatos, worker results, gates e refs de prova que a próxima fase precisa existem e são consumíveis.

#### Schemas e comandos

Schemas:
- factory/schemas/factory-maturity-scorecard.schema.json

Comandos:
- factoryctl status-snapshot


## Como um card avança de verdade

Um card só avança quando o phase engine encontra o próximo artefato obrigatório, o predicado de gate relevante passa, workers obrigatórios estão satisfeitos ou não aplicáveis, e a próxima transição é legal para a fronteira atual. Se qualquer ponto é falso, a Factory deve criar trabalho delimitado de reparo no Hermes ou bloquear com motivo.

Postura no-idle não significa “spammar workers até algo mexer”. Significa que um card bloqueado precisa ter dono, próxima ação segura, escopo congelado e exigência de prova. Se a Factory consegue resolver sem humano, resolve. Se o bloqueio é realmente autoridade humana, ela prepara pacote de decisão.

## Como debugar a Factory

Quando algo parecer errado, inspecione nesta ordem:

1. source refs e source ledger;
2. Product SOT e full scope coverage;
3. factory_phase_lock;
4. rota e Method Contract;
5. worker packets criados no Hermes;
6. worker results e refs de evidência;
7. readback e validação de schema;
8. review result e se foi consumido;
9. pacote de human gate, se necessário;
10. Receipt Five e closure summary.

Não debuge por vibe. Debuge por campos, gates, worker results e estado Hermes.
