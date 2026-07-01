# Ciclo simples

A máquina tem um workflow detalhado. Você não precisa começar por ele.

O workflow compilado é a fonte factual para a máquina. Para entender o produto, o mapa humano é mais simples:

```text
pedido -> fonte -> entendimento -> verdade do produto -> caminho -> trabalho pequeno -> Hermes -> prova -> revisão -> decisão humana -> entrega, bloqueio ou aprendizado
```

## Pedido

Tudo começa com um sinal: frase, bug, repo, documento, incidente, tela, release ou decisão.

Nesse momento a fábrica ainda não sabe o suficiente. Executar direto seria chute.

## Fonte

A fonte é preservada antes do resumo.

Isso protege o pedido original contra uma primeira interpretação ruim. Se a fonte longa vira resumo curto cedo demais, a fábrica pode construir em cima de um erro.

O nome interno que aparece no workflow é `F0 — Pre-Start / Sealed Source Envelope`. Esses nomes existem para a máquina e para os testes, não para vender o produto. Leia como: selar a fonte antes de mexer nela.

## Entendimento

A fábrica separa fato, inferência, decisão, conflito e lacuna.

A saída humana deveria ser clara: isto sabemos, isto parece provável, isto foi decidido, isto conflita, isto falta.

Se esse entendimento está fraco, avançar é aposta.

## Verdade do produto

Agora a fábrica define o que será construído.

Qual produto? Para quem? Com que escopo? Fora de que escopo? Com que risco? Que prova encerra a discussão?

O nome interno é Product SOT. A tradução útil é: verdade do produto.

## Caminho

Com a verdade do produto na mesa, a fábrica escolhe rota e método.

Bug, release, incidente, segurança, interface, documentação, agente, integração e Solana não pedem a mesma prova.

A rota escolhe a régua. O método escolhe como provar.

## Trabalho pequeno

O produto vira unidades executáveis.

Cada unidade precisa de entrada, saída, dono, dependência, prova, reviewer e regra de pronto.

Sem isso, o agente recebe uma intenção, não uma tarefa.

## Hermes

Hermes é o chão vivo da execução.

Cards, dependências, workers, comentários, anexos, bloqueios e transições precisam aparecer ali. A Factory não deve manter um estado paralelo escondido.

## Prova

Cada worker devolve evidência adequada ao tipo de trabalho.

Código pede teste, diff, build ou scan. Interface pede superfície. CLI pede transcript. Release pede prontidão e rollback. Docs pedem clareza e caminho de uso.

A prova precisa bater com o pedido.

## Revisão

A revisão olha o artefato real.

Se passa, destrava. Se falha, cria reparo. Se encontra risco, registra dono e decisão. Se não muda nada, não foi consumida.

## Decisão humana

Algumas decisões pertencem ao operador: produção, mainnet, fundos, segredos, orçamento, release, waiver, risco residual.

Nesses casos, a fábrica prepara pacote de decisão. O humano não aprova no escuro.

## Fechamento

No fim, a fábrica escolhe um estado honesto.

Entregue, se há prova suficiente.

Bloqueado, se falta algo material.

Aprendizado, se a execução revelou que a própria fábrica precisa mudar.

Esse ciclo é simples de ler e difícil de cumprir. O valor da Factory está em cumprir mesmo quando seria mais fácil dizer "pronto".

## Para maintainers

O workflow compilado continua existindo para validação, testes e manutenção. Para inspecionar:

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```
