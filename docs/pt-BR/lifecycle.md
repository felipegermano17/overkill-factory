# Ciclo da fábrica

Esta página estava complicada demais. O ciclo da fábrica não deveria parecer uma tabela técnica com inglês vazando por todos os lados.

O workflow compilado é a fonte factual para a máquina. Para o leitor, ele precisa virar uma história simples.

A ideia é mais simples: um pedido entra cru e só pode virar entrega depois de passar por alguns momentos de proteção.

Não decore fase. Entenda o movimento.

## O ciclo em linguagem humana

```text
pedido
-> fonte protegida
-> entendimento
-> verdade do produto
-> caminho escolhido
-> trabalho dividido
-> execução no Hermes
-> prova e revisão
-> decisão humana, se precisar
-> entrega, bloqueio ou aprendizado
```

É isso.

Por baixo existem fases, gates, workers e schemas. Eles importam para a máquina. Para o leitor, o mais importante é entender por que cada momento existe.

## 1. Antes de começar: proteger a fonte

A fábrica começa antes da execução.

O operador pode mandar uma ideia, um documento, um bug, um link, um repo, uma conversa ou um pedido de release. A fábrica precisa guardar isso sem deformar.

O erro comum é resumir cedo demais. Um resumo curto vira plano. O plano vira execução. Depois todo mundo descobre que a primeira interpretação estava errada.

Então o começo da fábrica protege a fonte, cria o pedido inicial e diz qual runtime vai carregar o trabalho.

Nome interno que aparece no workflow: F0 — Pre-Start / Sealed Source Envelope.

## 2. Entender o que entrou

Depois a fábrica pergunta: "que tipo de sinal é esse?"

É produto novo? Bug? Incidente? Release? Segurança? UI? Integração? Migração? Trabalho em agente? Documentação?

Ela também separa fato, palpite, decisão, conflito e lacuna. Isso é chato de fazer, mas salva a execução. Se essa separação não acontece, o agente começa a construir em cima de uma mistura perigosa.

O operador deveria enxergar algo simples: "entendemos isto, falta aquilo, isso não podemos assumir".

Aqui vivem as fases de entrada, source ledger, source resolution e descoberta.

## 3. Definir a verdade do produto

Antes de construir produto, a fábrica precisa dizer que produto é esse.

Essa é a fase do Product SOT. Em português: a verdade do produto.

Ela define escopo, não escopo, usuário, problema, critério de aceite, risco e prova. Se o trabalho é grande, também precisa cobrir o escopo inteiro. A primeira fatia não pode fingir ser o todo.

O atalho perigoso aqui é executar a partir de uma conversa ou de um paper sem transformar aquilo em verdade revisável.

Se a verdade do produto está fraca, o resto pode ficar bonito e ainda assim errado.

## 4. Escolher a rota e o método

Com a verdade na mesa, a fábrica escolhe o caminho.

Bug não anda como release. Release não anda como tela. Segurança não anda como docs. Produto com interface não anda como backend puro. Mainnet, fundos e segredo não andam como tarefa comum.

Rota responde: "que tipo de trabalho é esse?"

Método responde: "como esse trabalho deve ser feito e provado?"

O operador não precisa escolher engine interno. A fábrica escolhe e explica o suficiente para o humano confiar na direção.

O atalho perigoso é começar arquitetura, PR ou worker packet antes de método claro.

## 5. Checar capacidade, risco e autoridade

Antes de execução material, a fábrica precisa perguntar:

Temos o tipo certo de worker?

Temos acesso?

Tem orçamento?

Tem risco de produção, mainnet, segredo, privacidade, carteira, assinatura ou dinheiro?

Tem pacote de capacidade para esse tipo de produto?

Se falta capacidade, bloqueia. Se a decisão é humana, prepara pacote. Se a decisão é da fábrica, a fábrica trabalha.

Essa parte existe para impedir falsa competência. É melhor dizer "não tenho cobertura ainda" do que fingir especialista.

## 6. Planejar o trabalho de verdade

Agora o produto vira unidades pequenas.

Uma unidade boa tem dono, reviewer, prova, dependência e regra de pronto. Se não tem isso, ainda é desejo, não trabalho.

Aqui entram planos de desenvolvimento, grafo de specs, plano de loop, plano de criação do produto e prontidão de implementação.

O atalho perigoso é mandar agentes trabalharem em paralelo sem saber quem depende de quem e que prova fecha cada pedaço.

## 7. Rodar no Hermes

Hermes é o chão da fábrica.

Quando a execução começa, ela precisa aparecer como cards, dependências, workers, workspaces, comentários, bloqueios e transições no Hermes. A fábrica pode reconciliar e reparar, mas não pode esconder um segundo estado por fora.

Se tem trabalho pronto, Hermes despacha. Se tem dependência, espera. Se o board fica silencioso sem motivo, no-idle repara ou falha de forma visível.

O atalho perigoso é deixar um agente operar numa lista privada e depois tentar sincronizar a verdade no fim.

## 8. Provar o que foi feito

Worker que executa precisa devolver resultado com evidência.

Dependendo do trabalho, evidência pode ser teste, diff, screenshot, transcript, log, scan, auditoria, simulação, pacote de release, proof remoto ou documento revisado.

Produto visível precisa de prova visível. CLI precisa de transcript. Documentação precisa provar que leva o leitor ao primeiro sucesso. Segurança precisa de evidência de risco. Release precisa de rollback e prontidão.

O atalho perigoso é tratar existência de arquivo ou pacote de worker como prova.

## 9. Revisar e reconciliar

Depois da execução vem a parte que muita gente pula: consumir a revisão.

Revisão boa não é comentário solto. Ela passa ou falha algo específico. Se passa, destrava. Se falha, cria reparo. Se sobra risco, registra dono e decisão.

Depois vem o Receipt Five, que amarra pedido, mudança, evidência, revisão e próximo estado.

Sem isso, "feito" ainda é frágil.

## 10. Chamar o humano quando a decisão é humana

Algumas coisas não podem ser decididas por worker.

Produção. Mainnet. Fundos. Segredos. Orçamento. Risco residual. Release. Waiver.

Nesses casos, a fábrica precisa entregar um pacote de decisão. A pessoa recebe o material, a escolha, o risco, o que aprovar autoriza e o que não autoriza.

O atalho perigoso é pedir "posso seguir?" sem entregar o artefato sob revisão.

## 11. Entregar, bloquear ou aprender

No final, só existem três saídas honestas.

Entrega: a prova existe, a revisão foi consumida, os gates passaram e o próximo estado está claro.

Bloqueio: falta prova, acesso, autoridade, capacidade ou segurança. O bloqueio precisa ter dono e próximo passo.

Aprendizado: a execução mostrou que a própria fábrica precisa melhorar. Isso pode virar teste, doc, skill, worker, gate, issue ou mudança de processo.

A fábrica não deve chamar tudo de sucesso. Às vezes a melhor resposta é um bloqueio bem explicado.

## Onde entram as fases internas

O workflow compilado ainda tem fases internas. Elas existem para a máquina e para os maintainers.

A versão atual expõe 26 fases em `docs/factory-workflow.catalog.json`. Você pode inspecionar com:

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

Mas para ler o produto, use o ciclo simples desta página. As fases internas são o mecanismo. O movimento humano é: entender, organizar, executar, provar e fechar.
