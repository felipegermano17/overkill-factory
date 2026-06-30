# Manual do produto

A Overkill Factory fica mais fácil de entender quando começamos pelo problema que ela resolve.

Uma pessoa pede alguma coisa: criar um produto, corrigir um bug, revisar uma mudança arriscada, preparar um release, tratar um incidente, melhorar um worker ou transformar uma ideia num sistema funcionando. Em muitos fluxos com agentes, isso vira uma instrução grande. O agente tenta ajudar, começa a trabalhar e vai mandando status. Às vezes dá certo. Muitas vezes vira movimento sem controle.

A Overkill Factory trata trabalho de produto como produção controlada. A fábrica não joga um "se vira" para o agente. Ela preserva a fonte, define o produto, escolhe o método, divide o trabalho, executa pelo Hermes, verifica evidência e fecha com recibo.

## O que "fábrica" quer dizer aqui

Fábrica não é sinônimo de burocracia. Quer dizer que existe uma linha de produção. O trabalho entra por um lado e precisa passar por estados que protegem o operador.

Um pedido de produto não deveria pular direto para implementação se ninguém resolveu a fonte. Um release não deveria sair porque o executor disse que está pronto. Uma mudança sensível de segurança não deveria pular arquitetura. Um gate humano não deveria ficar escondido num comentário de chat. Um worker não deveria aprovar o próprio trabalho.

Isso é produção controlada. É a diferença entre "um agente mexeu nisso" e "a fábrica consegue explicar o que aconteceu, por que aconteceu, quem tinha autoridade e qual evidência prova o resultado".

## A experiência do operador

O operador não deveria ter que cuidar da fábrica como babá. Ele não deveria precisar perceber que um worker foi raso, que uma revisão nunca foi consumida, ou que um bloqueio era na verdade trabalho da própria fábrica. A fábrica é dona do processo. O humano é dono das decisões reais.

Uma boa execução se parece com isto:

- o operador entrega um objetivo ou material de origem;
- a fábrica diz o que entendeu e o que falta;
- a fábrica cria uma definição de produto que pode ser revisada;
- o trabalho é quebrado em partes pequenas o bastante para um worker terminar e provar;
- o Hermes guarda o estado vivo;
- revisões são independentes quando o risco pede;
- gates humanos chegam como pacotes de decisão, não como interrupções vagas;
- a conclusão vem com Receipt Five, não com uma mensagem animada dizendo "pronto".

## A camada de verdade do produto

O artefato mais importante é a verdade do produto. A fábrica chama isso de Product SOT, porque é a fonte de verdade do produto. O nome é técnico, mas a ideia é simples: antes de construir, todo mundo precisa saber que produto está sendo construído.

Um Product SOT precisa dizer o que foi pedido, o que entra no escopo, o que fica fora, quais riscos importam, que evidência vai contar e o que tornaria o trabalho inaceitável. Sem isso, a fábrica não consegue escolher método nem distribuir workers com segurança.

É aqui que muitos sistemas com agentes escorregam. Eles transformam um briefing grande num resumo curto e depois constroem a partir do resumo. A Overkill Factory foi desenhada para evitar isso. Resumo não é verdade do produto. Palpite útil não é verdade do produto. A verdade do produto precisa vir da fonte e precisa ser revisada quando o risco pede.

## Métodos são escolhidos, não improvisados

Trabalhos diferentes pedem métodos diferentes. Bug precisa de reprodução e prova de regressão. Produto novo precisa de definição e cobertura de escopo. Release precisa de prontidão, rollback e aprovação. Mudança de segurança precisa de arquitetura, ameaça e evidência.

O registro de rotas e os motores de método deixam isso explícito. Hoje a fábrica tem 14 classes de rota e 8 motores de método. A ideia não é impressionar com uma lista grande. A ideia é impedir que todo pedido seja tratado do mesmo jeito.

Quando o método está certo, o worker recebe um pacote limitado. Ele sabe a tarefa, os limites, a evidência esperada e a autoridade que ele não tem. Isso torna a autonomia mais segura. O worker pode andar rápido dentro da faixa porque a faixa está clara.

## Hermes é o chão da fábrica

O Hermes é onde o estado vivo mora. Cards, dependências, comentários, workspaces, workers, bloqueios e transições pertencem a ele. A Overkill Factory define o método de produção e os checks. O Hermes roda o chão da fábrica.

Essa separação é importante. Se a fábrica tentasse virar um segundo Hermes, ela criaria outro estado escondido. Se o Hermes guardasse o estado mas a fábrica ignorasse método e evidência, os workers moveriam cards sem disciplina de produto. O desenho é separado de propósito: Hermes controla o estado vivo; Overkill Factory controla o contrato de produção.

## Pronto quer dizer provado

A fábrica é rígida com conclusão porque trabalho com agente pode parecer convincente mesmo quando está errado. Um arquivo pode existir e não servir. Um teste pode passar e ainda não cobrir o produto. Um revisor pode aprovar sem checar a coisa certa. Um worker pode dizer que terminou e esquecer o artefato.

O Receipt Five existe para evitar isso. Ele registra o que foi pedido, o que foi feito, qual evidência prova, quem revisou, o que ainda está arriscado ou bloqueado e qual é o próximo estado. Se essa evidência não existe, a resposta honesta não é "pronto". É bloqueado, incompleto ou pronto para revisão.

## O que este projeto não é

A Overkill Factory não tenta fingir que produto é simples. Ela tenta colocar a complexidade no lugar certo. O operador vê estado claro e decisões reais. Os workers recebem pacotes exatos. O código carrega schemas e testes. A documentação pública explica o suficiente para uma pessoa nova confiar no sistema sem ler cada arquivo interno.

Esse é o nível esperado do projeto: simples por fora, rigoroso por dentro e honesto na fronteira.

## Um exemplo concreto

Imagine que o operador diga: "Crie o fluxo de onboarding do cliente." Um sistema fraco com agentes talvez comece a desenhar telas imediatamente. A fábrica não deveria fazer isso.

Primeiro ela precisa entender o que "cliente" quer dizer naquele produto, o que o onboarding deve resolver, que contas ou permissões existem, o que o usuário precisa ver, o que precisa ser registrado e o que conta como uma primeira execução bem-sucedida. Se o produto já tem design system, a fábrica deve consumir isso. Se o fluxo toca dinheiro, identidade, custódia ou dados de produção, os gates de risco mudam.

Só depois implementação faz sentido. Um worker de frontend pode receber um pacote. Um worker de backend pode receber outro. Um worker de Product Face talvez precise devolver screenshots e prova por viewport. QA pode precisar de teste de jornada. Um reviewer pode precisar comparar o resultado com o Product SOT. O operador não deveria coordenar tudo isso na mão.

Esse é o valor prático da fábrica. Ela transforma um pedido vago em pedaços pequenos, revisáveis e sustentados por evidência.

## O que a fábrica tira das costas do operador

A promessa prática é autonomia com responsabilidade. O operador traz direção, contexto, restrições e decisões reais. Ele não deveria virar coordenador manual de source ledger, Product SOT, worker packet, review, proof, release e learnback.

Quando a fábrica funciona bem, ela antecipa o que normalmente viraria cobrança humana:

- percebe que a fonte está incompleta antes de começar;
- transforma o pedido em definição de produto revisável;
- escolhe a rota certa para bug, feature, release, incidente, segurança, UX ou agente;
- cria pacotes pequenos em vez de uma missão gigante;
- cobra prova do worker que executou;
- chama review independente quando o risco pede;
- prepara gate humano com artefato legível quando a decisão é do operador;
- bloqueia com motivo claro quando falta acesso, autoridade, evidência ou segurança.

Isso muda a relação com agentes. O humano deixa de ser fiscal de preguiça do sistema e volta a ser dono do produto e das decisões importantes.

## A recepção pode ser simples; o contrato por trás não pode ser fraco

Telegram, Discord, cockpit ou CLI podem ser a porta de entrada. O operador pode começar com uma frase curta, um documento, um repo, um bug ou um objetivo de negócio. A conversa deve ser simples.

Mas simplicidade na entrada não significa informalidade na execução. Atrás da conversa, a fábrica precisa montar fonte, escopo, método, gates, workers e evidência. Se ela pula isso, só trocou formulário por chat e continua frágil.

Por isso a fábrica separa o gerente, que fala com o operador, do orquestrador, que cuida de rota e runtime. O operador recebe status e decisões em linguagem humana. O Hermes e os contratos guardam o estado real.
