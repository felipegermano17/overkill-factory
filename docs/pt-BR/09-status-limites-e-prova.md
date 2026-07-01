# Status, limites e prova

Esta página separa contrato público, prova local, runtime vivo e entrega real.

## O que o repo público prova

O repo público prova que existe um kernel verificável: workflow compilado, route classes, method engines, operating-system areas, schemas, templates, worker registries, scripts, fixtures, exemplos, docs e testes.

No checkout atual, os registries expõem 26 compiled phases, 14 route classes, 8 method engines, 17 operating-system areas e 40 public workers. O filesystem atual contém 249 JSON schemas, 161 JSON templates e 101 test files.

Esses números devem ser atualizados por ferramenta, não por palpite.

## O que documentação prova

Documentação prova o contrato explicado e a navegação pública. Ela não prova execução privada.

## O que o mapa visual prova

O mapa visual é suporte conceitual. Ele ajuda a entender a fábrica. Ele não é fonte de verdade de runtime, não prova entrega e não substitui Hermes.

## O que teste local prova

Teste local prova coerência do checkout. `factoryctl doctor` e `factoryctl run minimal` indicam que o kernel público está operacional localmente.

Isso não prova que um board real rodou, que worker atual entregou, que revisão foi consumida ou que humano aprovou.

## O que Hermes vivo prova

Hermes vivo prova estado de runtime: cards, transições, dependências, anexos, comentários e workers naquele ambiente.

Mesmo isso ainda precisa de evidência e Receipt Five para virar conclusão.

## O que worker result prova

Worker result prova que um worker devolveu algo dentro de um escopo. A fábrica ainda precisa readback, revisão e reconciliação.

## O que Receipt Five prova

Receipt Five prova que pedido, entrega, prova, revisão e pendências foram reconciliados. Se gate humano era obrigatório, precisa apontar decisão humana real.

## Claims proibidas

Não diga que docs públicas provam runtime. Não diga que mapa prova produção. Não diga que teste local prova entrega. Não diga que arquivo criado prova readback. Não diga que aprovação genérica prova mainnet.
