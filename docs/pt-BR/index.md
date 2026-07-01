# Overkill Factory

Sem a fábrica, você vira fiscal do agente.

Você pede uma coisa importante. O agente responde rápido, abre arquivo, move card, talvez passe teste, talvez diga que terminou. Só que ainda sobra a pergunta: entregou mesmo o que eu pedi ou só produziu movimento?

A Overkill Factory existe para tirar essa pergunta do improviso.

Você faz um pedido. A fábrica guarda o contexto original, entende o que é fato e o que é palpite, divide o trabalho em partes pequenas, manda os agentes trabalharem no Hermes e só chama de pronto quando existe prova.

O objetivo é tornar a velocidade confiável. Em português direto: andar rápido sem obrigar você a conferir tudo na mão.

## A ideia em uma frase

A Overkill Factory é uma camada de produção para trabalho com agentes: ela transforma pedidos vagos em trabalho pequeno, rastreável e provado.

O agente pode executar. Ele não pode inventar escopo, esconder risco, aprovar a si mesmo ou dizer "pronto" sem evidência.

## Um exemplo em 30 segundos

Você escreve:

> Quero lançar o onboarding novo amanhã.

A fábrica não deveria responder "ok, fazendo".

Ela primeiro segura o pedido e devolve algo mais útil:

> Entendi que você quer lançar o onboarding novo. Antes de executar, preciso confirmar o usuário do fluxo, o que conta como sucesso e se isso toca pagamento, carteira, dados sensíveis ou produção. Enquanto isso, já preservei a fonte, localizei o repo e vou preparar a definição do produto.

Essa é a diferença. A fábrica não tira a decisão do humano. Ela impede que um agente gaste horas construindo a coisa errada.

## Por onde ler

Se você quer entender o produto, leia assim:

1. [Manual](manual.md): por que a fábrica existe e o que ela tira das suas costas.
2. [Como a fábrica trabalha](operating-model.md): o que acontece depois que você manda um pedido.
3. [Confiança e prova](trust-and-evidence.md): como separar entrega real de teatro de progresso.
4. [Ciclo simples](lifecycle.md): o mapa curto do começo ao fim.

Se você vai operar ou manter o repo:

- [Uso](usage.md): comandos locais e o que eles provam.
- [Modelo técnico](technical-model.md): como Hermes, Factory, scripts, schemas e workers se encaixam.
- [Referência](reference.md): nomes e caminhos quando você já sabe o que procurar.

## O que esta documentação prova

Ela prova o contrato público do repositório: workflow compilado, rotas, métodos, schemas, workers, exemplos, validadores e testes.

Ela não prova que um produto privado foi entregue. Não prova que um Hermes vivo rodou um card real. Não prova aprovação humana em produção. Para isso, precisa de estado atual no Hermes, resultado de worker, evidência do produto, revisão consumida e autorização explícita quando houver risco.

Essa fronteira não é fraqueza. É o que impede a fábrica de virar mais um agente falando bonito.
