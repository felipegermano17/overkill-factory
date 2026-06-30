# Manual do Produto

A Overkill Factory existe porque trabalho com agentes muitas vezes parece produtivo antes de estar realmente controlado.

Um fluxo comum com agente pode responder rápido, escrever código rápido e produzir um status convincente rápido. A falha normalmente aparece depois: a fonte foi mal entendida, uma fatia parcial substituiu o produto inteiro, um worker declarou `done` sem prova, um risco virou checklist, ou o operador teve que perceber que o sistema estava parado.

A fábrica transforma esse fluxo frágil em uma linha de produção.

## O que a fábrica é

Overkill Factory é uma camada de método e um kernel público para rodar trabalho de produto com agentes limitados por contratos.

Ela dá forma ao trabalho:

- a fonte é capturada antes de ser interpretada;
- verdade de produto é separada de suposição;
- método é escolhido por contrato, não por impressão;
- workers recebem pacotes limitados;
- cada transição importante precisa de evidência;
- gates humanos continuam humanos;
- bloqueios não humanos são reparados pela fábrica em vez de serem jogados no operador;
- conclusão significa entrega com evidência, não mensagem confiante.

## O que o Hermes controla

Hermes é o chão da fábrica. Ele controla o estado durável de runtime: Kanban, cards, dependências, typed blocks, dispatch de workers, comentários, logs, schedules, workspaces e transições de estado.

A fábrica não deve recriar esse runtime dentro de prompt. Se algo é estado de runtime, o Hermes é a autoridade.

## O que a Overkill Factory controla

A Overkill Factory controla o método de produção em volta do Hermes:

- phase graph;
- route registry;
- method contracts;
- templates e schemas;
- regras de autoridade de worker;
- Product SOT / contratos de verdade de produto;
- expectativas de Product Experience e Product Face;
- gates de segurança, acesso e release;
- regras de evidência e Receipt Five;
- comandos públicos de validação.

A fábrica pode projetar status e preparar pacotes, mas não deve fingir que uma projeção local é o runtime real.

## O que agentes controlam

Agentes são workers limitados. Eles não controlam a rota. Eles não decidem que o produto está pronto. Eles executam um pacote, devolvem evidência e aceitam revisão.

Um worker pode ser forte sem ser confiado cegamente. A fábrica foi desenhada em cima dessa diferença.

## O que humanos controlam

Humanos controlam decisões reais de autoridade: custo, acesso de produção, assinatura, aceite de release, risco material, julgamento de negócio e waivers explícitos.

Um gate humano deve ser raro e claro. Ele não deve obrigar o operador a ler maquinaria interna. Deve apresentar decisão, artefato, evidência, risco e consequências.

## A promessa central

A promessa da fábrica não é "agentes nunca vão falhar". A promessa é: quando agentes falharem, o sistema deve saber onde, por quê, qual evidência falta, se o bloqueio é humano ou não humano e qual é a próxima ação segura.

Essa é a diferença entre teatro autônomo e produção controlada.

## Fronteira pública/privada

Este repositório é o kernel público: código, contratos, testes, exemplos, registries públicos de workers e docs públicas. Uma execução real de produto acontece em um runtime Hermes do operador. Esse runtime pode conter boards privados, fontes privadas, segredos, evidências, decisões de produto e aprovações humanas. Isso não pertence ao GitHub público.
