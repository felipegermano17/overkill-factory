# Overkill Factory

Idioma: [English](README.md) | Português

A Overkill Factory é uma fábrica de produto para trabalho com agentes em cima do Hermes.

Ela transforma um sinal bruto de produto em estado controlado de fábrica: intake de fonte, source ledger, verdade de produto, method contract, work units limitadas, execução por workers no Hermes, evidência, revisão, release ou bloqueio e learnback.

A versão curta:

```text
Hermes roda o chão da fábrica.
Overkill Factory define o método de produção e os checks.
Agentes executam trabalho limitado.
Humanos decidem gates humanos reais.
Evidência decide se o trabalho pode avançar.
```

## Leia a documentação

A documentação pública foi reescrita como manual de produto em vez de arquivo técnico disperso.

- [English documentation](docs/en/index.md)
- [Documentação em português](docs/pt-BR/index.md)
- [Mapa visual público](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)

Hermes e Receipt Five continuam sendo a fonte de verdade para claims de conclusão em runtime: o mapa e o manual explicam a fábrica; eles não provam que um produto foi entregue.

As docs públicas antigas foram preservadas em `factory/legacy-docs/` apenas por compatibilidade histórica. Elas não são a fonte canônica de verdade.

## Primeiro teste local

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Um teste local passando significa que o kernel público está coerente. Não prova que um runtime Hermes real de operador entregou um produto específico.

## Estrutura do repositório

```text
README.md              entrada pública em inglês
README.pt-BR.md        entrada pública em português
docs/                  documentação pública canônica e catálogos públicos
factory/               implementação, schemas, templates, workers, testes, exemplos, docs legadas
```

Dentro de `factory/`, as áreas públicas importantes são `agents/`, `examples/`, `fixtures/`, `schemas/`, `scripts/`, `skills/`, `templates/` e `tests/`.

Worker packets e gate reports gerados pertencem a `.tmp/`, não à documentação pública.

## Fatos do kernel público

Este repositório atualmente expõe:

- 26 fases compiladas da fábrica;
- 14 classes de rota;
- 8 method engines;
- 17 áreas de operating system;
- 40 workers públicos;
- 244 schemas JSON;
- 156 templates JSON;
- 97 testes.

A fonte factual do comportamento atual é a superfície executável em `factory/`, especialmente `factory/scripts/factoryctl.py`, `factory/schemas/`, `factory/templates/`, `factory/agents/` e `factory/tests/`.
