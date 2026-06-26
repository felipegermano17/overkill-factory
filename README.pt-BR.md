# Overkill Factory

Idioma: [English](README.md) | Português

Overkill Factory é uma linha de produção para trabalho de produto feito por
agentes em cima do Hermes. Ela transforma um pedido bruto em estado controlado
de fábrica: intake de fonte, confirmação de entendimento, Product SOT,
cobertura completa do Product SOT, roteamento de método, pacotes de worker,
gates, evidência, revisão, readiness de release e learnback.

Ela existe para operadores que querem agentes trabalhando com velocidade sem
deixar chat, entusiasmo ou demo parcial virar fonte de verdade.

Mapa público:
https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.1.html

## Explicação Simples

A Overkill Factory é uma linha de produção para projetos feitos por agentes.

Em vez de você pedir "faz um app" e um agente sair codando no improviso, a
fábrica transforma sua ideia em um processo controlado: entende o material,
confirma o entendimento, planeja, divide o trabalho, chama agentes
especialistas, cobra provas, revisa, bloqueia riscos e só então considera algo
pronto.

Em termos simples:

- **Hermes** é o chão da fábrica: o quadro de tarefas, os cards, os agentes
  rodando, os status e os logs.
- **Overkill Factory** é o método: regras, etapas, contratos, gates, workers,
  evidências e validações.
- **Gerente da fábrica** é a porta de entrada: você fala com ele, por exemplo no
  Telegram.
- **Workers** são agentes especialistas: produto, arquitetura, frontend,
  backend, segurança, Solana, QA, documentação, release etc.
- **Gates** são checkpoints: pode avançar, tem prova, precisa de decisão humana?
- **Receipt Five** é o recibo final: o pacote de evidências que diz o que foi
  feito, testado, revisado e aprovado/bloqueado.

O fluxo normal é:

```text
sua ideia/material
-> entendimento do produto
-> confirmação com você
-> fonte da verdade do produto
-> plano completo
-> tarefas para agentes
-> execução
-> testes e revisão
-> aprovação/bloqueio
-> entrega com evidências
-> aprendizados para melhorar a fábrica
```

O ponto mais importante: a fábrica não é "um chat inteligente". Ela é um
sistema para impedir que agentes pulem entendimento, inventem escopo, ignorem
segurança ou digam que algo está pronto sem prova.

## Por Que Existe

Trabalho feito por agentes costuma quebrar nos espaços entre tarefas:

- um paper vira resumo informal;
- uma primeira fatia substitui silenciosamente o escopo completo;
- um worker diz "done" sem evidência inspecionável;
- um dashboard parece útil, mas não é a fonte de verdade do runtime;
- um bloqueio espera o operador mesmo quando a fábrica deveria reparar.

Overkill Factory torna esses espaços explícitos. Cada sinal entra por contratos
conhecidos. Cada estado importante tem dono, gate, próxima ação e formato de
evidência. Bloqueios não humanos devem voltar para rotas de reparo da própria
fábrica. Gate humano continua sendo decisão humana.

## Como A Fábrica Funciona

O método público é uma linha de produção em etapas para trabalho de produto controlado:

```text
sinal bruto
-> Universal Signal Intake
-> source ledger e source resolution
-> confirmação de entendimento com o operador
-> outcome e discovery
-> Product SOT
-> cobertura completa do Product SOT
-> method contract
-> capability pack e roteamento de risco
-> arquitetura, segurança e gates de acesso
-> Product Creation Plan e work units
-> pacotes de worker no Hermes
-> execução, verificação e revisão independente
-> Receipt Five
-> decisão de release ou bloqueio
-> monitoramento, suporte e learnback
```

A entrada pode ser paper de produto, bug, ideia, repositório existente,
incidente, pedido de release, pesquisa, UX, analytics, integração, migração ou
mudança em agente/runtime. O route registry e o golden signal corpus tornam
esses caminhos inspecionáveis em vez de escondidos na conversa.

A saída esperada não é "uma boa resposta". É um produto ou decisão de fábrica
auditável: o que foi pedido, o que foi planejado, o que bloqueou, o que foi
feito, quem tinha autoridade e qual evidência permite o próximo estado.

Trabalho com superfície de produto também precisa criar o contrato de design
system do projeto e o `DESIGN.md` legível por IA antes de builders de frontend
ou prova de Product Face passarem.

## Operating Systems Da Fábrica

As áreas críticas da fábrica ficam agrupadas em um registry canônico de
Operating Systems. Isso impede que a fábrica vire um conjunto de contratos
espalhados sem dono operacional.

Inspecione com:

```bash
factoryctl operating-systems
factoryctl validate-operating-systems templates/factory-operating-system-registry.json
factoryctl operating-system-scorecard --runtime-proof .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json
```

O registry cobre Product Truth and Research, Method, Authority and Autonomy,
Hermes Worker Runtime, Evidence and Product Proof, Capability and Domain Packs,
Operator Experience, Security and Release, Product Quality, Velocity and Cost e
Factory Learning.

Uma OS declara worker dono, issue, contratos, regras de falha fechada,
fronteira de runtime e provas exigidas. Ela não afirma que um produto está
pronto para produção. Produção ainda exige estado Hermes, resultados de
workers, Receipt Five, prova específica do produto e gates humanos quando o
risco exigir.

A prova runtime do Hermes é public-safe e redigida: ela prova gateway, auth do
Codex, Telegram, perfil gerente, conclusão de worker e bloqueio de human gate
sem publicar conteúdo privado do board. Ela prova a espinha operacional da
fábrica, não o release de um produto específico.

O Method OS também tem um registry de method engines:

```bash
factoryctl method-engines
factoryctl validate-method-engines templates/method-engine-registry.json
```

O Method Contract precisa ligar os métodos escolhidos a engines como spec-first
SDD, test-first TDD, behavior-first BDD, discovery/research, security-first,
design-first, legacy diagnosis ou incident-first. Nome de método sozinho não
autoriza execução.

## Runtime Hermes

Hermes é o primeiro chão de fábrica suportado. A Overkill Factory não substitui
o Hermes; o caminho normal de execução hoje é Hermes Kanban mais contratos da
Overkill Factory.

Overkill Factory fornece método, schemas, worker registry, bindings Hermes,
adapter hooks, exemplos e ferramentas de validação. Hermes fornece o runtime
Kanban durável onde cards, workers, comentários, runs e transições de estado
vivem.

A fronteira de runtime é simples:

- `factoryctl`, schemas e testes validam contratos públicos.
- Hermes Kanban continua sendo a fonte de verdade para cards e transições reais.
- Resultados de workers e Receipt Five são a evidência de conclusão.
- Consoles e dashboards de operador podem projetar estado, mas não aprovam gates
  nem substituem o Hermes.

Velocidade é controlada por autoridade, não por improviso. Trabalho reversível
e de baixo risco pode usar a Fast Autonomy Lane. Produção, mainnet, fundos,
assinatura, segredos, billing, ações destrutivas e aprovação de human gate ficam
fora de qualquer modo parecido com YOLO. Veja
`docs/operations/fast-autonomy-lane.md`.

Hermes e Receipt Five continuam sendo a fonte de verdade da execução real da
fábrica.

## Formas De Usar

Existem três caminhos práticos de operação:

| Caminho | Use quando | O que acontece |
| --- | --- | --- |
| `factoryctl` | Você quer inspecionar, validar ou gerar pacotes localmente. | A CLI escreve artefatos public-safe em `.tmp/`. Ela não muda um board Hermes real. |
| Hermes runtime | Você quer a fábrica rodando cards e workers reais. | Hermes Kanban possui cards, workers, comentários, runs e transições. |
| Plugin Bridge do Codex | Você quer o Codex como ponte do operador humano. | Codex lê o Durable Operator Inbox e encaminha decisões sem virar a fábrica. |

O bridge não roda a fábrica. Ele ajuda a coletar o sinal inicial, iniciar uma
run aprovada, ler eventos pendentes do operador, mostrar human gates, registrar
a resposta do operador e devolver essa resposta para a fábrica.

Instale o plugin Bridge do Codex a partir da raiz do repo:

```bash
codex plugin marketplace add .
codex plugin add overkill-factory-bridge@overkill-factory
```

Leia `docs/operator/overkill-factory-bridge.md` para a arquitetura da ponte e
`docs/operator/overkill-factory-bridge-plugin.md` para instalação, resolução do
inbox e confiança dos hooks.

## Primeira Execução

A partir de um checkout limpo:

```bash
git clone https://github.com/felipegermano17/overkill-factory.git
cd overkill-factory
python -m pip install -e .
factoryctl doctor
factoryctl run minimal
```

A execução mínima escreve saídas locais em `.tmp/`, incluindo o resultado do
quickstart e pacotes de worker para o card público de exemplo. Pacotes de worker
e gate reports gerados pertencem a `.tmp/`, artefatos de release ou evidence
store privado, não ao repo público.

Crie um workspace de produto quando estiver pronto para conectar o método ao
seu próprio material:

```bash
factoryctl init --out ../my-product-factory --project-name my-product
factoryctl operator-interface --primary-interface telegram --out .tmp/operator-interface-profile.json
factoryctl validate-operator-interface .tmp/operator-interface-profile.json
factoryctl start-conversation --operator-interface .tmp/operator-interface-profile.json --source-envelope-ref external:operator-source-envelope --out .tmp/factory-start-conversation.json
factoryctl validate-start-conversation .tmp/factory-start-conversation.json
factoryctl intake --route-class product_creation --request-type product_new --signal-type product_paper --summary "Brief público do produto entra em resolução de fontes e confirmação de entendimento." --source-ref external:source-card-product-brief --out .tmp/universal-signal-intake.json
factoryctl validate-signal-intake .tmp/universal-signal-intake.json
```

Leia `docs/getting-started/quickstart-hermes.md` e
`docs/getting-started/install-in-hermes.md` antes de conectar pacotes gerados a
um runtime Hermes do operador.

## Estrutura Do Repositório

Todo diretório versionado de topo precisa justificar por que existe, quem abre
primeiro, qual é sua fonte de verdade e como drift é evitado.

| Caminho | Propósito público |
| --- | --- |
| `.agents/` | Marketplace local de plugins Codex para instalar a ponte. Veja `.agents/README.md`. |
| `.codex/` | Hooks locais do Codex para a ponte de operador. Veja `.codex/README.md`. |
| `.github/` | Workflows, templates, Dependabot e higiene do repositório. Veja `.github/PROJECT_SURFACE.md`. |
| `adapters/` | Integrações de runtime, hoje hooks e patches Hermes. Veja `adapters/README.md`. |
| `agents/` | Worker registry, profiles, permissões, capability packs e bindings Hermes. Veja `agents/README.md`. |
| `docs/` | Guias humanos para onboarding, conceitos, operação, segurança e manutenção. Veja `docs/README.md`. |
| `examples/` | Exemplos públicos pequenos e fixtures de fonte para a esteira da fábrica. Veja `examples/README.md`. |
| `fixtures/` | Fixtures públicas mínimas de regressão, incluindo validações avançadas com formato de produto. Veja `fixtures/README.md`. |
| `planning-bundles/` | Protocolos public-safe para artefatos candidatos antes da validação da fábrica. Veja `planning-bundles/README.md`. |
| `plugins/` | Pacotes públicos de plugin Codex, hoje o Overkill Factory Bridge. Veja `plugins/README.md`. |
| `schemas/` | Contratos de máquina para cards, receipts, workers, gates e artefatos públicos. Veja `schemas/README.md`. |
| `scripts/` | CLI, ferramentas de validação, helpers de prova e checks de manutenção. Veja `scripts/README.md`. |
| `skills/` | Material instalável de skill Codex para operar a fábrica a partir do clone público. Veja `skills/README.md`. |
| `templates/` | Contratos iniciais pareados com schemas e testes. Veja `templates/README.md`. |
| `tests/` | Regressão para contratos públicos, docs, adapters e exemplos. Veja `tests/README.md`. |

Pastas locais ignoradas como `.tmp/`, `build/`, `dist/`, `site/` e
`*.egg-info/` não são superfície pública de produto.

## Estado Atual De Release

Factory V2 é a linha atual de release do kernel público. A release pública mais
recente é v2.0.6.

V2 significa que o kernel público tem contratos executáveis para a linha da
fábrica:

- phase graph determinístico, workflow compilado, command inbox, event log,
  decision outbox e promotion packets;
- Hermes/Kanban como fonte de verdade real para cards, workers e transições;
- contratos de autoridade dos workers: agentes produzem evidência, mas não
  escolhem rota, fase, human gate ou promoção;
- Product Experience control plane: trabalho com interface precisa de Product
  Experience Plan, Product Face Packet, processo profissional de design, design
  system do projeto, `DESIGN.md` e Product Face Result;
- lane runtime de aquisição de capability: quando falta especialista, a fábrica
  pesquisa skill providers, capability packs e referências, escreve um receipt
  `capability_acquisition_run` e só bloqueia depois da busca completa;
- política Hermes de bloqueios tipados: espera de dependência não aciona o
  operador, loops de bloqueio viram triagem, capability exige aquisição e holds
  transitórios viram reparo/retry em vez de aprovação humana genérica;
- Solana AI Kit como rota de primeira classe para Solana/on-chain, com usage
  receipt, signer boundary e onchain work package;
- human gates estritos: o operador recebe o material antes da pergunta de
  decisão;
- readiness claims que separam kernel público, runtime, run de produto e prova
  de produção.

Esse claim é deliberadamente limitado. Factory V2 não significa que um produto
específico está pronto para produção. Um produto criado pela fábrica ainda
exige fonte real, Product SOT, execução de workers, evidência, revisões, human
gates e prova própria de production readiness.
As promessas públicas são rastreadas em
`docs/operations/promise-to-implementation.md` e
`docs/promise-implementation-map.public.json`; cada claim importante precisa
apontar sua implementação, prova e limite.

## Leia Depois

- `docs/index.md`: home da documentação.
- `docs/getting-started/quickstart-hermes.md`: primeira execução com contexto Hermes.
- `docs/getting-started/install-in-hermes.md`: conectar a um runtime Hermes do operador.
- `docs/reference/cli.md`: comandos suportados do `factoryctl`.
- `docs/architecture/factory-v2-control-plane.md`: control plane determinístico.
- `templates/v2-study-traceability.json`: ledger dos claims brutos da V2 com nível de verdade, evidência e lacunas conhecidas.
- `templates/v2-doc-implementation-obligations.json`: obrigações que impedem trabalho documentado de ser confundido com código implementado.
- `templates/factory-v2-readiness-claim.json`: contrato de readiness com escopo explícito.
- `docs/operations/promise-to-implementation.md`: auditoria pública promessa-prova.

## Validação

Antes de publicar mudanças públicas:

```bash
python scripts/validate_document_governance.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_worker_profiles.py
python scripts/validate_promise_implementation_map.py
python scripts/validate_planning_bundles.py
python scripts/factoryctl.py validate-v2-runtime-contracts
python scripts/factoryctl.py validate-agent-skill-boundaries
python scripts/factoryctl.py validate-reference-superiority
python scripts/factoryctl.py capability-acquisition-run --capability-gap solana-ai-kit --surface solana --out .tmp/factory-runs/capability/readme-capability-acquisition-run.json
python scripts/factoryctl.py validate-capability-acquisition-run .tmp/factory-runs/capability/readme-capability-acquisition-run.json
python scripts/factoryctl.py validate-v2-study-traceability templates/v2-study-traceability.json
python scripts/factoryctl.py validate-v2-doc-implementation-obligations templates/v2-doc-implementation-obligations.json --traceability templates/v2-study-traceability.json
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

O mapa público é validado por `scripts/validate_public_surface_sync.py`. O
script compara o HTML versionado com o objeto publicado no GCS e verifica que o
visual não reivindica autoridade de runtime.

## Fronteira Pública

O repositório é uma superfície pública de produto. Ele não deve conter segredos,
evidência privada crua, links privados de board, caminhos absolutos locais,
dumps de fonte privada, screenshots de runs privados, pacotes de worker
gerados, arquivos históricos de prova ou autoridade derivada de chat.

Histórico narrativo de validação, notas antigas tratadas como prova e trilhas
internas de auditoria não pertencem ao onboarding público. O onboarding público
deve apontar para contratos atuais, exemplos executáveis, validadores e guias
curtos para operador.

Hermes e Receipt Five continuam sendo a fonte de verdade da execução real da
fábrica. Este repo documenta e valida o kernel da fábrica; ele não é depósito de
histórico privado de runtime.

## Licença

MIT.
