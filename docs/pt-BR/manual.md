# Fábrica

## Definição

A Overkill Factory organiza trabalho em torno de Hermes. Ela recebe um pedido, preserva a fonte que sustenta esse pedido, registra o entendimento, monta a verdade do produto, escolhe uma rota, aplica um método, quebra o trabalho em unidades pequenas e acompanha cada unidade no Hermes até evidência, revisão, decisão e fechamento.

A fábrica não trata uma frase inicial como plano. Uma mensagem, uma issue, um documento ou um card entram como começo do ciclo. Antes de virar execução, esse material precisa ficar ligado à fonte, precisa ser lido, precisa separar o que está decidido do que ainda é lacuna e precisa gerar um estado que consiga alimentar trabalho pequeno.

A produção acontece por mudança de estado. Uma parte da fábrica recebe material, lê esse material, cria ou atualiza um artefato e entrega uma saída que a próxima parte consegue usar. O pedido alimenta a fonte. A fonte alimenta o entendimento. O entendimento alimenta a verdade do produto. A verdade do produto alimenta rota, método e trabalho. O trabalho aparece no Hermes. A execução devolve resultado. A evidência sustenta revisão. A revisão altera o estado. A decisão humana entra quando há autoridade necessária. O recibo final fecha ou registra o que ficou pendente.



Quando uma parte muda de estado, a mudança precisa deixar rastro. Se a fonte foi preservada, deve haver referência para ela. Se o entendimento foi registrado, deve ser possível ler quais fatos, lacunas e decisões sustentam a próxima etapa. Se uma unidade avançou, deve haver evidência ligada ao card. A fábrica depende desses rastros para que uma pessoa consiga retomar o ciclo sem depender da memória de quem estava no chat.

Nomes internos aparecem quando ajudam a manter ligação com o código. A verdade do produto também pode aparecer como `Product SOT`. A unidade de trabalho pode aparecer como `work unit`. O pacote de worker pode aparecer como `worker packet`. O recibo final pode aparecer como `Receipt Five`. Esses nomes não substituem a explicação humana; eles apenas apontam para contratos internos.

## Hermes

Hermes é o chão onde o trabalho fica visível. No Hermes, a execução aparece como cards, status, comentários, anexos, dependências, workers, bloqueios, transições, registros de revisão e registros de decisão.

A Factory prepara o trabalho que entra nesse chão. Ela define qual fonte sustenta o card, qual verdade do produto se aplica, qual rota foi escolhida, qual método rege a execução, qual worker pode atuar, qual evidência deve voltar e qual revisão precisa consumir o resultado. Hermes registra o estado vivo: card aberto, card bloqueado, worker atribuído, comentário novo, anexo recebido, dependência esperando, revisão pendente, decisão aguardando ou ciclo fechado.

A relação é operacional. A Factory não deve criar um controle paralelo que esconda o Hermes. Se uma unidade de trabalho está pronta para execução, ela precisa aparecer como card ou atualização de card. Se uma dependência impede avanço, o bloqueio precisa ficar visível. Se um worker termina uma parte, o resultado volta ligado ao card. Se há evidência, ela fica anexada ou referenciada naquele ponto. Se a revisão aprova, pede reparo ou bloqueia, a mudança de estado acontece no mesmo fluxo.

Hermes mostra o trabalho vivo. A Factory define o método de produção. A Factory lê o estado, a evidência e a revisão para decidir o próximo movimento. Essa fronteira importa porque um arquivo local, um pacote gerado ou uma frase em chat não substitui estado vivo no Hermes.

## Papéis

O operador inicia ou orienta o ciclo. Ele entrega pedido, contexto, fonte, decisão ou autoridade. O operador não precisa reconciliar detalhes internos da fábrica. Quando a fábrica precisa dele, ela prepara um pacote de decisão com contexto, evidência, opções, risco e consequência.

O Factory Manager conduz a linha. Ele recebe o pedido já ligado à fonte, observa o estado no Hermes, decide qual parte da fábrica precisa agir e mantém o fluxo entre entendimento, verdade do produto, rota, método, trabalho, execução, revisão e fechamento. Ele não deve transformar ausência de evidência em aprovação, nem tratar silêncio humano como decisão.

Hermes registra o chão de execução. Ele recebe cards, comentários, anexos, dependências, workers, bloqueios e transições. Ele mostra onde a unidade está e o que falta para mudar de estado.

O worker executa uma unidade limitada. Ele recebe um pacote com contexto, entrada, saída esperada, limites, evidência exigida e campo de retorno. O worker pode produzir resultado e evidência dentro daquela unidade. Ele não pode ampliar escopo, aprovar release, inventar decisão humana ou fechar o ciclo inteiro sozinho.

O reviewer lê o resultado e a evidência. A revisão não é opinião solta. Ela consome o material ligado ao card e produz mudança de estado: aprovado, precisa reparo, bloqueado, evidência insuficiente, fora de escopo ou decisão humana necessária.

O humano decisor entra quando a etapa exige autoridade. Produção, release, mainnet, fundos, segredos, gasto, risco residual, waiver, exceção de método e mudança irreversível exigem decisão registrada quando aplicável. A fábrica prepara o pacote; o humano decide; o Hermes registra o efeito.

O mantenedor altera a própria fábrica. Ele mexe em documentação, contratos, schemas, templates, registries, scripts, testes e validadores. Uma mudança sólida normalmente atualiza explicação humana, contrato executável e teste ou prova local.

## Estado

A fábrica trabalha com estado, não só com tarefas abertas ou concluídas. Estado inclui origem preservada, entendimento registrado, verdade do produto montada, rota escolhida, método aplicado, trabalho quebrado, worker atribuído, evidência anexada, revisão consumida, decisão pendente, bloqueio registrado, recibo produzido e fechamento arquivado.

Cada etapa altera algo que a próxima etapa lê. Quando a fonte é preservada, o entendimento passa a ter material consultável. Quando o entendimento separa fatos, inferências, lacunas e decisões, a verdade do produto passa a ter base. Quando a verdade do produto declara escopo, fora de escopo, prova e autoridade, a rota pode ser escolhida sem depender de frase solta. Quando a rota e o método existem, as unidades de trabalho podem carregar entrada, saída, evidência e regra de avanço. Quando essas unidades entram no Hermes, workers, reviewers e decisões passam a operar sobre estado visível.

Bloqueio também é estado. Se falta fonte, o entendimento não avança. Se falta acesso, a unidade não é executável. Se falta evidência, a revisão não fecha. Se a decisão humana está pendente, o gate aguarda. Se o risco não tem dono, o fechamento não declara pronto completo. O bloqueio precisa registrar motivo, dono, próxima ação e ponto de retomada.

Retomada também é estado. Quando a fonte aparece, o registro de entendimento pode ser reaberto. Quando o acesso é concedido, a unidade volta para a fila executável. Quando a evidência chega, a revisão consome o material. Quando a decisão humana é registrada, o card muda para o próximo estado autorizado.

## Artefatos

A fonte é o material preservado antes da interpretação. Pode ser mensagem, documento, link, repositório, print, arquivo, conversa anterior, card anterior, decisão anterior ou anexo. Ela fica ligada ao pedido para que a fábrica possa voltar ao material original quando surgir dúvida.

O registro de entendimento é a leitura estruturada da fonte. Ele separa fatos, afirmações do pedido, decisões já tomadas, restrições, dependências, dúvidas, lacunas, conflitos, inferências e itens fora de escopo. Ele não é plano de execução. Ele é a passagem entre fonte preservada e verdade do produto.

A verdade do produto (`Product SOT`) é a referência central do que será produzido. Ela contém objetivo, usuário ou destinatário, escopo dentro, escopo fora, estado atual, estado desejado, restrições, riscos, dependências, critérios de aceitação, prova necessária, decisões pendentes e autoridade necessária.

A rota classifica o tipo de trabalho. Documentação, bug, feature, interface, CLI, integração, release, incidente, segurança, blockchain/Solana, dados, operação e manutenção podem exigir rotas diferentes. A rota vem da verdade do produto e determina quais métodos, provas, workers e gates entram no ciclo.

O método é a régua de execução para a rota. Ele define passos mínimos, evidência que conta, revisão exigida, decisão humana possível, trabalho que pode ser automatizado, checks necessários e estado mínimo antes de avanço.

A unidade de trabalho (`work unit`) é uma parte executável. Ela tem entrada, saída esperada, dono, worker ou perfil de worker, dependência, evidência exigida, reviewer, regra de pronto, relação com card Hermes e estado de bloqueio ou avanço.

O card Hermes é a representação viva da unidade ou do conjunto de unidades. Ele carrega status, comentários, anexos, dependências, workers, bloqueios, revisão e decisão.

O pacote de worker (`worker packet`) é a preparação para execução. Ele diz ao worker o que fazer, com quais entradas, quais limites, que evidência devolver e em qual campo. O pacote não é execução. Execução exige resultado voltando ao ciclo.

A evidência é material ligado à unidade, ao card, ao resultado do worker e à revisão. Pode ser saída de comando, log, screenshot, diff, arquivo alterado, teste rodado, relatório, comentário de revisão, decisão registrada, link para artefato, anexo, checklist consumido, prova de rollback, prova de ambiente ou prova de transação quando aplicável.

A revisão consome resultado e evidência. Ela produz estado: aprovado, precisa reparo, bloqueado, decisão humana necessária, evidência insuficiente, fora de escopo, risco aceito, risco não aceito ou reaberto.

A decisão humana registra autoridade. Ela contém contexto, pedido, evidência, opções, risco, consequência, limite do que já foi verificado e próximo estado após a escolha.

O recibo final (`Receipt Five`) fecha o ciclo de forma legível. Ele registra o que foi pedido, o que foi produzido, que evidência sustenta, quem revisou ou decidiu e o que ficou pendente, bloqueado, fora de escopo ou como risco.

## Ciclo

```text
pedido -> fonte -> entendimento -> verdade do produto -> rota -> método -> trabalho -> Hermes -> evidência -> revisão -> decisão -> recibo -> fechamento
```

O pedido entra como sinal inicial. A fonte preserva o material que sustenta o pedido. O entendimento lê a fonte e separa o que pode alimentar produção. A verdade do produto transforma essa leitura em referência de escopo, prova e autoridade. A rota classifica o tipo de trabalho. O método define a régua de execução. O trabalho é quebrado em unidades pequenas. Hermes recebe cards, workers, dependências e bloqueios. A execução devolve resultado. A evidência fica ligada ao card. A revisão consome essa evidência e muda estado. A decisão humana entra quando há autoridade necessária. O recibo final liga pedido, produção, evidência, revisão, decisão e pendências. O fechamento declara entregue, bloqueado, parcial, reaberto, aprendido, arquivado ou aguardando decisão.

## Limites

Prova local mostra coerência local. Ela não mostra execução viva no Hermes.

Contrato válido mostra que um artefato segue schema ou regra pública. Ele não mostra que um worker executou uma unidade real.

Card criado mostra registro. Ele não mostra trabalho concluído.

Pacote de worker mostra preparação. Ele não mostra execução.

Evidência anexada mostra material disponível. Evidência consumida em revisão mostra avanço de estado.

Revisão sem efeito de estado não fecha ciclo.

Decisão humana não deve ser simulada pela fábrica. Produção, release, mainnet, fundos, segredos, gasto, mudança irreversível e risco residual exigem autoridade registrada quando aplicável.

Recibo final mostra fechamento do ciclo apenas quando liga pedido, produção, evidência, revisão, decisão e pendências. Se há pendência ou risco, o recibo precisa declarar isso.
