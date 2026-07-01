# Overkill Factory

A Overkill Factory é uma resposta para um problema que aparece rápido quando começamos a usar agentes para trabalho sério.

Você pede uma coisa importante. O agente entende uma parte, completa outra parte com palpite, faz bastante barulho, talvez abra arquivos, talvez passe testes, talvez diga que terminou. Só que, no fim, você ainda precisa perguntar: "isso entregou mesmo o produto que eu pedi?".

A fábrica existe para tirar essa pergunta do improviso.

Ela pega um pedido e transforma em produção controlada: fonte preservada, verdade do produto, caminho escolhido, trabalho dividido, execução no Hermes, prova, revisão, decisão humana quando precisa e fechamento honesto.

O objetivo é tornar a velocidade confiável. Não é fazer agente correr mais. É fazer cada avanço deixar rastro suficiente para alguém confiar, revisar ou bloquear.

## O que ler primeiro

Se você está chegando agora, não comece pelo modelo técnico. Comece pela pergunta que você tem na cabeça.

- [Manual](manual.md): "o que é essa fábrica e por que ela existe?"
- [Como a fábrica trabalha](operating-model.md): "o que acontece depois que eu mando um pedido?"
- [Confiança e prova](trust-and-evidence.md): "como eu sei que isso não é só teatro de agente?"
- [Ciclo simples](lifecycle.md): "qual é o caminho do começo ao fim?"

Depois, se você for operar ou manter o repo:

- [Uso](usage.md): comandos para provar o checkout local.
- [Modelo técnico](technical-model.md): como Hermes, workers, schemas, adapters e validadores se encaixam.
- [Referência](reference.md): nomes e caminhos para consulta rápida.

## A versão curta

A fábrica não confia em frase bonita. Ela confia em fonte, escopo, método, trabalho pequeno e prova.

Um pedido não deveria virar código antes de virar entendimento. Um release não deveria sair porque alguém escreveu "pass". Um gate humano não deveria ser uma pergunta vaga no chat. Um worker não deveria julgar o próprio trabalho. E um bloqueio interno da fábrica não deveria cair no colo do operador como se fosse decisão humana.

Se a fábrica funciona, o operador não fica caçando evidência. Ele recebe estado claro, decisão clara e recibo claro.

## O que esta documentação prova

O kernel público atual está na versão `3.0.2`. Ele tem workflow compilado, rotas, métodos, schemas, workers, exemplos, validadores e testes.

Isso prova uma coisa específica: o repositório público tem um contrato verificável.

Não prova que uma execução privada terminou. Não prova que um produto vivo foi entregue. Não prova aprovação humana em produção. Para isso, precisa de estado real no Hermes, resultados atuais de workers, evidência do produto, revisão consumida e autorização explícita quando houver risco.

Essa fronteira é parte do produto. A fábrica só vale se souber dizer o que sabe e o que ainda não sabe.
