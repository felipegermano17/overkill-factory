# Como a fábrica trabalha

Veja o que acontece quando você manda um pedido.

O exemplo aqui é simples:

> Quero lançar o onboarding novo amanhã.

A resposta errada é abrir uma tarefa gigante e deixar um agente tentar resolver. Um pedido ainda não é plano. Primeiro a fábrica entende o que você realmente quer construir.

## O que entra

O pedido pode chegar por Telegram, Discord, cockpit, terminal, documento, repo, screenshot ou conversa antiga.

A entrada é só a porta. Ela não decide o produto. Ela não aprova risco. Ela não substitui o Hermes.

A primeira obrigação é guardar a fonte: mensagem original, anexos, links, repo, documentos e contexto.

Se a fábrica resume cedo demais, pode cortar justamente a frase que explicaria uma decisão depois.

## O que a fábrica responde primeiro

Uma boa primeira resposta não é "fazendo".

É algo como:

> Entendi que você quer lançar o onboarding novo. Antes de executar, preciso confirmar o usuário do fluxo, o que conta como sucesso e se isso toca pagamento, carteira, dados sensíveis ou produção. Já preservei a fonte e vou preparar a definição do produto.

Essa resposta já mostra três coisas: ela entendeu, não vai assumir no escuro e já sabe o próximo passo seguro.

## Separar fato de palpite

Depois ela separa o que veio da fonte do que seria palpite.

Fato: você pediu onboarding novo.

Inferência: talvez seja para usuário final, mas isso precisa de fonte.

Decisão: se você já aprovou Figma ou escopo em outro documento, isso entra como decisão.

Conflito: se um doc fala em KYC e outro diz sem KYC, isso não pode ser escondido.

Lacuna: se ninguém sabe o que conta como sucesso, isso precisa ser resolvido.

Sem essa separação, o agente pode trabalhar muito em cima de uma suposição.

## Definir o produto

Agora a fábrica define o que será entregue.

Para o onboarding, ela precisa dizer: quem passa pelo fluxo, onde começa, onde termina, quais telas ou comandos existem, quais estados precisam aparecer, quais riscos importam e que prova fecha o trabalho.

Essa definição é a verdade do produto. Internamente pode aparecer como Product SOT.

O nome importa menos que a função: impedir que cada worker invente uma versão diferente do produto.

## Escolher a régua

Depois vem a rota.

Se o pedido é bug, a régua é reprodução e regressão.

Se é release, é prontidão, rollback, dono e monitoramento.

Se é interface, é jornada, estados e prova visual.

Se é segurança, é fronteira, ameaça, permissão, segredo e revisão.

Se toca Solana, carteira, assinatura, fundos ou mainnet, o cuidado sobe.

A rota diz que tipo de trabalho é. O método diz como provar.

## Checar capacidade e autoridade

Antes de mandar worker, a fábrica confere se tem capacidade e autoridade.

Tem worker certo? Tem acesso? Tem pack para essa superfície? Precisa de especialista? Toca produção? Toca dinheiro? Precisa de decisão humana?

Se falta capacidade, bloqueia.

Se falta decisão humana, prepara pacote.

Se falta só reparo interno, como readback, anexo, revisão ou evidência, a fábrica trabalha. Não joga isso no operador.

## Quebrar em trabalho pequeno

A fábrica então transforma o produto em unidades pequenas.

Uma unidade boa tem entrada, saída, dono, dependência, prova, reviewer e regra de pronto.

Uma unidade ruim diz: "construa o onboarding".

Para o exemplo, as unidades poderiam ser:

- confirmar escopo e sucesso do onboarding;
- implementar tela inicial e estados;
- ligar API necessária;
- testar jornada feliz e erro;
- revisar risco;
- anexar evidência visual;
- preparar release ou bloqueio.

Cada worker recebe só a parte dele e devolve prova.

## Onde o trabalho aparece

Hermes Kanban continua sendo a fonte de verdade do runtime.

O quadro do Hermes é onde o trabalho vivo aparece: cards, dependências, status, workers, workspaces, comentários, anexos, bloqueios e transições.

A Factory não mantém um quadro secreto por fora. Ela cobra o contrato, mas a execução precisa estar visível no Hermes.

## Quando o quadro parece parado

Quando o quadro parece parado, a fábrica precisa descobrir se é espera legítima ou travamento.

Se há dependência real, espera.

Se há trabalho pronto, despacha.

Se falta decisão humana e o pacote está pronto, chama o operador.

Se falta readback, artefato, revisão ou evidência, repara.

O guard de no-idle existe para isso. Ele não é outro Hermes e não inventa autoridade.

## Como a fábrica prova

A prova muda conforme o trabalho.

Para web: screenshots, estados, console, viewport, erro, loading, overflow e jornada.

Para CLI: instalação, help, comando real, saída e erro.

Para release: prontidão, rollback, dono e decisão.

Para docs: clareza, navegação e primeiro sucesso do leitor.

Prova boa responde ao pedido. Prova ruim só mostra atividade.

## Como revisão vira avanço

Review não é comentário decorativo.

Se passa, destrava ou fecha o item certo.

Se falha, cria reparo.

Se aponta risco, registra dono e consequência.

Se pede decisão, vira pacote humano.

Review que não muda estado não foi consumido.

## Como termina

A execução termina em três estados honestos.

Entregue: há prova, revisão consumida, gates resolvidos e próximo estado claro.

Bloqueado: falta prova, acesso, autoridade, capacidade ou segurança. O bloqueio tem dono e menor próximo passo seguro.

Aprendizado: a execução mostrou que a própria fábrica precisa mudar. Isso pode virar teste, doc, skill, worker, gate, issue ou mudança de processo.

A fábrica boa não força final feliz. Ela diz a verdade operacional.
