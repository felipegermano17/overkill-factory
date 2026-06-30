# Uso

Esta página é o primeiro caminho prático para um checkout local.

## Requisitos

- Python 3.11 ou mais novo.
- Um checkout deste repositório.
- Opcional: runtime Hermes se você quiser execução real com operador/workers. Checks locais do kernel não exigem runtime Hermes vivo.

## Doctor local

```bash
cd factory
python3 scripts/factoryctl.py doctor
```

Um doctor passando checa metadata do pacote, estrutura do repositório, caminho mínimo de exemplo, superfície pública de CLI e prova local de V3 production activation. Ele pode avisar que o runtime Hermes não foi checado. Esse aviso é honesto: validação local não é prova E2E Hermes viva.

## Minimal run

```bash
cd factory
python3 scripts/factoryctl.py run minimal
```

Resultado esperado:

```text
Wrote .tmp/quickstart-result.json
PASS: wrote .tmp/quickstart-result.json
```

Isso prova que o caminho público mínimo consegue materializar um artefato local válido.

## Build do site de documentação

Da raiz do repositório:

```bash
python3 -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-site
```

A documentação nasce para GitHub e já está estruturada para MkDocs.

## Inspecionar o sistema de rotas

```bash
cd factory
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py method-engines
python3 scripts/factoryctl.py operating-systems
```

Use estes comandos quando quiser fatos da superfície executável em vez de prosa.

## Compilar o workflow

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

Isso produz o plano de fases usado pela documentação do ciclo.

## Checks de segurança pública

Antes de alterar docs ou claims públicas, rode pelo menos:

```bash
cd factory
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
```

Se um check falhar, não descreva a superfície pública como pronta. Corrija o mismatch ou reporte a fronteira honestamente.

Saídas geradas em `.tmp/`, snapshots de validação, registros de piloto e provas locais são evidência de execução. Elas não devem ser commitadas como fonte pública, salvo quando um contrato público específico declarar que o artefato faz parte da superfície do repositório.

## Uso com Hermes vivo

Uma execução real exige um runtime Hermes do operador. O kernel público pode preparar e validar contratos, mas cards vivos, workers, comentários, workspaces, evidências e transições vivem no Hermes.

Não trate `doctor` ou `run minimal` como prova de que um produto real foi entregue.
