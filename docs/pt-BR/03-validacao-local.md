# Validação local

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
