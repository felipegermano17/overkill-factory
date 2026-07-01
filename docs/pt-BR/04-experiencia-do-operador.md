# Experiência do operador

A Overkill Factory é um produto para operadores, não só um conjunto de scripts.

A pergunta central desta página é: o que a pessoa vê, manda, recebe, aprova e deixa de precisar fiscalizar?

## O que o operador manda

O operador pode mandar pedido, bug, release, incidente, documento, repo, screenshot, decisão ou pergunta de status.

Ele não deveria precisar transformar tudo em ticket perfeito. A fábrica deve conseguir receber matéria-prima e explicar o que ainda falta para virar trabalho seguro.

## Primeira resposta boa

Pedido:

```text
Quero lançar o onboarding novo amanhã.
```

Resposta ruim:

```text
Ok, vou fazer.
```

Resposta boa:

```text
Entendi o objetivo. Antes de executar, preciso confirmar quem entra no fluxo, o que conta como sucesso e se isso toca pagamento, carteira ou dados sensíveis. Já preservei a fonte e vou preparar o pacote de produto.
```

A resposta boa dá controle sem empurrar burocracia.

## Status que presta

Status ruim:

```text
Em andamento.
```

Status bom:

```text
Fonte preservada. Produto definido. Três work units criadas. Duas estão rodando no Hermes. Uma está bloqueada por conflito entre “com KYC” e “sem KYC”. Menor próximo passo: decidir se KYC entra no v1.
```

O operador entende o estado sem abrir dez arquivos.

## Bloqueio bom

Bloqueio bom diz o que falta, por que falta, quem é dono e qual é o menor próximo passo seguro.

Bloqueio ruim diz apenas “aguardando humano”. Isso transfere preguiça da fábrica para o operador.

Nem todo bloqueio é humano. Falta de readback, anexo, worker result, revisão consumida ou evidência válida é trabalho da fábrica.

## Quando o operador age

O operador age quando existe autoridade real: produção, mainnet, fundos, segredos, orçamento, release, waiver, risco residual ou mudança de poder.

Ele não deve agir para suprir bagunça interna.

## O que uma boa pergunta humana contém

Uma boa pergunta humana mostra:

- o que está sendo aprovado;
- o que não está sendo aprovado;
- que prova existe;
- qual risco sobra;
- quais opções existem;
- o que acontece se aprovar;
- o que acontece se recusar.

Isso respeita o humano e preserva a trilha de decisão.

## Como ler um recibo

No fim, o operador deve receber um recibo, não uma declaração confiante.

O recibo diz: pedido, entrega, prova, revisão e pendências. Se algo ficou fora, precisa aparecer. Se há risco aceito, precisa ter dono. Se a entrega é parcial, não pode ser vendida como completa.

## Bridge e inbox

A ponte de operador pode trazer contexto, acordar atenção, registrar decisão e montar handoff. Ela não deve criar board Hermes, fechar gate, executar trabalho da fábrica ou aprovar por conta própria.

Modos como `status_bridge`, `start_bridge`, `question_bridge`, `decision_bridge`, `change_bridge`, `exception_bridge`, `handoff_bridge` e `learnback_forwarding` existem para separar conversa de autoridade. O `factory_bridge_start_request` e a Durable Operator Inbox ajudam a transportar contexto, mas continuam sem autoridade para burlar a Factory.

O perfil `overkill-factory-gerente` conversa com o operador. O worker `factory-orchestrator` continua dono da orquestração. O `default Hermes store` não deve ser usado como alvo implícito quando uma execução real exige board/run explícito. Factory Mechanic remains the self-improvement owner. The bridge cannot execute factory work.
