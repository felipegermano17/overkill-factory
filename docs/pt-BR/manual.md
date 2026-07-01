# Manual

A Overkill Factory é uma camada de produção para trabalho com agentes.

Ela transforma pedidos vagos em trabalho pequeno, rastreável e provado.

A ideia é simples: o agente pode executar, mas não pode inventar escopo, esconder risco, aprovar o próprio trabalho ou dizer "pronto" sem prova.

Isso é produção controlada.

## Para quem isso existe

Existe para quem usa agentes em produto, código, release, revisão, operação, incidente ou documentação e cansou de virar fiscal do processo.

Você não quer ficar perguntando toda hora:

- ele entendeu o pedido?
- isso era fato ou palpite?
- quem revisou?
- que teste prova o comportamento certo?
- esse risco foi aceito por alguém?
- esse bloqueio é meu ou é trabalho da fábrica?

Se você precisa fazer essas perguntas manualmente, o agente pode até ajudar, mas a operação ainda depende demais de você.

A fábrica existe para mudar isso.

## O problema real

Agente falhando claramente é fácil de lidar. O comando quebra. O teste falha. O arquivo não existe.

O problema é o agente que erra com aparência de progresso.

Ele entrega um plano bonito baseado num resumo ruim. Cria uma tela que não cobre erro, vazio, permissão ou mobile. Passa um teste que não prova o risco. Marca revisão como feita, mas ninguém consumiu o resultado. Pede aprovação humana com uma pergunta vaga: "posso seguir?".

Aí você vira gerente, QA, auditor e detetive.

A Overkill Factory tenta impedir esse tipo de progresso falso.

## O que ela faz antes de executar

Antes de deixar um agente sair fazendo, a fábrica precisa responder algumas perguntas.

O que chegou como fonte original?

O que é fato?

O que é palpite?

Qual produto ou mudança está sendo pedido?

Que tipo de trabalho é esse: bug, release, incidente, tela, segurança, integração, documentação, produto novo?

Quem pode executar?

Quem pode aprovar?

Que prova vai contar?

Se essas respostas não existem, executar é aposta.

## Um exemplo: onboarding novo

Você escreve:

> Cria o onboarding do cliente.

Um agente solto pode começar pela tela. Parece produtivo, mas pode estar errado desde o primeiro minuto.

A fábrica segura o pedido.

Ela procura a fonte. Separa o que veio de você do que seria palpite. Pergunta ou descobre quem é "cliente" nesse contexto. Verifica se onboarding significa criar conta, conectar carteira, passar por KYC, assinar transação, fazer primeiro depósito ou só chegar a uma tela inicial.

Ela também olha risco: toca pagamento? toca dados sensíveis? toca produção? toca mainnet? existe Figma? existe backend? existe design system? o que conta como sucesso?

Depois disso, o trabalho pode virar unidades menores:

- definir a verdade do fluxo;
- implementar a tela;
- implementar API, se houver;
- testar a jornada;
- revisar risco e escopo;
- anexar prova visual;
- fechar com recibo.

O operador não deveria coordenar tudo isso na mão.

## O que você recebe

Quando a fábrica funciona, você recebe coisas que ajudam a decidir.

Uma leitura do pedido: o que foi entendido, o que falta e o que não será assumido.

Uma definição do produto: o que será entregue, para quem, com quais limites e que prova vai contar. Internamente isso pode aparecer como Product SOT, mas o ponto é simples: é a verdade do produto.

Um plano pequeno: tarefas com dono, dependência, evidência e reviewer.

Status no Hermes: cards, bloqueios, workspaces, anexos e transições visíveis.

Pedidos humanos bons: quando a decisão é sua, você recebe contexto, opções e consequência.

Um recibo final: o que foi pedido, o que foi feito, que prova existe, quem revisou e o que ainda falta.

## Quando a fábrica chama o humano

A fábrica chama o humano quando a autoridade é humana.

Produção. Mainnet. Fundos. Segredos. Orçamento. Release. Risco residual. Waiver. Mudança de poder.

Ela não deveria chamar você porque esqueceu readback, não anexou prova, deixou review parado ou recebeu entrega rasa de worker. Isso é trabalho dela.

Pedido ruim de aprovação:

> Posso seguir para produção?

Pedido bom:

> Você está aprovando o release do onboarding v2 para produção. Inclui cadastro, validação de email e tela de erro. Não inclui pagamento, KYC ou convite por equipe. Provas: testes X, screenshots Y, revisão Z. Risco restante: analytics ainda sem evento de abandono. Se aprovar, faço deploy. Se recusar, mantenho em staging e abro reparo.

Essa diferença é produto.

## O que significa pronto

Pronto não é "o agente disse que terminou".

Pronto é: pedido entendido, trabalho feito, prova anexada, revisão consumida e próximo estado claro.

O recibo interno disso é o Receipt Five.

Ele precisa responder:

1. o que foi pedido;
2. o que foi feito ou decidido;
3. que prova sustenta isso;
4. quem revisou e o que disse;
5. o que ainda falta, bloqueia ou fica como risco.

Se isso não existe, a entrega pode estar em revisão, bloqueada, parcial ou aguardando decisão. Mas pronta, não.

## Onde entra o Hermes

Hermes é onde o trabalho vivo aparece.

Cards, status, dependências, comentários, workspaces, anexos, bloqueios e transições ficam ali.

A Overkill Factory é o contrato de produção em volta desse trabalho: o que precisa existir antes de avançar, quem pode executar, que prova precisa voltar, quem revisa e que decisão exige humano.

Hermes mostra o chão da fábrica. A Factory define as regras para esse chão não virar bagunça.

## O que ela não promete

Ela não promete que agentes nunca erram.

Ela não substitui decisão humana.

Ela não transforma teste local em prova de produto vivo.

Ela não deveria fingir que um pedido vago virou produto completo se ainda faltam fonte, autoridade, capacidade ou evidência.

A promessa é outra: tornar erro, lacuna, risco e bloqueio visíveis cedo o bastante para você não descobrir tarde demais.

## Próximo passo

Se você quer ver o pedido andando por dentro, leia [Como a fábrica trabalha](operating-model.md).

Se quer entender como ela separa entrega real de teatro de progresso, leia [Confiança e prova](trust-and-evidence.md).

Se quer provar o checkout local, vá para [Uso](usage.md).
