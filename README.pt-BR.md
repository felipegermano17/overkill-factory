# Overkill Factory

Idioma: [English](README.md) | Portugues

Overkill Factory e um sistema open-source de producao para trabalho agentico de
produto. Ela transforma sinais brutos em estado controlado de fabrica: intake de
fonte, Product SOT, planejamento de escopo completo, roteamento de metodo,
pacotes de worker, gates, evidencia, revisao, readiness de release e learnback.

Ela existe para operadores que querem agentes trabalhando de verdade, sem deixar
chat, entusiasmo ou demo parcial virar fonte de verdade.

Mapa publico:
https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.1.html

## Por Que Existe

Trabalho agentico costuma quebrar nos espacos entre tarefas:

- um paper vira resumo informal;
- uma primeira fatia substitui silenciosamente o escopo completo;
- um worker diz "done" sem evidencia inspecionavel;
- um dashboard parece util, mas nao e a fonte de verdade do runtime;
- um bloqueio espera o operador mesmo quando a fabrica deveria reparar.

Overkill Factory torna esses espacos explicitos. Cada sinal entra por contratos
conhecidos. Cada estado importante tem dono, gate, proxima acao e formato de
evidencia. Bloqueios nao humanos devem voltar para rotas de reparo da propria
fabrica. Human gate continua sendo human gate.

## Como A Fabrica Funciona

O metodo publico e uma linha de producao completa, nao um atalho de MVP:

```text
sinal bruto
-> Universal Signal Intake
-> source ledger e source resolution
-> outcome e discovery
-> Product SOT
-> cobertura completa do Product SOT
-> method contract
-> capability pack e roteamento de risco
-> arquitetura, seguranca e gates de acesso
-> Product Creation Plan e work units
-> pacotes de worker no Hermes
-> execucao, verificacao e revisao independente
-> Receipt Five
-> decisao de release ou bloqueio
-> monitoramento, suporte e learnback
```

A entrada pode ser paper de produto, bug, ideia, repositorio existente,
incidente, pedido de release, pesquisa, UX, analytics, integracao, migracao ou
mudanca em agente/runtime. O route registry e o golden signal corpus tornam
esses caminhos inspecionaveis em vez de escondidos na conversa.

A saida esperada nao e "uma boa resposta". E um produto ou decisao de fabrica
auditavel: o que foi pedido, o que foi planejado, o que bloqueou, o que foi
feito, quem ou o que tinha autoridade, e qual evidencia permite o proximo
estado.

Para trabalho com superficie de produto, a rota tambem precisa criar o contrato
de design system do projeto e o `DESIGN.md` legivel por IA antes de builders de
frontend ou prova de Product Face passarem.

## Runtime Hermes

Hermes e o primeiro chao de fabrica suportado. A fabrica nao substitui o
Hermes; o caminho normal de execucao hoje e Hermes Kanban mais contratos da
Overkill Factory.

Overkill Factory fornece metodo, contratos, schemas, worker registry, bindings
Hermes, adapter hooks, exemplos e ferramentas de validacao. Hermes fornece o
runtime Kanban duravel onde cards, workers, comentarios, runs e transicoes de
estado vivem.

A fronteira pratica e simples:

- `factoryctl`, schemas e testes validam contratos publicos.
- Hermes Kanban e a autoridade de runtime para cards e transicoes reais.
- Receipt Five e resultados de workers sao a evidencia de conclusao.
- Operator Consoles e dashboards de operador podem projetar estado, mas nao aprovam
  gates nem substituem o Hermes.

Velocidade e controlada por autoridade, nao por improviso. Trabalho reversivel
e de baixo risco pode usar a Fast Autonomy Lane, enquanto producao, mainnet,
fundos, assinatura, segredos, billing, acoes destrutivas e aprovacao de human
gate ficam fora de qualquer modo parecido com YOLO. Veja
`docs/operations/fast-autonomy-lane.md`.

## Usar Com O Plugin Bridge Do Codex

Existem dois caminhos publicos de operacao:

- direto: use `factoryctl` e conecte os pacotes gerados ao seu runtime Hermes;
- com ponte: instale o plugin Bridge do Codex para o Codex agir como ponte do
  operador humano.

O plugin nao roda a fabrica. Ele ajuda o operador a coletar o sinal inicial,
iniciar uma run aprovada, ler o Durable Operator Inbox, reportar human gates
pendentes, registrar a resposta do operador e devolver essa resposta para a
fabrica.

Hermes Kanban continua sendo a fonte de verdade. Resultados de workers e
Receipt Five continuam decidindo conclusao. O plugin e apenas a ponte entre o
operador e o runtime.

Instale a partir da raiz do repo:

```bash
codex plugin marketplace add .
codex plugin add overkill-factory-bridge@overkill-factory
```

Depois da instalacao, abra uma nova thread do Codex e revise/confie nos hooks
do plugin. Os hooks rodam quando o Codex inicia ou quando o operador envia um
prompt. Eles nao mantem o Codex ativo 24/7, nao aprovam gates, nao mutam
Hermes, nao rodam workers e nao substituem Receipt Five.

Use a ponte quando quiser pedir status da fabrica, iniciar uma run aprovada,
ver o que esta bloqueado, responder um human gate ou pedir uma mudanca com
escopo definido sem deixar chat virar fonte de verdade.

Leia `docs/operator/overkill-factory-bridge.md` para a arquitetura da ponte e
`docs/operator/overkill-factory-bridge-plugin.md` para instalacao, resolucao do
inbox e confianca dos hooks.

## Primeira Execucao

A partir de um checkout limpo:

```bash
git clone https://github.com/felipegermano17/overkill-factory.git
cd overkill-factory
python -m pip install -e .
factoryctl doctor
factoryctl run minimal
```

A execucao minima escreve saidas locais em `.tmp/`, incluindo o resultado do
quickstart e pacotes de worker para o card publico de exemplo. Pacotes de worker
e gate reports gerados pertencem a `.tmp/`, artefatos de release ou evidence
store privado, nao ao repo publico.

Comandos uteis na sequencia:

```bash
factoryctl init --out ../my-product-factory --project-name my-product
factoryctl route-registry --route-class product_creation
factoryctl intake --route-class product_creation --request-type product_new --signal-type product_paper --summary "Brief publico do produto entra pela rota completa de criacao." --source-ref external:source-card-product-brief --out .tmp/product-intake.json
factoryctl source-resolution --intake .tmp/product-intake.json --intake-ref external:sanitized-product-intake --out .tmp/source-resolution-packet.json
factoryctl source-ledger --source-resolution .tmp/source-resolution-packet.json --source-ref external:source-card-product-brief --out .tmp/product-source-ledger.json
factoryctl outcome-contract --source-ledger .tmp/product-source-ledger.json --out .tmp/outcome-contract.json
factoryctl product-sot --outcome-contract .tmp/outcome-contract.json --out .tmp/product-sot.json
factoryctl full-scope-coverage --product-sot .tmp/product-sot.json --out .tmp/full-product-sot-scope-coverage.json
factoryctl method-contract --full-scope-coverage .tmp/full-product-sot-scope-coverage.json --out .tmp/method-contract.json
factoryctl product-creation-plan --method-contract .tmp/method-contract.json --out .tmp/product-creation-plan.json
factoryctl product-implementation-readiness --product-creation-plan .tmp/product-creation-plan.json --out .tmp/product-implementation-readiness.json
factoryctl ready-work-unit-packets --product-creation-plan .tmp/product-creation-plan.json --product-implementation-readiness .tmp/product-implementation-readiness.json --out .tmp/ready-work-unit-packets
factoryctl validate-ready-work-unit-packets .tmp/ready-work-unit-packets/manifest.json
factoryctl signal-coverage --out .tmp/factory-runs/signal-coverage/factory-signal-coverage-scorecard.json
factoryctl gate-report --card examples/minimal-hermes-project/card.md
factoryctl worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
```

Leia `docs/getting-started/quickstart-hermes.md` e
`docs/getting-started/install-in-hermes.md` para conectar a fabrica ao seu
runtime Hermes.

## Estrutura Do Repositorio

Todo diretorio versionado de topo precisa justificar por que existe, quem abre
primeiro, qual e sua fonte de verdade e como drift e evitado.

| Caminho | Proposito publico |
| --- | --- |
| `.agents/` | Marketplace local de plugins Codex para instalar a ponte. Veja `.agents/README.md`. |
| `.codex/` | Hooks locais do Codex para a ponte de operador. Veja `.codex/README.md`. |
| `.github/` | Workflows, templates, Dependabot e higiene do repositorio. Veja `.github/PROJECT_SURFACE.md`. |
| `adapters/` | Integracoes de runtime, hoje hooks e patches Hermes. Veja `adapters/README.md`. |
| `agents/` | Worker registry, profiles, permissoes, capability packs e bindings Hermes. Veja `agents/README.md`. |
| `docs/` | Guias humanos para onboarding, conceitos, operacao, seguranca e manutencao. Veja `docs/README.md`. |
| `examples/` | Exemplos publicos pequenos e fixtures de fonte para a esteira da fabrica. Veja `examples/README.md`. |
| `fixtures/` | Fixtures publicas minimas de regressao, incluindo validacoes avancadas com formato de produto quando scripts precisam delas. Veja `fixtures/README.md`. |
| `planning-bundles/` | Protocolos public-safe para artefatos candidatos antes da validacao da fabrica. Veja `planning-bundles/README.md`. |
| `plugins/` | Pacotes publicos de plugin Codex, hoje o Overkill Factory Bridge. Veja `plugins/README.md`. |
| `schemas/` | Contratos de maquina para cards, receipts, workers, gates e artefatos publicos. Veja `schemas/README.md`. |
| `scripts/` | CLI, ferramentas de validacao, helpers de prova e checks de manutencao. Veja `scripts/README.md`. |
| `skills/` | Material instalavel de skill Codex para operar a fabrica a partir do clone publico. Veja `skills/README.md`. |
| `templates/` | Contratos iniciais pareados com schemas e testes. Veja `templates/README.md`. |
| `tests/` | Regressao para contratos publicos, docs, adapters e exemplos. Veja `tests/README.md`. |

Pastas locais ignoradas como `.tmp/`, `build/`, `dist/`, `site/` e
`*.egg-info/` nao sao superficie publica de produto.

## Estado Atual De Release

Factory v1 e a linha atual de release do kernel publico; a tag publica mais
recente e v1.3.0. Ela inclui:

- Universal Signal Intake e route registry;
- Golden Corpus e checks de cobertura de sinais;
- Product SOT, planejamento de escopo completo e method contracts;
- worker registry, bindings Hermes e permission classes;
- regras de ativacao de capability packs;
- roteamento Solana AI Kit como cerebro de dominio para trabalho Solana e
  on-chain;
- remote proof e gates R4 para trabalho Solana/on-chain de alto risco;
- docs e pacote do plugin Bridge do Codex para handoff operador-fabrica;
- contratos de Product Face packet/result mais gate de design system do projeto
  / `DESIGN.md`;
- release preflight, public-surface sync e safety scans;
- Factory v1 Completion Gate;
- projecao de artefato de conclusao Hermes e controles de no-idle;
- Hermes update guard para manutencao mais segura do runtime;
- Fast Autonomy Lane para trabalho reversivel rapido sem autoridade YOLO
  global.

Esse claim e deliberadamente limitado. Factory v1 significa que o kernel
publico esta completo o suficiente para instalar, inspecionar, validar e
estender. Um produto criado pela fabrica ainda exige fonte real, Product SOT,
execucao de workers, evidencia, revisoes, human gates e prova de production
readiness propria.

## Leia Depois

- `docs/index.md`: home da documentacao.
- `docs/getting-started/quickstart-hermes.md`: primeira execucao com contexto Hermes.
- `docs/getting-started/install-in-hermes.md`: conectar a fabrica a um runtime Hermes do operador.
- `docs/governance/document-governance.md`: autoridade documental e fronteira publica.
- `docs/reference/cli.md`: comandos suportados do `factoryctl`.
- `docs/concepts/factory-flow.md`: linha de producao e modelo de estado.
- `docs/concepts/overkill-factory-method.md`: guia do metodo.
- `docs/concepts/operator-journey.md`: jornada do operador.
- `docs/visuals/README.md`: fronteira e validacao do mapa visual.
- `agents/README.md`: entrada humana para o diretorio de contratos de workers.
- `docs/agents/worker-profiles.md`: papeis, entradas, saidas e limites dos workers.
- `docs/agents/factory-stage-agent-map.md`: mapa de dono por estagio.
- `docs/agents/capability-packs.md`: regras de cobertura por tipo de produto.
- `docs/control-tower/open-source-setup.md`: setup opcional de Control Tower.
- `docs/operations/validation-and-release.md`: checklist de release.
- `docs/operations/fast-autonomy-lane.md`: limites da execucao autonoma rapida.
- `docs/operations/release-policy.md`: politica de versao e release.
- `docs/operations/troubleshooting.md`: falhas comuns e caminho de recuperacao.
- `docs/architecture/hermes-integration.md`: arquitetura do adapter Hermes.
- `docs/operator/overkill-factory-bridge.md`: arquitetura da ponte Codex/operador.
- `docs/operator/overkill-factory-bridge-plugin.md`: instalacao do plugin Codex e confianca dos hooks.
- `docs/examples/gallery.md`: exemplos publicos.
- `docs/security/oss-security.md`: postura de seguranca.
- `docs/maintenance/repo-surface.md`: regras de manutencao da superficie publica.
- `.agents/README.md`: fronteira do marketplace local de plugins Codex.
- `plugins/README.md`: fronteira dos pacotes publicos de plugin.
- `examples/minimal-hermes-project/README.md`: exemplo minimo executavel.
- `.env.example`: template seguro de variaveis de ambiente.
- `CHANGELOG.md`: historico publico de release.
- `CONTRIBUTING.md`: regras de contribuicao e checks obrigatorios.
- `SECURITY.md`: reporte de seguranca e politica de fronteira publica.

## Validacao

Antes de publicar mudancas publicas:

```bash
python scripts/validate_document_governance.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_worker_profiles.py
python scripts/validate_planning_bundles.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python scripts/validate_public_surface_sync.py --check-published
python -m unittest discover -s tests -q
```

Para readiness de release:

```bash
python scripts/release_integration_preflight.py
python scripts/worktree_release_inventory.py
factoryctl v1-completion-gate --github-actions-result PASS --open-v1-blockers 0 --open-prs 0
```

O mapa publico e validado por `scripts/validate_public_surface_sync.py`. O
script compara o HTML versionado com o objeto publicado no GCS e verifica que o
visual nao reivindica autoridade de runtime.

## Fronteira Publica

O repositorio e uma superficie publica de produto. Ele nao deve conter segredos,
evidencia privada crua, links privados de board, caminhos absolutos locais,
dumps de fonte privada, screenshots de runs privados, pacotes de worker
gerados, arquivos historicos de prova ou autoridade derivada de chat.

Historico narrativo de validacao, notas antigas tratadas como prova e trilhas
internas de auditoria nao pertencem ao onboarding publico. O onboarding publico
deve apontar para contratos atuais, exemplos executaveis, validadores e guias
curtos para operador.

Hermes e Receipt Five continuam sendo a fonte de verdade da execucao real da fabrica.
Este repo documenta e valida o kernel da fabrica; ele nao e deposito de
historico privado de runtime.

## Licenca

MIT.
