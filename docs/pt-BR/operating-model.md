# Modelo operacional

Esta página explica o que acontece numa execução da fábrica. Em vez de fazer um passeio por pastas internas, ela acompanha a vida de um pedido.

Um pedido começa como um sinal. Pode ser uma ideia de produto, um bug, um release, um incidente, uma mudança de segurança, uma tela, um pedido de dados, uma integração ou uma melhoria de worker. O primeiro trabalho da fábrica não é construir. É entender que tipo de trabalho entrou e o que tornaria o avanço seguro.

## 1. A entrada protege a fonte

A fábrica recebe o material de origem e cria um envelope de fonte. Esse envelope preserva o que o operador realmente entregou. Ele não deveria transformar tudo, em silêncio, num resumo conveniente.

Depois, o source ledger registra o que já se sabe, o que falta, o que está em conflito e o que ainda precisa do operador. Parece básico, mas evita uma das falhas mais caras em sistemas com agentes: construir a partir de um briefing mal entendido.

O operador deveria receber uma explicação simples: "foi isso que entendemos, isso ainda falta, isso não podemos assumir". Se essa explicação não estiver clara, a execução já nasceu fraca.

## 2. A rota escolhe o tipo de execução

A classe de rota decide o formato do trabalho. Corrigir bug não é preparar release. Preparar release não é criar produto do zero. Auditar Solana/onchain não é atualizar documentação. Hoje a fábrica expõe estas classes de rota:

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

A rota não dá permissão para um worker sair fazendo o que quiser. Ela escolhe a faixa, a família de método e os gates que precisam ser satisfeitos.

## 3. A verdade do produto vira contrato

Em trabalho de produto, o Product SOT transforma o material de origem numa definição usável. É o momento em que a fábrica diz: "este é o produto que estamos construindo de verdade".

Um Product SOT fraco enfraquece tudo que vem depois. Workers ainda podem produzir código, docs, design ou comentários de revisão, mas talvez estejam otimizando para a coisa errada. Por isso a fábrica bloqueia execução downstream quando a verdade do produto falta ou ainda não foi revisada.

## 4. O método liga a rota à evidência

O contrato de método diz como esta execução deve ser tratada. Os motores de método atuais incluem:

- `spec_first_sdd`: None. Entra quando a rota pede `spec_first`. Rotas: .
- `test_first_tdd`: None. Entra quando a rota pede `test_first`. Rotas: .
- `behavior_first_bdd`: None. Entra quando a rota pede `behavior_first`. Rotas: .
- `discovery_research`: None. Entra quando a rota pede `discovery_first`. Rotas: .
- `security_first_threat_model`: None. Entra quando a rota pede `security_first`. Rotas: .
- `design_first_product_experience`: None. Entra quando a rota pede `design_first`. Rotas: .
- `legacy_diagnosis`: None. Entra quando a rota pede `legacy_diagnosis`. Rotas: .
- `incident_first`: None. Entra quando a rota pede `incident_first`. Rotas: .

O método importa porque muda a evidência. Trabalho test-first precisa de teste e prova de regressão. Trabalho design-first precisa de prova de experiência de produto. Trabalho security-first precisa de threat modeling e evidência de segurança. Incidente precisa de mitigação, status e learnback.

Método não é slogan. Ele precisa produzir artefatos, gates, pacotes de worker e critérios de parada.

## 5. O trabalho vira pacotes pequenos

Um worker packet é um contrato pequeno. Ele diz ao worker o que fazer, o que não fazer, que evidência anexar e que autoridade ele tem. É aqui que a fábrica evita o pedido vago: "constrói isso aí".

Pacotes bons são estreitos. Dá para executar, revisar, repetir e fechar. Pacotes ruins são missões grandes sem prova clara. A fábrica deve criar os primeiros e bloquear os segundos.

## 6. O Hermes roda o chão da fábrica

Hermes Kanban continua sendo a fonte de verdade do runtime. Cards, dependências, comentários, status de worker, workspaces e transições vivem nele. A fábrica prepara e valida os contratos de produção; o Hermes registra o que está acontecendo de fato.

Essa separação é importante. Arquivos locais provam que o kernel público está coerente. Eles não provam que uma execução viva, num Hermes do operador, terminou. Conclusão real precisa de estado de runtime, resultado de worker, revisão, evidência e decisões humanas quando o risco exige.

## Modos da ponte com o operador

A ponte pública com o operador é uma camada de interface. Ela traduz mensagens do operador para registros seguros da fábrica, mas não executa trabalho da fábrica sozinha. A execução continua pertencendo aos cards Hermes e aos workers atribuídos.

Os modos da ponte são `status_bridge`, `start_bridge`, `question_bridge`, `decision_bridge`, `change_bridge`, `exception_bridge`, `handoff_bridge` e `learnback_forwarding`. Um pedido de início cria ou encaminha contexto de `factory_bridge_start_request`; ele não pula fonte, método nem gates de prontidão.

A ponte separa o `overkill-factory-gerente`, que conversa com o operador, do `factory-orchestrator`, que cuida de rota e controle de runtime. O Durable Operator Inbox preserva decisões, perguntas e handoffs no default Hermes store. O Factory Mechanic continua sendo o dono de self-improvement e learnback. A ponte não pode conceder autoridade, inventar aprovação, fechar gate ou declarar conclusão sem evidência.

## 7. Revisar é diferente de executar

O executor não deveria ser o juiz final de trabalho material. A fábrica usa readback, verificação, revisão independente e Receipt Five para separar "o worker disse que terminou" de "a fábrica consegue provar que terminou".

Se a revisão passa, o resultado precisa voltar para a tarefa original. Se falha, a fábrica deve criar trabalho de reparo. Uma revisão aprovada que fica parada não é progresso. É mais um estado bloqueado.

## 8. Gates humanos são raros, mas reais

Um gate humano entra quando a decisão pertence ao operador: aceitar risco, aprovar orçamento, mexer em produção, mainnet, segredos, release ou outra fronteira explícita de autoridade. A fábrica não deve pedir aprovação humana só porque não sabe continuar.

Quando o gate humano é necessário, o operador deve receber um pacote de decisão: a escolha, a evidência, o risco, a recomendação e a consequência de cada caminho. JSON cru não é um bom gate humano. Pergunta vaga no chat é pior.

## 9. Entregar, bloquear ou aprender

Uma execução termina em um de três estados honestos.

Ela pode entregar quando a evidência é forte o bastante e os gates necessários passaram. Pode bloquear quando falta prova, acesso, autoridade ou segurança. Ou pode aprender quando a execução mostra um método melhor, um worker ausente, um validador fraco ou uma falha que se repete.

Aprendizado também tem gate. A fábrica não deve se reescrever em silêncio porque uma execução foi estranha. Ela deve propor a mudança, testar e promover só quando for seguro.
