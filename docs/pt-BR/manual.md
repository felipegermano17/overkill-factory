# Manual do produto

Se você me perguntasse no chat "o que é a Overkill Factory?", eu não começaria falando de schema, worker, registry ou fase.

Eu começaria assim: é uma forma de fazer agentes trabalharem sem virar bagunça.

Você pede uma coisa. Pode ser um produto novo, uma correção, um release, uma revisão de segurança, uma tela, um fluxo, uma integração, uma operação em produção. Um agente comum tenta resolver direto. Às vezes acerta. Muitas vezes ele parece ocupado, escreve bastante, move alguma coisa, entrega um resumo bonito e deixa o problema real no mesmo lugar.

A Overkill Factory existe para evitar esse teatro.

Ela transforma um pedido em produção controlada. Primeiro entende a fonte. Depois define o produto. Depois escolhe o caminho. Depois divide o trabalho. Depois manda os workers certos pelo Hermes. Depois cobra prova. Depois revisa. Depois fecha, bloqueia ou aprende.

Isso é a fábrica.

## O problema que ela resolve

O problema não é "agente erra". Isso todo mundo já sabe.

O problema é pior: agente erra de um jeito que parece certo.

Ele escreve um arquivo, mas o arquivo não resolve o pedido. Ele passa um teste, mas o teste não cobre o comportamento importante. Ele diz que revisou, mas não leu o artefato certo. Ele marca uma tarefa como pronta, mas a evidência não existe. Ele pede aprovação humana, mas não entrega o material que a pessoa precisa aprovar.

Aí o operador vira fiscal. Tem que perguntar: isso está mesmo pronto? Quem revisou? Onde está a prova? Esse bloqueio é meu ou é trabalho da fábrica? Esse "pass" vale alguma coisa?

Esse é o trabalho que a fábrica precisa tirar das costas do operador.

## A ideia em uma frase

A fábrica não deixa um pedido virar execução antes de virar verdade, método, trabalho pequeno e prova.

Essa frase é o centro do produto.

Sem verdade, o agente constrói em cima de mal-entendido.

Sem método, todo pedido vira a mesma tarefa genérica.

Sem trabalho pequeno, ninguém sabe revisar.

Sem prova, "pronto" é só uma opinião.

## O que entra na fábrica

Pode entrar quase qualquer sinal de trabalho:

- "cria esse produto";
- "corrige esse bug";
- "prepara esse release";
- "revisa essa mudança perigosa";
- "descobre por que isso parou";
- "transforma esse repo em algo publicável";
- "faz essa tela ficar usável";
- "prepara um fluxo com carteira, assinatura ou dinheiro";
- "melhora esse worker porque ele está sendo raso".

A fábrica não deveria responder a tudo com a mesma receita. Bug precisa de reprodução. Release precisa de rollback. Interface precisa de prova visual. Segurança precisa de arquitetura. Produto novo precisa de verdade de produto. Mainnet, fundos, segredos e produção precisam de autoridade humana explícita.

## A primeira obrigação: entender antes de fazer

Quando o pedido entra, a fábrica precisa proteger a fonte.

Isso quer dizer: guardar o que foi pedido de verdade, separar fato de suposição, marcar conflito, listar lacuna e dizer o que ainda não pode ser assumido.

Parece básico. Não é. É onde muito trabalho com agente começa a morrer.

Um resumo malfeito vira plano. Um plano malfeito vira execução. Uma execução malfeita vira uma entrega que parece pronta, mas nasceu torta.

A fábrica tenta quebrar essa sequência logo no começo.

## A verdade do produto

Depois da fonte vem a verdade do produto. O nome interno é Product SOT. Pode esquecer o nome por um segundo. A pergunta é simples:

"Que produto estamos construindo, exatamente?"

Não basta dizer "um dashboard", "um app", "um onboarding" ou "um agente". A fábrica precisa saber para quem é, que problema resolve, o que entra, o que fica fora, quais promessas precisam ser cumpridas, que risco existe e que prova vai contar.

Sem isso, um worker pode trabalhar muito e ainda entregar a coisa errada.

Quando o trabalho é um produto inteiro, a fábrica também precisa olhar a cobertura do escopo. A primeira fatia prática não pode virar "o produto" só porque foi a parte mais fácil de executar. Cada promessa importante precisa ter destino: planejada, bloqueada com dono, fora de escopo com justificativa, decidida pelo humano ou provada.

## A fábrica escolhe o caminho

Depois de entender o produto, a fábrica escolhe o caminho.

Um bug não anda como um release. Um release não anda como uma tela. Uma tela não anda como uma mudança de chave. Uma integração crítica não anda como uma alteração de texto.

A fábrica tem rotas e métodos para isso. O leitor não precisa decorar os nomes. O ponto é outro: a fábrica precisa escolher a régua certa antes de distribuir trabalho.

Se é bug, cadê a reprodução?

Se é produto, cadê a definição?

Se é interface, cadê a jornada e os estados?

Se é segurança, cadê a ameaça e a fronteira?

Se é produção, cadê rollback, dono e monitoramento?

Essa escolha muda o que será pedido aos workers e muda o que vai contar como prova.

## Workers não são personagens

Um worker não deveria ser "um agente esperto com um prompt bom".

Na fábrica, worker é papel com limite. Ele recebe um pacote pequeno dizendo o que fazer, o que não fazer, o que devolver e que autoridade ele não tem.

Isso vale para quem planeja, quem constrói, quem testa, quem revisa, quem faz segurança, quem prepara release, quem reconcilia evidência e quem registra decisão humana.

O worker pode ter autonomia dentro da faixa. Fora da faixa, ele bloqueia.

Esse limite é o que permite velocidade sem entregar o volante inteiro para o agente.

## Hermes é o chão da fábrica

O Hermes guarda o estado vivo: cards, dependências, workers, comentários, workspaces, bloqueios e transições.

A Overkill Factory não tenta substituir isso. Ela define o contrato de produção: que artefatos precisam existir, que gates bloqueiam, que worker entra, que prova precisa voltar, que decisão é humana e o que não pode ser autorizado por um agente.

Essa separação é saudável.

Hermes mostra o que está acontecendo.

A fábrica diz o que pode acontecer com segurança.

## Pronto quer dizer provado

Aqui está a regra mais importante: pronto quer dizer provado.

Não quer dizer "o worker disse que terminou".

Não quer dizer "um arquivo apareceu".

Não quer dizer "o teste que ele mesmo escolheu passou".

Não quer dizer "alguém aprovou no chat sem ver o material".

Pronto quer dizer que a fábrica consegue apontar para o pedido, para a mudança, para a evidência, para a revisão e para o próximo estado.

O nome interno desse recibo é Receipt Five. Ele não é burocracia. Ele é o freio contra conclusão falsa.

## Quando o humano entra

O humano entra quando a decisão é realmente dele.

Produção. Mainnet. Fundos. Segredos. Orçamento. Risco material. Release. Waiver. Mudança que pode afetar cliente, dinheiro, segurança ou reputação.

Mas a fábrica não deveria chamar o humano para resolver bagunça interna. Se falta readback, se falta PDF, se falta artefato, se falta revisão, se um worker foi raso, isso é trabalho da fábrica.

Quando existe gate humano de verdade, ele precisa vir como pacote de decisão. Uma mensagem curta, em português claro, dizendo:

- que decisão está sendo pedida;
- que material está em revisão;
- o que aprovar permite;
- o que aprovar não permite;
- quais são as opções;
- qual é o risco;
- qual é o próximo passo seguro.

JSON cru não é gate humano. Pergunta vaga no chat também não.

## Um exemplo simples

Você pede: "cria o onboarding do cliente".

Um agente comum pode começar a desenhar tela.

A fábrica deveria parar e perguntar, mesmo que internamente:

Quem é o cliente? O que ele precisa conseguir fazer no primeiro uso? Tem conta? Tem permissão? Tem carteira? Tem pagamento? Tem dado sensível? Tem design pronto? O que conta como sucesso? O que não entra agora?

Depois disso, a fábrica separa o trabalho:

- alguém define a verdade do fluxo;
- alguém planeja a experiência;
- alguém implementa a tela;
- alguém implementa API ou dados, se houver;
- alguém testa a jornada;
- alguém olha a prova visual;
- alguém revisa;
- alguém fecha com evidência.

O operador não deveria coordenar tudo isso na mão. Ele deveria receber o estado claro e ser chamado apenas quando houver decisão real.

## O que a fábrica ainda precisa provar

A documentação pública prova a intenção e o contrato do kernel. Os testes locais provam que o repositório está coerente.

Isso não é a mesma coisa que dizer que uma execução privada, num Hermes vivo, entregou um produto específico.

Para isso, precisa de estado real no Hermes, worker results atuais, evidência do produto, revisão consumida e decisão humana quando o risco pedir.

Essa fronteira é importante. A fábrica não fica mais fraca por dizer isso. Ela fica mais confiável.

## Se você só lembrar de uma coisa

A Overkill Factory é uma tentativa de transformar agentes em linha de produção confiável.

Não é mágica. Não é um agente único. Não é um prompt gigante.

É um jeito de impedir que velocidade vire chute.

Pedido entra. A fábrica entende, organiza, executa, prova, revisa e fecha.

Quando não consegue provar, ela não finge. Ela bloqueia e diz o que falta.
