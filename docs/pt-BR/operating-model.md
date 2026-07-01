# Como a fábrica trabalha

Vamos acompanhar um pedido como ele deveria andar.

O operador manda: "quero transformar essa ideia em produto".

A resposta errada é abrir uma tarefa gigante e deixar um agente tentar resolver. A resposta certa é a fábrica tratar o pedido como matéria-prima. Matéria-prima ainda não é produto.

## A entrada é só a porta

O pedido pode chegar por Telegram, Discord, cockpit, CLI ou outro canal. O canal não manda na fábrica. Ele só recebe o sinal.

A primeira responsabilidade é guardar a fonte. A mensagem original, o documento, o repo, o link, a conversa, a imagem, o bug, a decisão. Tudo isso precisa existir antes da interpretação.

Se a fábrica resume cedo demais, perde nuance. Se perde nuance, planeja errado. Se planeja errado, entrega algo convincente e inútil.

Por isso o começo é cuidadoso.

## A fábrica separa o que sabe do que acha

Depois de guardar a fonte, a fábrica separa cinco coisas.

Fato: veio da fonte.

Inferência: parece razoável, mas não foi dito literalmente.

Decisão: alguém com autoridade já decidiu.

Conflito: duas fontes dizem coisas diferentes.

Lacuna: falta informação para seguir com segurança.

Essa etapa parece pequena. Não é. Ela impede que um palpite vire requisito e que uma lacuna vire trabalho escondido.

O operador deveria receber uma leitura simples: "entendi isso, falta aquilo, isso aqui não vou assumir".

## A fábrica define o produto antes de planejar

O próximo passo é criar a verdade do produto.

Não é um texto bonito para justificar a execução. É o contrato do que será construído.

Ele responde: qual é o produto, para quem, com que promessa, dentro de que limite, com que risco e com que prova de aceite.

Se o pedido é pequeno, essa verdade pode ser curta. Se o pedido é grande, precisa cobrir o escopo inteiro. O importante é não deixar o worker decidir o produto no meio da execução.

Quando o produto não está definido, qualquer entrega pode parecer certa.

## A rota escolhe a régua

Com o produto definido, a fábrica escolhe a rota.

Rota é a resposta para: que tipo de trabalho é esse?

Bug, produto novo, release, incidente, segurança, UX, documentação, integração, migração, agente, Solana, operação viva. Cada um pede uma régua diferente.

Se é bug, a fábrica precisa de reprodução e regressão.

Se é release, precisa de prontidão, rollback e dono.

Se é interface, precisa de prova da experiência.

Se é segurança, precisa de fronteira, ameaça e revisão.

Se é mainnet ou fundos, precisa de autoridade humana explícita.

A rota impede que tudo vire "manda um agente fazer".

## O método diz como provar

Depois da rota vem o método.

Método bom não é slogan. Ele muda a prova.

Se o método é test-first, precisa ter teste que falha antes ou prova equivalente de regressão.

Se é design-first, precisa de estados, jornada, superfície e evidência visual.

Se é security-first, precisa de fronteira, scan, revisão e decisão sobre risco.

Se é incident-first, precisa de contenção, causa e aprendizado.

Se o método não muda artefato, gate ou evidência, ele não está fazendo nada.

## A fábrica checa se tem capacidade

Nem todo tipo de produto está igualmente coberto.

Web, CLI, cloud, agentes, docs, onboarding e alguns caminhos Solana têm cobertura mais madura no kernel público. Outras áreas podem exigir pacote de capacidade antes: mobile nativo, desktop, game, fintech regulado, hardware, analytics avançado, extensão de navegador.

Isso não é fraqueza. É honestidade operacional.

Uma fábrica confiável não finge que sabe fazer tudo. Ela diz quando tem cobertura e quando precisa instalar, testar ou revisar um pack antes de execução material.

## O trabalho vira pacote pequeno

Agora a fábrica quebra o produto em unidades de trabalho.

Uma unidade boa tem entrada, saída, dono, dependência, evidência, reviewer e regra de pronto.

Uma unidade ruim diz "construir o produto".

A diferença é enorme. Trabalho pequeno pode ser executado, cobrado e refeito. Trabalho gigante vira aposta.

O worker recebe só a parte dele. Ele não ganha autoridade para mudar escopo, aprovar risco, tocar segredo, decidir release ou encerrar o card inteiro.

## Hermes Kanban continua sendo a fonte de verdade

Hermes Kanban continua sendo a fonte de verdade do runtime.

Cards, dependências, status, workers, comentários, workspaces, anexos, bloqueios e transições precisam aparecer ali.

A fábrica não pode manter um segundo estado escondido e depois tentar sincronizar no fim. Se uma unidade depende de outra, a dependência precisa estar no grafo. Se trabalho obrigatório aparece tarde, entra no grafo antes de a fase seguinte andar.

Isso evita uma mentira comum: dizer que a fase terminou enquanto ainda existe trabalho obrigatório fora do quadro.

## No-idle observa silêncio perigoso

No-idle não é outro Hermes.

Ele serve para perceber quando o board está parado de um jeito suspeito. Se há trabalho pronto, despacha. Se há dependência, espera. Se falta pacote de decisão humana, prepara. Se falta readback, artefato ou revisão, repara. Se não consegue reparar, falha de forma visível.

O que ele não pode fazer é inventar autoridade. Não aprova gate, não completa tarefa, não chama o humano por preguiça interna.

## Produto visível precisa ser visto

Quando o trabalho tem interface, a fábrica precisa provar a experiência.

Para web, isso pode envolver telas, viewports, console, overflow, estados vazios, loading, erro, acessibilidade básica e comparação com a promessa do produto.

Para CLI, envolve instalação, help, comando real, saída, erro e comportamento no terminal.

Para docs, envolve outra coisa: o texto realmente ajuda alguém a entender e chegar ao primeiro sucesso?

Uma prova de backend não prova interface. Uma screenshot não prova jornada inteira. Cada superfície precisa de prova própria.

## Revisão só vale quando muda estado

Revisão que fica parada é decoração.

Se passou, precisa destravar ou fechar a tarefa certa. Se falhou, precisa criar reparo. Se apontou risco, precisa registrar dono, consequência e decisão. Se o executor revisa a si mesmo num trabalho material, a fábrica está se enganando.

A revisão precisa voltar para o fluxo.

## Gate humano é pacote de decisão

Quando a decisão é humana, a fábrica chama o humano.

Mas chama direito.

Ela entrega o artefato ou uma projeção fiel. Explica a decisão. Mostra opções. Diz o que cada opção autoriza. Diz o que não autoriza. Mostra o risco e o próximo passo seguro.

O humano não deveria aprovar no escuro.

## O fim tem três saídas

Entrega: há prova, revisão consumida, gates resolvidos e próximo estado claro.

Bloqueio: falta prova, acesso, autoridade, capacidade ou segurança. O bloqueio tem dono e menor próximo passo seguro.

Aprendizado: a execução revelou que a própria fábrica precisa melhorar. Isso pode virar teste, doc, skill, worker, gate, issue ou mudança de processo.

A fábrica boa não força final feliz. Ela fecha quando pode, bloqueia quando deve e aprende quando descobriu algo real.
