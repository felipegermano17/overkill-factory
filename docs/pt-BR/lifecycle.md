# Ciclo simples

O workflow compilado é a fonte factual para a máquina. Ele tem fases, gates, workers e artefatos.

Mas a pessoa que está tentando entender a fábrica não deveria começar decorando fase.

O ciclo humano é este:

```text
pedido
-> fonte protegida
-> entendimento
-> verdade do produto
-> caminho escolhido
-> trabalho pequeno
-> execução no Hermes
-> prova
-> revisão
-> decisão humana, se houver
-> entrega, bloqueio ou aprendizado
```

## 1. Pedido

Tudo começa com um sinal.

Pode ser uma frase, um bug, um repo, um documento, uma conversa, uma tela, um incidente, um pedido de release.

A fábrica ainda não sabe se isso é produto, correção, operação, risco, pesquisa ou decisão. Então ela não deveria sair executando.

## 2. Fonte protegida

Antes de interpretar, a fábrica preserva a fonte.

Isso impede que a primeira versão resumida vire verdade oficial.

Se o operador mandou contexto longo, a fábrica não pode amputar o contexto e depois construir sobre o pedaço que sobrou.

## 3. Entendimento

A fábrica separa fato, inferência, decisão, conflito e lacuna.

Aqui ela deve conseguir dizer em português claro: "sabemos isso, achamos aquilo, falta isto, este ponto conflita".

Se essa leitura está fraca, o resto ainda não deveria andar.

## 4. Verdade do produto

Agora o pedido vira definição.

Qual é o produto? Para quem? Que problema resolve? O que entra? O que fica fora? Que risco importa? Que prova conta?

A fábrica chama isso de Product SOT, mas a ideia é só esta: ninguém deveria construir antes de saber o que está construindo.

## 5. Caminho escolhido

A fábrica escolhe rota e método.

Bug, release, incidente, segurança, interface, integração, docs, agente, Solana e produto novo não andam do mesmo jeito.

A rota escolhe a régua. O método escolhe como provar.

## 6. Capacidade e autoridade

Antes de mandar worker, a fábrica pergunta se tem capacidade e autoridade.

Tem worker certo? Tem acesso? Tem pack para essa superfície? Toca segredo? Toca produção? Toca mainnet? Toca fundos? Precisa de humano?

Se falta capacidade, bloqueia. Se precisa de decisão humana, prepara pacote. Se é problema interno, repara.

## 7. Trabalho pequeno

O produto vira unidades menores.

Cada unidade precisa ter entrada, saída, dono, dependência, evidência, reviewer e regra de pronto.

Sem isso, não é trabalho. É desejo.

## 8. Execução no Hermes

Hermes é onde o trabalho vivo aparece.

Cards, dependências, workers, comentários, workspaces, anexos, bloqueios e transições precisam estar no runtime. A fábrica não deveria manter uma verdade paralela escondida.

Se algo depende de outra coisa, a dependência precisa estar no grafo.

## 9. Prova

Cada worker devolve evidência.

Para código, pode ser teste, diff, build, scan.

Para interface, tela, jornada, estado, console, viewport.

Para CLI, transcript, instalação, help, erro.

Para release, prontidão, rollback, dono.

Para docs, clareza, navegação, primeiro sucesso.

A prova precisa bater com o pedido.

## 10. Revisão

A revisão olha o artefato real.

Ela passa, falha, pede reparo ou registra risco. Depois a fábrica precisa consumir esse resultado.

Revisão que não muda nada é só comentário.

## 11. Decisão humana

Algumas decisões pertencem ao operador.

Produção, mainnet, fundos, segredos, orçamento, risco residual, release, waiver.

Nesses casos, a fábrica prepara um pacote de decisão. O humano aprova ou bloqueia sabendo exatamente o que está autorizando.

## 12. Fechamento

No fim, a fábrica não escolhe uma palavra bonita. Ela escolhe um estado honesto.

Entregue, se há prova suficiente.

Bloqueado, se falta algo material.

Aprendizado, se a execução mostrou que a fábrica precisa mudar.

Esse é o ciclo. O resto são mecanismos para garantir que ele não vire teatro.

## Nomes internos que você pode encontrar

Se você abrir o workflow compilado, vai ver nomes como `F0 — Pre-Start / Sealed Source Envelope`. Não precisa gostar do nome nem ler isso como copy de produto. Esse nome existe para a máquina e para os testes: ele marca o momento em que a fábrica sela a fonte antes de qualquer interpretação.

A regra de leitura é esta: quando aparecer um nome interno em inglês, traduza mentalmente para a proteção que ele oferece. `Sealed Source Envelope` quer dizer "não destrua a fonte original". `Product SOT` quer dizer "defina a verdade do produto". `Receipt Five` quer dizer "não chame de pronto sem recibo".

## Como ver o workflow interno

Para inspecionar a versão compilada usada pelos testes:

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

Esse comando ajuda maintainers. Para entender o produto, o ciclo acima é o mapa certo.
