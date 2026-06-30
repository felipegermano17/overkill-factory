# Uso

Esta página é o caminho prático para um checkout local. Ela não finge que um checkout local é a mesma coisa que um runtime Hermes vivo, do operador. Primeiro ela dá uma prova segura. Depois mostra os checks que deveriam rodar antes de mexer em documentação pública ou em claims públicas.

## Requisitos

Você precisa de Python 3.11 ou mais novo e de um checkout do repositório. Um runtime Hermes vivo é opcional para validar o kernel local. Ele só vira obrigatório quando você quer execução real com operador e workers.

## Doctor local

```bash
cd factory
python3 scripts/factoryctl.py doctor
```

Um doctor passando checa metadata do pacote, estrutura do repositório, exemplo mínimo, superfície pública de CLI e prova local de ativação V3. O comando pode avisar que o runtime Hermes não foi checado. Esse aviso está certo: validação local não é prova E2E Hermes viva.

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

Isso prova que o caminho público mínimo consegue escrever um artefato local válido. Não prova que um produto real foi entregue.

## Inspecione a fábrica em vez de chutar

Use os registries executáveis quando quiser fatos:

```bash
cd factory
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py method-engines
python3 scripts/factoryctl.py operating-systems
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

Esses comandos são melhores do que ler prosa antiga, porque vêm da superfície real de implementação.

## Build do site de documentação

Da raiz do repositório:

```bash
python3 -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-site
```

O site é pequeno de propósito: inglês, português e assets públicos. O arquivo técnico antigo fica em `factory/legacy-docs/` e não faz parte da navegação principal.

## Checks de segurança pública

Antes de alterar docs públicas ou claims públicas, rode:

```bash
cd factory
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
python3 scripts/generate_factory_reference_docs.py --check
```

`validate_public_surface_sync.py` checa se as superfícies públicas continuam alinhadas ao manifest. `validate_promise_implementation_map.py` checa se promessas públicas ainda têm referência de implementação e fronteira. `public_safety_scan.py` e `secret_safety_scan.py` protegem a fronteira pública do repositório.

Se um check falhar, não descreva a superfície pública como pronta. Corrija a divergência ou explique a fronteira honestamente.

Saídas geradas em `.tmp/`, snapshots de validação, registros de piloto e provas locais são evidência de execução. Elas não devem ser commitadas como fonte pública, salvo quando um contrato público específico declarar que o artefato faz parte do repositório.

## Validação local completa

Para uma passada local mais profunda:

```bash
cd factory
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

É mais pesado do que o smoke público, mas é o check certo antes de uma mudança ampla em docs ou contratos.

## Uso com Hermes vivo

Uma execução real exige um runtime Hermes do operador. O kernel público pode preparar contratos e validar caminhos locais de prova, mas cards vivos, workers, comentários, workspaces, evidências e transições vivem no Hermes.

Não trate `doctor` ou `run minimal` como prova de que um produto foi entregue. Trate como prova de que este checkout está coerente o bastante para começar.
