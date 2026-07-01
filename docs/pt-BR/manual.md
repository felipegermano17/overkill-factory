# Manual

A Overkill Factory é mais fácil de entender se você esquecer, por um minuto, os nomes internos.

Pense numa conversa normal.

Você diz: "quero criar esse produto". Ou: "esse release pode ir?". Ou: "corrige esse bug sem quebrar o resto". Ou: "tem algo errado nesse board, os agentes parecem ocupados, mas nada anda".

Um agente comum tenta responder fazendo. Ele pode ser útil, mas trabalha com um risco enorme: ele quer avançar antes de ter certeza do que está avançando.

A fábrica existe para colocar um processo entre o pedido e a execução.

Não processo no sentido ruim, de burocracia. Processo no sentido de chão firme. Antes de alguém mexer no produto, a fábrica precisa saber o que foi pedido, o que é fato, o que é suposição, qual é o produto, que tipo de trabalho é, quem tem autoridade, que prova vai contar e o que acontece se a prova não aparecer.

Isso é produção controlada.

## Por que isso importa

O erro mais perigoso de um agente não é falhar claramente.

Falha clara é fácil. O comando quebrou. O arquivo não existe. A API recusou. O teste falhou.

O erro perigoso é a entrega que parece certa.

O agente cria um documento, mas o documento não responde à pergunta. Cria uma tela, mas não cobre os estados importantes. Escreve um teste, mas testa o caminho feliz e ignora o risco. Faz uma revisão, mas não relê o artefato. Diz que precisa do humano, mas na verdade faltou readback, faltou anexar prova, faltou rodar um worker.

Aí o operador vira fiscal de tudo.

Ele precisa perguntar onde está a prova. Precisa notar que o card andou sem dependência. Precisa perceber que o reviewer só carimbou. Precisa descobrir que o bloqueio era interno. Precisa virar gerente, QA, auditor e detetive.

A fábrica foi desenhada para impedir isso.

## O que a fábrica promete

A promessa não é "agentes nunca erram".

A promessa é melhor: quando a fábrica está funcionando, erro vira estado visível. Lacuna vira lacuna. Risco vira risco. Bloqueio vira bloqueio com dono. Pronto vira pronto com prova.

O operador não precisa acreditar no tom do agente. Ele olha o recibo.

## O caminho de um pedido

Um pedido entra quase sempre meio torto. Isso é normal. Produto real começa assim mesmo.

"Cria o onboarding".

Certo. Mas onboarding de quem? Com que conta? Com carteira? Com permissão? Com KYC? Com trial? Com pagamento? Com convite? Com dados sensíveis? O sucesso é chegar numa tela? É fazer a primeira ação? É depositar dinheiro? É assinar uma transação? É convidar alguém?

A fábrica não deveria pular essas perguntas. Também não deveria jogar tudo de volta para o operador se ela consegue resolver com a fonte que já existe.

O primeiro trabalho é preservar a fonte e separar o que é sabido do que é palpite.

Depois vem a verdade do produto. Internamente isso aparece como Product SOT. Em português simples: é o acordo sobre o que está sendo construído.

Só depois faz sentido escolher método, criar tarefas e mandar workers.

## O que é verdade do produto

Verdade do produto não é um resumo bonito.

É o lugar onde a fábrica registra:

- qual é o pedido;
- quem é o usuário ou operador afetado;
- que problema precisa ser resolvido;
- o que entra no escopo;
- o que fica fora;
- que riscos importam;
- que decisões já foram tomadas;
- que decisões ainda dependem do humano;
- que prova vai contar como aceite.

Sem isso, qualquer plano parece razoável. Com isso, o plano pode ser cobrado.

A fábrica também precisa cuidar de uma armadilha comum: transformar a primeira fatia executável no produto inteiro. Se o produto é maior, cada parte importante precisa ter destino. Pode estar planejada, bloqueada, fora de escopo, delegada ao humano ou provada. Não pode simplesmente sumir.

## Método não é enfeite

Trabalhos diferentes precisam de caminhos diferentes.

Bug pede reprodução e regressão.

Release pede prontidão, rollback, dono e monitoramento.

Interface pede jornada, estados, tela, erro, carregamento, acessibilidade básica e prova visual.

Segurança pede fronteira, ameaça, segredo, permissão, supply chain, revisão e decisão sobre risco residual.

Incidente pede contenção, causa, comunicação e aprendizado.

Produto novo pede verdade do produto, decomposição, workers, revisão e aceite.

Se a fábrica trata tudo igual, ela é só uma fila de tarefas com nome bonito.

## O papel do Hermes

Hermes é o chão da fábrica.

É onde ficam os cards, dependências, status, workers, comentários, workspaces, anexos, bloqueios e transições.

A Overkill Factory não deveria criar outro estado escondido. Ela define o contrato do trabalho: que artefatos precisam existir, que gates bloqueiam, que worker entra, que prova volta, que decisão é humana e que atalhos são proibidos.

Hermes mostra o trabalho vivo. A fábrica diz o que esse trabalho precisa respeitar.

## O que é um worker bom

Um worker bom não recebe "faz o produto".

Recebe um pacote pequeno.

O pacote diz: faça isto, usando esta fonte, dentro deste limite, sem essa autoridade, devolvendo esta evidência. Se faltar algo, bloqueie deste jeito.

Isso parece simples, mas muda a qualidade da autonomia. O worker pode andar rápido porque a faixa está marcada. E a revisão consegue olhar uma entrega pequena em vez de tentar julgar uma missão nebulosa.

## Onde o humano entra

O humano não deveria ser chamado para limpar bagunça da fábrica.

Se falta arquivo, readback, evidência, revisão, PDF, link, hash, screenshot, worker result ou reparo interno, a fábrica trabalha.

O humano entra quando a autoridade é dele: produção, mainnet, fundos, segredos, orçamento, release, risco material, waiver, mudança de poder.

E quando entra, a fábrica precisa respeitar o tempo dele. Nada de "aprova?" sem contexto. Nada de JSON cru. Nada de caminho local como se fosse decisão.

Um gate humano bom entrega uma decisão clara:

"Você está aprovando este artefato, com estes riscos, para permitir este próximo passo. Você não está aprovando aquilo. Se recusar, o caminho seguro é este".

## O que significa pronto

Pronto quer dizer provado.

Não quer dizer que o agente ficou confiante. Não quer dizer que um arquivo apareceu. Não quer dizer que um teste qualquer passou. Não quer dizer que alguém falou "ok" no chat.

A fábrica precisa conseguir contar a história:

"O pedido era este. A fonte usada foi esta. O produto definido foi este. O método escolhido foi este. Estes workers rodaram. Estas provas voltaram. Esta revisão foi consumida. Este gate humano autorizou isto. O que ainda falta é aquilo".

Se essa história não existe, a entrega não está pronta. Ela pode estar em revisão, bloqueada, incompleta ou aguardando decisão. Mas pronta, não.

## O que falta quando a fábrica parece ruim

Quando a documentação, o board ou a execução parecem ruins, normalmente é porque uma dessas coisas sumiu:

- a dor do operador;
- a verdade do produto;
- o motivo de cada fase;
- a fronteira entre Hermes e fábrica;
- a diferença entre prova local e entrega viva;
- a explicação de por que um humano está sendo chamado;
- a ligação entre worker, evidência, revisão e recibo.

A fábrica não pode virar uma coleção de termos internos. Se o leitor precisa decorar nomes para entender o produto, a documentação falhou.

A versão boa precisa parecer uma conversa séria: simples na superfície, precisa por baixo, honesta sobre o que existe e o que ainda precisa ser provado.
