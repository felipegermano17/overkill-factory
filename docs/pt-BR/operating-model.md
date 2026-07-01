# Como a fábrica trabalha

A melhor forma de entender a Overkill Factory é acompanhar um pedido por dentro.

Imagine que você manda uma mensagem: "quero transformar essa ideia num produto". Ou "esse release pode ir?". Ou "corrige esse fluxo". A fábrica não deveria sair correndo para codar. O primeiro trabalho dela é descobrir que tipo de pedido entrou e o que precisa ser verdade antes de qualquer agente tocar no produto.

## 1. Entrada não é execução

A conversa pode começar no Telegram, no Discord, no cockpit, no terminal ou em outro canal. Isso é só a porta de entrada.

A porta recebe material, pergunta, arquivo, link, repo, imagem, bug, decisão. Mas ela não decide sozinha o que vai ser feito. Ela não é o runtime. Ela não é a verdade.

A função da entrada é criar um começo seguro: guardar a fonte, registrar o objetivo, separar o que já está claro do que ainda precisa ser resolvido e impedir que a primeira interpretação vire plano definitivo.

É aqui que o gerente aparece. O gerente fala com o operador. Ele traduz estado, pede decisão quando precisa e entrega pacotes legíveis. Ele não substitui os workers nem o Hermes.

## 2. A fábrica separa fato, palpite e decisão

Logo no começo, a fábrica precisa responder:

"O que sabemos de verdade?"

Ela separa:

- o que veio da fonte;
- o que é inferência;
- o que já foi decidido;
- o que está em conflito;
- o que ainda está faltando.

Essa separação é o chão de tudo. Se a fábrica mistura essas coisas, o resto fica contaminado. Um palpite vira requisito. Uma lacuna vira escopo. Uma decisão antiga vira regra atual.

Quando a fábrica faz isso direito, o operador consegue corrigir cedo. Quando faz errado, o operador só percebe tarde, quando já tem código, docs, PR e desculpa.

## 3. Antes de plano, vem verdade do produto

A fábrica precisa montar a verdade do produto antes de mandar execução material.

O nome interno é Product SOT. Em português simples: é o documento que diz "é isto que estamos construindo".

Ele precisa deixar claro:

- qual é o produto ou fatia;
- para quem serve;
- que problema resolve;
- o que entra;
- o que não entra;
- que risco existe;
- que prova conta como aceite;
- que decisão ainda depende do operador.

Se o trabalho é grande, a fábrica também precisa checar a cobertura do escopo inteiro. Isso evita uma armadilha comum: executar a primeira parte visível e fingir que o produto todo ficou planejado.

## 4. O caminho muda conforme o tipo de trabalho

A fábrica não deveria tratar tudo como "tarefa para agente".

Um bug pede reprodução. Um incidente pede mitigação. Um release pede rollback. Uma tela pede prova de experiência. Uma mudança de segurança pede ameaça e fronteira. Um produto novo pede definição, decomposição e gates. Uma integração pede contrato e fallback. Um trabalho com Solana, carteira, assinatura ou dinheiro pede muito mais cuidado.

Por isso existem rotas e métodos.

O operador não precisa decorar os nomes. O que importa é que a fábrica precisa escolher a régua certa. A pergunta não é "qual agente pega isso?". A pergunta é "que tipo de risco e prova esse pedido exige?".

## 5. A fábrica verifica capacidade antes de fingir especialista

Nem todo produto cabe no mesmo conjunto de workers.

Web, API, CLI, cloud, agente, Solana, docs e onboarding têm cobertura mais madura no kernel público. Outros mundos, como mobile nativo, desktop, game, fintech, domínio regulado, analytics avançado, extensão de navegador e hardware, exigem pacotes de capacidade próprios antes de execução material.

Isso é importante. Bloquear porque falta capacidade é melhor do que deixar um agente genérico fingir que é especialista.

A fábrica boa não promete "faço tudo". Ela diz: "para isso eu tenho cobertura" ou "para isso eu preciso instalar e provar um pacote antes".

## 6. O trabalho vira unidades pequenas

Depois da verdade e do método, a fábrica quebra o trabalho.

Uma unidade boa tem dono, escopo, entrada, saída, prova, reviewer, dependência e regra de pronto. Uma unidade ruim é algo como "construir o produto".

Essa diferença muda tudo. Trabalho pequeno pode ser executado, revisado, repetido e fechado. Trabalho grande demais vira uma aposta.

Na prática, a fábrica transforma o produto em cards e pacotes de worker. Cada pacote diz o que o worker deve fazer e, principalmente, o que ele não pode fazer.

## 7. Hermes guarda o estado vivo

Hermes Kanban continua sendo a fonte de verdade do runtime. É lá que ficam cards, dependências, status, workers, workspaces, comentários, bloqueios e transições.

A fábrica não deve criar um segundo Hermes por fora. Ela prepara o contrato e reconcilia o estado, mas o trabalho vivo precisa aparecer no runtime.

Isso também vale para dependências. Se uma fase depende de uma unidade de trabalho, essa unidade precisa estar ligada no grafo. Se trabalho obrigatório aparece tarde, ele precisa entrar no grafo antes de a próxima fase andar.

A fábrica não pode descobrir uma obrigação depois e fingir que a fase anterior estava completa.

## 8. No-idle é guarda, não motor principal

No-idle existe para evitar silêncio perigoso.

Se tem coisa rodando, ele observa. Se tem coisa pronta, Hermes despacha. Se tem dependência, ele espera. Se precisa de decisão humana e o pacote está pronto, o gerente chama o operador. Se falta artefato, readback, PDF, revisão ou reparo interno, a fábrica repara.

O que ele não pode fazer: virar um despachante paralelo, inventar fase, aprovar gate, completar tarefa ou jogar bloqueio interno no humano.

No-idle bom não é barulho. É a garantia de que a fábrica não fica parada fingindo que está tudo bem.

## 9. Produto visível precisa de prova visível

Se o produto tem interface, não basta dizer que o backend está pronto.

A fábrica precisa de prova da cara do produto. Isso pode incluir tela, estados, jornada, erro, loading, viewport, acessibilidade básica, console, overflow, texto e comparação com o que foi prometido.

Para CLI, a prova é diferente: instalação, help, transcript, erro, comportamento no terminal.

Para docs, também é diferente: o leitor consegue chegar ao primeiro sucesso? Os links funcionam? O texto guia alguém de verdade?

A regra é simples: cada superfície pede um tipo de prova. Uma screenshot bonita não prova um produto inteiro. Mas sem prova da experiência, produto visível não está pronto.

## 10. Revisão precisa voltar para o trabalho

Review não é decoração.

Se a revisão passa, ela precisa destravar ou fechar a tarefa certa. Se falha, precisa criar reparo. Se encontra risco, precisa registrar. Se fica parada num comentário, é só teatro.

O executor não deve ser o juiz final do próprio trabalho quando o risco é material. A fábrica precisa consumir a revisão, não apenas gerar uma revisão.

## 11. Gate humano é decisão, não interrupção

A fábrica só deve chamar o humano quando a decisão é mesmo do humano.

Produção. Mainnet. Fundos. Segredo. Orçamento. Release. Risco residual. Waiver. Mudança de autoridade.

E quando chama, precisa entregar um pacote de decisão. Curto na frente, completo nos anexos. A pessoa precisa entender o que está aprovando sem abrir JSON cru ou caçar contexto no Kanban.

Um gate humano bom diz: "você está aprovando isto, com este risco, para permitir este próximo passo. Você não está aprovando aquilo".

## 12. Fechar é reconciliar

No fim, a fábrica compara o que era obrigatório com o que foi entregue.

Ela olha pedido, Product SOT, método, workers, evidências, revisão, gates, risco residual, release e próximo estado.

Se bate, fecha com Receipt Five.

Se não bate, bloqueia com motivo e dono.

Se a execução revelou uma falha da própria fábrica, vira learnback: teste novo, doc nova, skill nova, gate novo, issue ou mudança de processo. Mas isso também precisa de validação. A fábrica não deve se reescrever no escuro.

## 13. O que o operador deveria sentir

O operador não deveria sentir que está pilotando quarenta agentes.

Deveria sentir que existe uma linha de produção: o pedido entrou, a fábrica entendeu, o estado está claro, os bloqueios têm dono, as decisões chegam bem explicadas e "pronto" vem com prova.

Se a experiência vira cobrança manual, se o operador precisa detectar preguiça, se o humano precisa perguntar onde está a evidência, a fábrica falhou.

Esse é o padrão certo para ler qualquer parte da Overkill Factory.
