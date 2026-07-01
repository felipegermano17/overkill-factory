# Referência do repositório

Esta página reúne os fatos curtos para quem já entendeu o produto e precisa achar coisas no repo.

## Raiz

- `README.md`: entrada pública em inglês.
- `README.pt-BR.md`: entrada pública em português.
- `docs/`: documentação pública canônica e catálogos públicos.
- `factory/`: implementação, scripts, schemas, templates, agents, tests, examples, fixtures, skills e legacy docs.

## docs/

- `docs/en/`: documentação pública em inglês.
- `docs/pt-BR/`: documentação pública em português.
- `docs/factory-workflow.catalog.json`: workflow público compilado.
- `docs/promise-implementation-map.public.json`: mapa de promessa para implementação.
- `docs/public-surface.manifest.json`: manifest das superfícies públicas.
- `docs/assets/public-map/`: mapa visual público.

## factory/

- `factory/scripts/factoryctl.py`: principal CLI pública.
- `factory/schemas/`: contratos JSON.
- `factory/templates/`: templates e registries.
- `factory/agents/`: workers, profiles, bindings e permission classes.
- `factory/tests/`: regressões.
- `factory/examples/`: exemplos seguros.
- `factory/fixtures/`: fixtures públicas e negativas.
- `factory/legacy-docs/`: histórico preservado, não canônico.

## Classes de rota

Route classes são IDs de contrato. Não traduza IDs quando usados como IDs. `product_creation` é um exemplo: ele deve aparecer assim no contrato, mesmo quando a explicação estiver em português.

## Registries principais

- `factory/templates/factory-route-registry.json`: route classes.
- `factory/templates/method-engine-registry.json`: method engines.
- `factory/templates/factory-operating-system-registry.json`: operating-system areas.
- `factory/agents/worker-registry.public.json`: workers públicos.

## Onde não colocar coisas

Não coloque outputs gerados em docs públicas. Worker packets, gate reports, evidence archives e resultados privados pertencem a `.tmp` ou a store própria de runtime, nunca à documentação canônica.
