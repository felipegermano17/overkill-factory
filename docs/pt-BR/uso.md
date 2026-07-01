# Uso

## Requisitos

Use um checkout local do repositório e Python 3.11 ou superior. Os comandos abaixo partem da raiz do repositório e entram em `factory/`, onde fica a superfície executável da fábrica.

```bash
cd factory
```

Os comandos locais leem arquivos públicos do repositório: scripts, schemas, templates, registries, exemplos e docs. Eles não provam que um produto privado foi entregue, nem que um worker executou em um Hermes vivo.

## Instalação

Para usar a superfície local, instale as dependências necessárias para documentação quando for construir o site.

```bash
python3 -m pip install -e '.[docs]'
```

A instalação deixa o comando `factoryctl` disponível quando o ambiente aceita entry points. Se preferir não depender disso, rode sempre pelo arquivo:

```bash
python3 scripts/factoryctl.py --help
```

Esse comando lê a CLI local e mostra subcomandos. Ele confirma que o script é carregável. Ele não executa um ciclo da fábrica.

## Prova local

`factoryctl doctor` verifica se o checkout local tem as peças mínimas da fábrica no lugar. Ele lê estrutura esperada, arquivos essenciais e contratos públicos. Quando passa, indica que a superfície local pode ser usada para próximos comandos. Ele não indica execução viva no Hermes.

```bash
python3 scripts/factoryctl.py doctor
```

`factoryctl run minimal` executa o caminho mínimo público. Ele cria ou valida artefatos locais de exemplo e mostra que o kernel público consegue atravessar um fluxo pequeno. Quando passa, prova coerência local. Não prova entrega real, aprovação de produção, worker vivo ou evidência consumida em um card Hermes real.

```bash
python3 scripts/factoryctl.py run minimal
```

## Inspeção

`route-registry` lista rotas conhecidas. Ele lê o registro de rotas e mostra quais tipos de trabalho a fábrica sabe classificar.

```bash
python3 scripts/factoryctl.py route-registry
```

`method-engines` lista métodos de execução. Ele lê os method engines e mostra quais réguas podem ser aplicadas depois da rota.

```bash
python3 scripts/factoryctl.py method-engines
```

`operating-systems` lista áreas operacionais. Ele lê o registry de operating systems e mostra domínios que a fábrica consegue mapear para trabalho, workers ou controles.

```bash
python3 scripts/factoryctl.py operating-systems
```

Esses comandos são inspeção. Eles mostram contratos disponíveis. Eles não criam execução.

## Card

`compile-workflow` gera um plano compilado do workflow público. Ele lê o catálogo de fases, contratos e regras e grava uma saída local. Essa saída ajuda a inspecionar como a fábrica entende a linha de produção.

```bash
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

`validate-card` lê um card de exemplo e verifica se ele respeita contratos esperados.

```bash
python3 scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md
```

Quando passa, o card é coerente com a validação local. Isso não quer dizer que o card executou. Card válido mostra registro válido, não conclusão.

## Relatórios

`gate-report` lê o card e produz um relatório de gate. O relatório mostra se o card pode avançar, quais workers são necessários, quais bloqueios existem e quais campos precisam ser preenchidos.

```bash
python3 scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
```

A saída pode dizer que algo está pronto para worker, bloqueado antes de ready, bloqueado antes de done ou aguardando decisão. Isso é estado local calculado a partir do card e dos contratos. A mudança real no Hermes precisa aparecer em card vivo.

## Workers

`worker-packet` gera pacotes de worker para o card. O pacote contém contexto, limites, campos de entrada, saída esperada, evidência exigida e regra de retorno.

```bash
python3 scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
```

Um pacote de worker mostra preparação. Ele não mostra execução. Para virar execução, um worker precisa receber o pacote, executar a unidade, devolver resultado e anexar evidência ao fluxo do Hermes.

## Hermes vivo

Execução viva no Hermes exige estado operacional no Hermes: card, status, dependência, worker atribuído, comentário ou anexo de resultado, evidência ligada, revisão consumida e transição registrada. Provas locais ajudam a verificar contratos antes disso, mas não substituem esse estado.

A diferença prática é:

- prova local: comando rodou no checkout e retornou saída;
- contrato válido: arquivo ou card segue schema ou regra;
- worker packet gerado: a fábrica preparou execução;
- execução viva no Hermes: worker executou unidade ligada a card vivo;
- evidência consumida: revisão leu a evidência e mudou estado;
- entrega fechada: recibo final liga pedido, produção, evidência, revisão, decisão e pendências.



## Validadores

Os validadores públicos conferem se documentação, manifestos, promise map e contratos continuam coerentes. Eles leem JSON público, refs de documentação, schemas e registries. Quando passam, mostram que a superfície pública está sincronizada localmente. Eles não provam execução viva no Hermes.

```bash
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/generate_factory_reference_docs.py --check
```

Arquivos gerados em `.tmp` ou relatórios transitórios não devem ser commitados. Eles servem para inspeção local, não para virar fonte pública permanente.

## Claims públicas

Ao escrever sobre a fábrica, mantenha a fronteira da claim. Um teste local passando significa coerência local. Um worker profile existente não significa worker executando. Um card criado não significa trabalho concluído. Evidência anexada não significa evidência consumida. Recibo final precisa declarar pendências e riscos quando existirem.
