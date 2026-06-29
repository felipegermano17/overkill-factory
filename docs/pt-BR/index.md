# Documentação da Overkill Factory

A Overkill Factory é um sistema de produção para trabalho de produto com agentes.

Ela existe para transformar um sinal inicial — ideia, repo, bug, documento, incidente ou pedido de release — em trabalho controlado: definição de produto, método, grafo Hermes, workers especializados, evidência, revisão, decisão humana quando precisa e Receipt Five no fechamento.

A ideia simples:

```text
Você manda o sinal inicial.
O gerente transforma isso em uma run controlada.
A fábrica separa fonte, suposição e decisões em aberto.
A definição de produto / PRD vira o alvo.
O método define gates e evidências.
O Hermes guarda e executa o grafo durável.
Workers produzem resultados limitados.
A fábrica verifica evidência e repara gaps recuperáveis.
O gerente chama você só para decisões humanas reais.
Receipt Five fecha o trabalho com honestidade.
```

## Ordem recomendada

1. [Manual da fábrica](manual-da-fabrica.md)
2. [Como funciona](como-funciona.md)
3. [Experiência do operador](experiencia-do-operador.md)
4. [Definição de produto / PRD](definicao-de-produto.md)
5. [Processo](processo.md)
6. [Runtime e estado](runtime-e-estado.md)
7. [Autonomia](autonomia.md)
8. [Método, gates e workers](metodo-gates-workers.md)
9. [Evidência e Receipt Five](evidencia-e-receipt-five.md)
10. [Segurança e release](seguranca-e-release.md)
11. [Instalação e uso](instalacao-e-uso.md)
12. [Estrutura do repositório](estrutura-do-repositorio.md)
13. [Examples e fixtures](examples-e-fixtures.md)
14. [Terminologia](terminologia.md)
15. [Status de implementação](status-de-implementacao.md)

## Fonte de verdade

Hermes e Receipt Five continuam sendo a fonte de verdade para estado de runtime e fechamento com evidência.

Mapa público: https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html

## O que esta documentação não é

Ela não é arquivo de estudo interno. Não é dump de artefato gerado. Não é documentação antiga movida para parecer nova.

A documentação pública explica o produto. Material técnico antigo fica separado em `factory/legacy-docs/` somente quando ainda tem valor técnico, de compatibilidade, teste ou migração.
