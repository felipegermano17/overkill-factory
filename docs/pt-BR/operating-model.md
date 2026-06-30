# Modelo operacional

Esta página acompanha a vida de um pedido dentro da fábrica. A pergunta central não é “qual script roda?”, mas “como um pedido vira trabalho seguro, provado e revisável?”.

Um pedido começa como sinal. Pode ser uma ideia de produto, um bug, um release, um incidente, uma tela, uma integração, uma auditoria, uma mudança em agente ou uma melhoria na própria fábrica. A resposta errada é sair fazendo. A resposta certa é preservar a fonte, entender o tipo de trabalho, escolher o método e só então executar.

## 1. O pedido entra pela porta certa

A fábrica pode conversar com o operador por Telegram, Discord, cockpit, CLI ou outro canal. Mas o canal é só a recepção. Ele não é a fonte de verdade.

O operador entrega material, objetivo, restrições e decisões quando elas são realmente dele. A fábrica deve cuidar do resto: registrar fonte, separar fato de inferência, montar Product SOT, escolher rota, criar worker packets, acompanhar Hermes, cobrar evidência, pedir review, preparar gates humanos e fechar com Receipt Five.

Isso tira trabalho das costas do operador. Ele não deveria ter que perceber que um worker foi raso, que a revisão não foi consumida, que o board parou por preguiça de processo ou que faltava pacote de decisão. Se isso acontece, é falha da fábrica.

## 2. A fonte é protegida antes do plano

O primeiro artefato importante é o envelope de fonte. Ele preserva o que chegou antes da fábrica resumir, interpretar ou decompor. Depois vem o source ledger, que separa cinco coisas que agentes costumam misturar:

- fato vindo da fonte;
- inferência razoável;
- decisão já tomada;
- conflito entre fontes;
- lacuna que ainda precisa ser resolvida.

Essa separação parece simples, mas muda tudo. Sem ela, um resumo curto vira “verdade” e o produto começa torto.

## 3. A fábrica trabalha em cinco camadas

A documentação legada tinha um bom mapa que continua atual. A fábrica opera em cinco camadas:

1. Camada de verdade: fonte, source resolution, Product SOT, decisões, conflitos e lacunas.
2. Camada de método e planejamento: rota, método, arquitetura, Product Creation Plan, Product Experience Plan, dados, evals e loop plan.
3. Camada de risco, autoridade, acesso e custo: risco, orçamento, segredos, produção, mainnet, privacidade, compliance e gates humanos.
4. Camada de execução e evidência: Hermes, worker packets, worker results, Product Face, QA, review, proof remoto e Receipt Five.
5. Camada de operação e aprendizado: release, monitoramento, suporte, incidente, learnback e auditoria de maturidade.

A utilidade desse mapa é mostrar que “fazer a tarefa” é só uma parte. A fábrica também precisa saber se a tarefa certa foi escolhida, se havia autoridade, se o produto foi provado e se a própria fábrica aprendeu algo.

## 4. A rota escolhe o peso certo

Rotas são a forma da fábrica dizer: este pedido não é igual aos outros.

Um bug precisa de reprodução e regressão. Um produto novo precisa de Product SOT e cobertura de escopo. Um release precisa de prontidão, rollback e dono. Um incidente precisa de severidade, mitigação e learnback. Uma integração crítica precisa de contrato, fallback e teste. Uma mudança de segurança precisa de arquitetura e review. Uma tela precisa de Product Face, estados, jornada e prova visual.

A fábrica tem quatorze classes de rota. O detalhe exato fica nos registries, mas a ideia pública é esta: cada tipo de trabalho ganha gates e provas diferentes. Isso impede que o mesmo agente genérico trate documentação, mainnet, UI, release e incidente como se fossem variações da mesma tarefa.

## 5. Product SOT é verdade do produto, não papel bonito

Product SOT é a definição revisável do produto. Ele deve dizer o que entra, o que não entra, quais usuários importam, quais promessas precisam ser cumpridas, que riscos existem e que evidência vai contar como aceite.

A fábrica também precisa de Full Product SOT Scope Coverage quando o trabalho é produto completo. Isso impede que a primeira fatia prática seja confundida com o produto inteiro. Cada requisito importante precisa estar planejado, bloqueado com dono, fora de escopo com justificativa, delegado ao humano ou concluído com prova.

Sem essa cobertura, workers podem trabalhar muito e ainda entregar uma versão estreita demais do produto.

## 6. Método liga intenção a prova

O Method Contract registra como aquele trabalho será feito. Ele pode puxar um caminho spec-first, test-first, behavior-first, discovery-first, security-first, design-first, legacy-diagnosis ou incident-first.

O ponto não é o nome do método. O ponto é que o método muda a evidência:

- test-first precisa de teste e regressão;
- design-first precisa de Product Experience Plan, Product Face Packet e prova por superfície;
- security-first precisa de ameaça, fronteira de confiança, scan e review;
- discovery-first precisa transformar incerteza em decisão operacional;
- legacy-diagnosis precisa baseline, rollback e proteção contra regressão;
- incident-first precisa mitigação, status, causa e learnback.

Método que não muda artefato, gate ou prova é só slogan.



## Modos da ponte com o operador

A ponte pública com o operador é uma camada de interface. Ela traduz mensagens do operador para registros seguros da fábrica, mas não executa trabalho da fábrica sozinha. A execução continua pertencendo aos cards Hermes e aos workers atribuídos.

Os modos da ponte são `status_bridge`, `start_bridge`, `question_bridge`, `decision_bridge`, `change_bridge`, `exception_bridge`, `handoff_bridge` e `learnback_forwarding`. Um pedido de início cria ou encaminha contexto de `factory_bridge_start_request`; ele não pula fonte, método nem gates de prontidão.

A ponte separa o `overkill-factory-gerente`, que conversa com o operador, do `factory-orchestrator`, que cuida de rota e controle de runtime. O Durable Operator Inbox preserva decisões, perguntas e handoffs no default Hermes store. O Factory Mechanic continua sendo o dono de self-improvement e learnback. A ponte não pode conceder autoridade, inventar aprovação, fechar gate ou declarar conclusão sem evidência.

## 7. Capability packs evitam falsa competência

A fábrica não deve fingir que um agente genérico cobre qualquer produto. Web SaaS, CLI/TUI, cloud, agente, Solana, mobile nativo, desktop, jogo, fintech, analytics, browser extension e hardware pedem provas diferentes.

Os capability packs dizem o que já está pronto e o que ainda é template. Packs core como web, CLI/TUI, cloud, agent-runtime, Solana AI Kit, onboarding e public docs podem seguir quando a rota e os gates batem. Packs de mobile, desktop, game, AI/ML, fintech, regulated domain, analytics, browser extension e hardware precisam ser ativados com especialistas, bindings, smoke, eval e evidência antes de execução material.

Isso é uma fronteira de honestidade. Bloquear por falta de pack é melhor do que fingir especialista.

## 8. O trabalho vira worker packet pequeno

Um worker packet é uma tarefa com bordas. Ele diz ao worker o que fazer, o que receber, o que devolver, que evidência anexar e que autoridade ele não tem.

Um bom packet consegue ser executado, revisado e refeito. Um packet ruim pede “construa o produto” e depois força o operador a adivinhar se ficou bom.

Workers importantes incluem orquestração, source ledger, Product SOT, arquitetura, Product Face, builders, QA, segurança, review, release, handoff, evidence reconciler, human-gate clerk e skill/eval distiller. O nome não basta. Cada worker precisa de perfil, binding Hermes, receipt field, política de evidência e limite de autoridade.

## 9. Hermes é o chão, a fábrica é o contrato

Hermes Kanban continua sendo a fonte de verdade do runtime. Ele guarda cards, dependências, status, workers, workspaces, comentários e transições. A fábrica não deve criar um segundo runtime escondido.

A fábrica prepara o contrato: que artefatos faltam, que gates bloqueiam, que workers entram, que tipo de evidência é aceitável e que aprovação humana é real. Hermes registra o trabalho vivo.

Quando a fábrica cria tarefas Hermes, ela deve usar dependências nativas. Se uma fase depende de work units, esses work units precisam ser pais da fase seguinte. Se aparecem tarde, entram no grafo antes do downstream andar. Não é aceitável descobrir trabalho obrigatório depois que a fase já está “done”.

## 10. No-idle não é despachante paralelo

No-idle existe para detectar silêncio perigoso. Se há trabalho rodando, ele observa. Se há ready, Hermes despacha. Se há dependency_wait, ele espera a dependência. Se há needs_input com pacote de decisão pronto, o gerente chama o operador. Se falta pacote, readback, PDF, artefato ou reparo interno, a fábrica corrige em vez de jogar no humano.

Essa regra importa muito. No-idle não pode virar um mini-Hermes. Ele é auditor de integridade do board, não fonte normal de autoridade.

## 11. Product Face prova a cara do produto

Produto com interface precisa provar experiência, não só backend ou arquitetura. Product Face cobre web visual, CLI/TUI, docs/onboarding, interface agentic, wallet UI e outros tipos de superfície.

Para web, a prova pode incluir screenshots, viewports, estados, jornada, console, acessibilidade básica, overflow e comparação com o Product Face Packet. Para CLI/TUI, precisa transcript, help, instalação, erro e comportamento de terminal. Para docs/onboarding, precisa replay do primeiro sucesso e critério de leitor. Para interface agentic, precisa controle do usuário, permissões, recuperação e limites.

Uma screenshot não prova produto inteiro. Product Face é uma parte da evidência, consumida junto com SOT, método, QA, review e Receipt Five.

## 12. Gates humanos são pacotes, não perguntas soltas

Gate humano só entra quando a decisão pertence ao operador: produção, mainnet, fundos, segredos, orçamento, autoridade, release, risco material ou waiver explícito.

O gate deve ser artifact-first. O operador recebe o artefato ou uma projeção fiel, um resumo de uma tela, opções claras, consequência de cada opção, o que a aprovação autoriza e o que ela não autoriza. JSON cru, caminho local ou pergunta vaga no chat não são gate humano válido.

A voz humana é o gerente. Worker, cron, evento Kanban e dump de artefato podem alimentar o estado interno, mas não deveriam notificar o operador diretamente.

## 13. Fechamento honesto

Uma execução termina em entregar, bloquear ou aprender.

Entrega exige evidência atual, readback, review consumido, Receipt Five e gates satisfeitos. Bloqueio exige motivo claro, dono e menor próximo passo seguro. Learnback exige proposta, teste, review e promoção; a fábrica não deve se alterar em silêncio porque uma execução foi estranha.
