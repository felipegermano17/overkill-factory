# Workers e unidades de trabalho

Worker bom não recebe “faz o produto”. Recebe uma unidade limitada com fonte, escopo, autoridade e prova.

## Por que isso importa

Agente autônomo com missão nebulosa expande escopo, escolhe atalhos e confunde intenção com tarefa. A Factory transforma o pedido em unidades pequenas para permitir autonomia sem entregar a chave inteira.

## Unidade boa

Uma unidade boa tem:

- entrada;
- saída;
- dono;
- dependência;
- prova exigida;
- reviewer;
- regra de pronto;
- limite de autoridade.

Unidade ruim diz apenas:

```text
Construa o onboarding.
```

## Worker Packet

Worker Packet é a tarefa entregue ao worker.

Exemplo:

```text
Tarefa: corrigir bug no checkout vazio.
Fonte: issue #123 e reprodução local.
Escopo: somente checkout vazio.
Fora de escopo: pricing, payment provider, auth.
Prova: teste falha antes, passa depois.
Autoridade: pode editar checkout e teste; não pode mudar cobrança.
```

## Worker Result

Worker Result é o retorno estruturado do worker.

Ele precisa dizer o que fez, que prova gerou, que arquivo mudou, que teste rodou, se há bloqueio, que risco sobra e se existe handoff para outro worker.

## Autoridade

Worker não decide release, mainnet, fundos, segredo, waiver ou risco residual. Worker também não revisa o próprio trabalho quando o risco é material.

## Especialistas

Alguns workers são genéricos. Outros cobrem segurança, supply chain, Product Face, evidence reconciliation, source ledger, QA, remote proof, handoff e human gate support.

A escolha do worker deve vir da rota/método, não da preferência do agente.

## Falhas comuns

- planner fingir prova de implementação;
- builder aprovar o próprio resultado;
- reviewer não ler artefato;
- worker entregar arquivo sem evidência;
- capability pack ser assumido sem cobertura;
- resultado não ser consumido pelo grafo.

## Como vira aprendizado

Quando um worker falha de forma recorrente, a Factory deve promover aprendizado: teste novo, skill nova, schema, gate, doc, issue ou mudança de processo. Learnback não é comentário solto; é melhoria com prova.
