# Modelo técnico

Esta página explica o modelo de implementação sem fingir que todo leitor quer morar dentro do código.

A versão curta é esta: Hermes controla estado de runtime. A Overkill Factory controla os contratos de produção em volta desse estado. O repositório guarda scripts, schemas, templates, registries, testes e documentação pública para tornar esse contrato verificável.

## Estrutura do repositório

O repositório público tem duas áreas principais:

- `docs/`: o manual público do produto e catálogos públicos.
- `factory/`: a implementação, com scripts, schemas, templates, agentes, adapters, exemplos, fixtures, testes, skills e docs legadas.

As docs técnicas antigas ficam em `factory/legacy-docs/`. Elas foram preservadas por histórico e compatibilidade, mas não são a explicação pública canônica.

## A superfície executável

`factoryctl` é a principal superfície de comando. Ele valida cards, cria gate reports, compila o workflow, imprime registries, prepara pacotes de worker e roda o caminho público de prova local.

A documentação não deve correr na frente dessa superfície executável. Se a documentação afirma uma capacidade, essa afirmação precisa apontar para código, schema, teste, saída de comando ou decisão atual de produto.

## Estado de runtime

O Hermes controla estado de runtime: cards Kanban, tarefas de worker, dependências, transições, comentários, workspaces, estados bloqueados e estados concluídos. A fábrica não deve recriar esse estado em texto ou num sidecar escondido.

A fábrica adiciona disciplina em volta do runtime. Ela decide quais artefatos são obrigatórios, quais gates entram, que perfil de worker deve cuidar da tarefa, que evidência precisa voltar e que autoridade está proibida.

## Contratos e schemas

O repositório tem hoje 244 schemas JSON e 156 templates JSON. Essa é a espinha dorsal do sistema. Os schemas definem como um registro válido deve parecer. Os templates dão exemplos ou contratos-base. Os testes impedem esses contratos de mudarem em silêncio.

Famílias importantes de contrato incluem planos de workflow, comandos da fábrica, eventos de execução, promotion packets, autoridade de worker, Product SOT, contratos de método, capability packs, gate reports, Receipt Five, gates humanos e provas de runtime.

## Rotas, métodos e sistemas operacionais

O registro de rotas expõe 14 classes de rota. O registro de método expõe 8 motores de método. O registro de operating systems expõe 17 áreas da fábrica.

Classes de rota respondem: "que tipo de trabalho é este?" Motores de método respondem: "como este tipo de trabalho deve ser tratado?" Áreas operacionais respondem: "que parte da fábrica é dona desta capacidade?"

Isso permite que a fábrica se adapte sem ficar vaga. Ela consegue tratar criação de produto, bug, incidente, release, segurança, analytics, UX, migração e qualidade de agente sem fingir que tudo é a mesma tarefa.

## Workers e perfis

O registro público lista hoje 40 workers públicos. O nome do worker não basta. Um worker precisa de perfil, binding, expectativa de resultado, skill refs, política de evidência e limite de autoridade.

Por isso o repositório tem registries de worker, perfis, bindings Hermes, readiness ledgers e validadores. Worker não deve ser personagem de prompt. Deve ser um papel operável com contrato.

## Referência gerada

A referência completa do kernel é produzida por `factory/scripts/generate_factory_reference_docs.py`. A saída gerada agora vive em `factory/legacy-docs/generated/`, porque o manual público precisa continuar legível. O arquivo gerado ainda é útil para maintainers e validadores.

## Pilha de validação

A implementação é guardada por validadores de JSON público, checks de public surface sync, promise-to-implementation, validação de perfis de worker, public safety scan, secret safety scan, build estrito do MkDocs e a suíte de testes Python.

A documentação pública deve ser lida por humanos, mas continua presa a esses checks. É isso que impede o manual de virar uma história solta do produto.

## Como um pedido vira estado

A fábrica não confia num pedido só porque ele apareceu no chat. Primeiro ela registra a fonte. Depois transforma essa fonte em artefatos estruturados. Esses artefatos escolhem a rota, o método, os gates e os pacotes de worker. Só depois a execução de runtime deveria começar.

Essa ordem é proposital. Se um worker começa a partir de uma instrução vaga, o sistema não tem uma forma estável de decidir se a resposta está certa. Se o pedido vira estado antes, cada passo depois consegue apontar para a mesma fonte. O worker ainda pode errar, mas a fábrica tem algo concreto para comparar.

## O que deve ser gerado e o que deve ser escrito para gente

Algumas coisas são melhores quando geradas a partir do código: catálogos completos de comando, cobertura de schemas, inventário de workers e tabelas grandes de referência. Escrever isso à mão, de cabeça, é o caminho mais curto para documentação velha.

Outras coisas precisam ser escritas para gente: este manual, o modelo operacional, o modelo de confiança e o caminho de uso. Um operador novo não precisa receber uma referência gerada de mil linhas como primeira explicação. Ele precisa entender a história em linguagem simples e depois ver comandos exatos quando estiver pronto.

O repositório atual mantém as duas camadas. O material gerado continua existindo para validação e manutenção. O manual público continua legível.

## O que pode dar errado

O modelo técnico é rígido porque as falhas são sutis. Um caminho pode existir, mas apontar para documentação legada. Um manifest público pode citar um arquivo que foi movido. Um perfil de worker pode parecer configurado enquanto o binding aponta para docs antigas. Uma prova local pode passar enquanto o Hermes vivo não foi checado. Uma claim pública pode ser verdadeira para o kernel e falsa para uma execução privada de produto.

Os validadores existem para pegar essas divergências. Eles não substituem julgamento, mas removem muitas formas fáceis de enganar a nós mesmos.

## Como mudar a fábrica com segurança

Uma mudança segura normalmente mexe em três camadas ao mesmo tempo: a explicação humana, o contrato executável e os testes ou validadores. Se você muda só a doc, talvez melhore a comunicação sem mudar comportamento. Se muda só o código, a superfície pública pode mentir. Se muda só o teste, talvez esteja protegendo um modelo antigo.

Para documentação pública, a regra mais segura é simples: escreva a partir do código atual e da saída real dos comandos, não de memória. Depois rode os validadores. Se eles reclamarem, trate isso como sinal de produto, não como incômodo.
