# Confiança e evidência

A pergunta desta página é simples:

"Como eu sei que isso não é só um agente falando bonito?"

A resposta começa por uma verdade incômoda: processo parecendo vivo não é a mesma coisa que progresso.

Essa pergunta precisa ficar no centro da Overkill Factory. Agente é muito bom em parecer confiante. Ele escreve. Ele resume. Ele cria arquivo. Ele move card. Ele diz que passou. Mas nada disso, sozinho, prova que o produto ficou certo.

A fábrica existe porque progresso falso é caro.

## O inimigo é o teatro de progresso

Teatro de progresso é quando o sistema parece vivo, mas a entrega real não avançou.

Exemplos:

- o worker diz "feito", mas não entrega evidência;
- o arquivo existe, mas não resolve o pedido;
- o teste passa, mas testa a coisa errada;
- o reviewer aprova sem ler o artefato;
- o humano é chamado para aprovar sem receber o material;
- o board fica cheio de atividade, mas o bloqueio real continua lá;
- a fábrica pede decisão humana para algo que ela mesma deveria reparar.

Tudo isso deve ser tratado como falha de produto, não como detalhe de processo.

## Evidência é mais importante que tom de voz

A fábrica não confia em confiança. Confia em prova.

Um worker bom não só diz o que fez. Ele aponta para o artefato, o comando, o resultado, a captura, o diff, o log, o teste, a revisão ou o pacote que prova.

Mesmo assim, evidência não pode ser qualquer coisa. Um caminho local perdido não serve. Um arquivo temporário não serve. Um print sem contexto quase nunca serve. Um pass sem escopo não serve. Uma aprovação humana genérica não serve para liberar produção, fundo, segredo ou mainnet.

A prova precisa ser atual, legível e ligada ao pedido.

## Readback: ler o que foi entregue

Readback é uma palavra feia para uma coisa simples: a fábrica precisa reler o que o worker diz que entregou.

Se ele diz que escreveu um Product SOT, a fábrica lê o SOT.

Se ele diz que anexou evidência, a fábrica confere se a evidência abre, se tem tamanho, se tem hash quando precisa, se pode ser lida depois e se não vaza segredo.

Se ele diz que criou um teste, a fábrica confere se o teste cobre o comportamento certo.

Sem readback, o processo pode estar correto e o produto errado.

## Receipt Five: o recibo do pronto

Receipt Five é o jeito da fábrica dizer "pronto" sem depender de humor, pressa ou autoridade do executor.

Ele precisa responder cinco perguntas:

1. O que foi pedido?
2. O que foi feito ou decidido?
3. Que evidência prova isso?
4. Quem revisou e o que a revisão concluiu?
5. O que continua pendente, bloqueado ou arriscado?

Se uma dessas respostas falta, o estado honesto não é pronto. Pode ser pronto para revisão. Pode ser parcialmente completo. Pode ser bloqueado. Pode estar aguardando decisão humana.

Mas não é pronto.

## Revisão independente não é carimbo

Review de verdade precisa ser consumido.

Não basta gerar um relatório de revisão. A fábrica precisa usar o resultado. Se passou, destrava ou fecha o item certo. Se falhou, cria reparo. Se achou risco residual, registra dono e decisão. Se o reviewer é a mesma identidade que executou, não é revisão independente.

Revisão parada é só mais um artefato bonito.

## Bloqueio honesto

Bloqueio bom diz:

- o que falta;
- por que falta;
- quem é dono;
- qual é o menor próximo passo seguro;
- se precisa ou não do operador.

Nem todo bloqueio é humano.

Se a dependência ainda não terminou, é espera. Se falta capacidade, a fábrica precisa buscar ou ativar um pacote. Se é erro transitório, tenta reparar. Se falta artefato, readback, PDF ou revisão, a fábrica trabalha.

O operador só entra quando existe decisão real de autoridade.

## Gate humano precisa respeitar o humano

Gate humano não é "posso seguir?" jogado no chat.

Um gate humano sério entrega o material sob revisão. Se é Product SOT, entrega o SOT. Se é arquitetura, entrega a arquitetura. Se é release, entrega o pacote de release. Se é segurança, entrega o risco e as opções.

A primeira mensagem precisa ser clara e curta:

- decisão pedida;
- resumo em português normal;
- o que aprovar permite;
- o que aprovar não permite;
- opções de resposta;
- consequência;
- evidência;
- urgência.

O anexo pode ser grande. A pergunta não pode ser vaga.

## Segurança não fica para o fim

Segurança não é um scan no final para deixar a PR bonita.

Se o trabalho toca autenticação, permissão, segredo, chave, produção, supply chain, privacidade, carteira, assinatura, Solana, fundos ou mainnet, a segurança entra no caminho desde cedo.

Às vezes isso significa arquitetura. Às vezes significa threat model. Às vezes significa worker especialista. Às vezes significa gate humano. Às vezes significa bloquear.

A fábrica não promete segurança perfeita. Promete não fingir que risco desapareceu.

## Prova local, prova viva e prova pública

Essas três coisas são diferentes.

Um comando local passando prova que o checkout está coerente.

Um Hermes vivo com worker result prova que aquele worker rodou naquele contexto.

Um Receipt Five bem formado prova que a conclusão daquele trabalho está ligada a pedido, mudança, evidência, revisão e próximo estado.

Uma publicação pública ainda precisa passar por segurança de superfície e segredo.

Não dá para trocar uma pela outra. Smoke local não prova produto entregue. Arquivo existente não prova readback. Aprovação genérica não prova release. Print bonito não prova jornada.

## Quando confiar

Você pode começar a confiar quando a fábrica consegue contar a história inteira sem pular etapa:

"O pedido era este. A fonte dizia isto. A verdade do produto ficou assim. O método escolhido foi este. Estes workers rodaram. Estas evidências voltaram. Esta revisão foi consumida. Este gate humano autorizou exatamente isto. O que ainda falta é aquilo."

Essa história precisa estar nos artefatos, não só na memória de quem estava no chat.

Esse é o padrão.
