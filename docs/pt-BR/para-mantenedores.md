# Para mantenedores

## Mapa

A raiz do repositório contém as entradas públicas, a licença, a configuração geral e a pasta `docs/`. A pasta `docs/` contém a documentação pública escrita para humanos, catálogos públicos e manifestos. A pasta `factory/` contém a superfície executável: scripts, schemas, templates, agents, testes, exemplos, fixtures e docs internas ou legadas.

```text
README.md
README.pt-BR.md
docs/
factory/
```

## Documentação

A documentação canônica em português fica em `docs/pt-BR/`:

```text
index.md
manual.md
linha-de-producao.md
uso.md
para-mantenedores.md
```

`index.md` é entrada curta. `manual.md` explica a fábrica como sistema. `linha-de-producao.md` descreve o funcionamento etapa por etapa. `uso.md` ensina comandos locais e fronteiras de prova. `para-mantenedores.md` concentra manutenção.

Não crie `trust-and-evidence.md`. Evidência deve aparecer dentro da linha de produção e dentro das etapas que mudam estado. Não crie `technical-model.md`. Conteúdo técnico de manutenção deve ficar neste arquivo.

## Factory

`factory/` contém a parte executável. Scripts leem schemas, templates, registries, examples e docs públicas. Testes verificam se as claims públicas continuam compatíveis com a superfície executável.

Áreas importantes:

- `factory/scripts/`: comandos e validadores;
- `factory/schemas/`: formatos esperados para artefatos;
- `factory/templates/`: exemplos e contratos editáveis;
- `factory/agents/`: workers, profiles, bindings e permissões;
- `factory/examples/`: cards e fluxos mínimos;
- `factory/tests/`: regressões que protegem contratos;
- `factory/legacy-docs/`: material histórico preservado, não canônico.

## Contratos

Schemas, templates, registries e regras são contratos de produção. Eles definem quais campos existem, quais estados são aceitos, quais workers podem aparecer, quais rotas e métodos são conhecidos e que validação local consegue provar.

Uma explicação humana não deve prometer mais do que esses contratos mostram. Se a documentação diz que a fábrica registra decisão humana, deve existir contrato, script, teste ou exemplo que mostre essa forma de registro. Se a documentação diz que local proof não é runtime proof, os testes devem proteger essa fronteira.

## Comandos

`factoryctl` é a superfície executável principal para inspeção e prova local. Use o arquivo diretamente quando quiser evitar ambiguidade de ambiente:

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py method-engines
python3 scripts/factoryctl.py operating-systems
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
python3 scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md
python3 scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python3 scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
```

Esses comandos leem o checkout local. Eles geram saída local, validam contratos e ajudam a inspecionar a linha. Eles não substituem worker executando em Hermes vivo.

## Testes

Testes e validadores protegem a relação entre documentação, contrato e execução. Eles devem verificar estrutura dos docs, ausência de copy de produto, comandos de uso, fronteiras de claim, existência de refs públicas, schema dos manifestos, sincronização do mapa público e coerência do promise map.

Comandos úteis:

```bash
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/generate_factory_reference_docs.py --check
python3 -m unittest tests.test_open_source_docs -q
```

Para site:

```bash
cd ..
python3 -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-site
```

## Geração

Algumas saídas podem ser geradas automaticamente: catálogos, inventários, listas completas, referências de schemas, tabelas extensas e saídas derivadas de registries. Essas saídas ajudam a manter cobertura, mas não devem substituir explicação humana.

Devem ser escritos manualmente: manual, linha de produção, explicações humanas, fronteiras de claim e instruções de uso. Esses textos precisam mostrar entrada, transformação, estado, artefato, Hermes, evidência, revisão, decisão quando aplicável, bloqueio, retomada e saída para próxima etapa.

## Mudanças

Uma mudança sólida normalmente atualiza três camadas:

1. explicação humana;
2. contrato executável;
3. teste, validador ou prova local.

Se uma nova rota entra, atualize registry, docs e teste. Se um novo worker entra, atualize profile, binding, worker registry, docs de manutenção e teste. Se uma claim muda, atualize manifest, promise map e fronteira no texto. Se a estrutura pública muda, atualize MkDocs, pyproject, manifest, testes e refs internas.

## Fronteiras

Documentação não pode prometer mais do que a superfície executável mostra.

Saída local não é execução viva. Worker profile não é worker executando. Arquivo existente não é evidência consumida. Revisão sem efeito de estado não fecha ciclo. Decisão humana não deve ser inventada. Claim pública precisa declarar seu limite.

Quando houver dúvida, escreva menos promessa e mais funcionamento: o que entra, que transformação acontece, que artefato muda, onde aparece no Hermes, que evidência sustenta avanço, quem revisa, quem decide e como o ciclo fecha ou bloqueia.
