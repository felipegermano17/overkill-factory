# Validação e referência do repositório

Validação local é necessária. Mas validação local não é prova E2E Hermes viva.

Ela prova que o checkout está coerente, que catálogos públicos batem com schemas, que docs constroem, que scans públicos passam e que testes locais protegem contratos.

## Requisitos

Use Python 3.11 ou mais novo. Rode os comandos a partir de `factory/`, salvo quando o comando indicar o root do repo.

## Doctor

```bash
cd factory
python3 scripts/factoryctl.py doctor
```

Prova que a superfície básica do kernel está legível. Não prova entrega real.

## Minimal run

```bash
python3 scripts/factoryctl.py run minimal
```

Resultado esperado inclui `Wrote .tmp/quickstart-result.json` e `PASS: wrote .tmp/quickstart-result.json`.

Arquivos em `.tmp` são saída gerada e must not be committed.

## Validadores públicos

```bash
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
python3 scripts/generate_factory_reference_docs.py --check
```

`validate_public_surface_sync.py` confere manifest, frases obrigatórias, links e fronteiras públicas. `public_safety_scan.py` evita claims públicas perigosas. `secret_safety_scan.py` evita vazamento.

## MkDocs

```bash
cd ..
python3 -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-check
```

Prova navegação e build da documentação. Não prova qualidade editorial sozinho.

## Suíte de testes

```bash
cd factory
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

A suíte pode imprimir fixtures negativas esperadas. O que importa é o status final.

## Como interpretar falhas

Falha de manifest geralmente significa página faltando, frase obrigatória ausente, source_ref inexistente ou claim pública exagerada.

Falha de schema significa contrato JSON quebrado.

Falha de docs build significa navegação, link ou Markdown incompatível com MkDocs strict.

Falha de worker profile significa registry/profile/binding/permission fora de sincronia.

## Quando precisa Hermes vivo

Precisa Hermes vivo para afirmar execução real, worker atual, runtime state, decisão operacional ou entrega privada. Local validation is not live Hermes E2E proof.


---

## Referência do repositório

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
