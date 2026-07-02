# Manual Da Overkill Factory

A Overkill Factory e uma fabrica de produto operada por agentes de IA.

Ela existe porque pedir para um agente "faz um produto" e perigoso quando nao existe processo de producao em volta do agente. Um agente capaz ainda pode entender errado, comecar a codar cedo demais, inventar requisito, esquecer risco, dizer que terminou sem prova, esconder uma decisao humana dentro de status ou produzir documentos bonitos que nao ajudam ninguem a construir nem verificar o produto.

A Factory tenta tornar o trabalho com IA controlavel. Ela nao torna IA perfeita. Ela torna o trabalho visivel, limitado, revisavel e auditavel.

A ideia central e:

Pedido bruto -> entendimento da fonte -> verdade do produto -> metodo -> plano -> unidades de trabalho -> cards Hermes -> execucao por workers -> evidencia -> revisao -> Receipt Five -> release, bloqueio ou learnback.

## A Factory Nao Comeca Construindo

O primeiro comportamento profissional e freio.

Um agente comum ouve "quero um app" e cria arquivos. A Factory nao deveria fazer isso. Ela primeiro pergunta ou deduz as poucas coisas que mudam produto, risco ou autoridade:

- para quem e o produto,
- qual problema resolve,
- qual resultado provaria sucesso,
- se envolve login, dado sensivel, dinheiro, blockchain, pagamento, producao, conta externa ou risco juridico,
- se repo, design, ambiente e acesso ja existem,
- quem pode aprovar risco, custo, producao, segredo, fundo ou mainnet.

A Factory nao deve fazer questionario burocratico. Ela deve perguntar quando a resposta muda algo importante. Se o proximo passo e seguro e claro, ela continua. Se o proximo passo exige autoridade real, ela para e pergunta com clareza.

Construir cedo demais e uma das principais fontes de erro. Se o entendimento inicial estiver errado, todo artefato depois disso fica errado com confianca.

## A Factory Trabalha Com Artefatos

Artefato e qualquer coisa concreta que registra ou prova algo:

- Product SOT,
- contrato JSON,
- card Kanban,
- worker packet,
- saida de teste,
- screenshot,
- pull request,
- resultado de revisao,
- pacote de human gate,
- prova de release,
- Receipt Five.

A Factory nao confia em frases vagas como "entendi", "parece bom", "pronto", "quase" ou "confia". Se a proxima etapa depende de uma informacao, essa informacao precisa estar registrada em algum lugar que outra pessoa ou agente consiga inspecionar.

Essa e a primeira disciplina: estado importante nao pode viver so na cabeca do agente.

## Fonte, Fato, Suposicao E Decisao Sao Coisas Diferentes

Uma conversa contem varios tipos de informacao: fatos, preferencias, exemplos, chutes, correcoes, duvidas, riscos e decisoes. Se tudo fica misturado, a Factory vira caos com uma interface melhor.

A Factory separa:

- fonte: material bruto vindo do operador, documento, repo, link, issue ou mensagem,
- fatos: coisas confirmadas pela fonte ou pelo operador,
- suposicoes: coisas que podem ser verdade, mas nao foram confirmadas,
- inferencias: conclusoes tiradas pela Factory,
- conflitos: fontes que discordam,
- perguntas: respostas faltantes que mudam produto, risco ou execucao,
- decisoes: escolhas que o dono do produto realmente fez.

Exemplo: "quero um app tipo Nubank para investimentos crypto" prova uma direcao de experiencia. Nao prova custodia, trading, escopo regulatorio, movimentacao de dinheiro ou quem pode assinar transacoes. Tratar essas suposicoes como fatos seria perigoso.

## Product SOT E A Verdade Oficial Do Produto

SOT significa Source of Truth. Product SOT e o documento que responde: que produto estamos construindo?

Ele deve nomear produto, publico, problema, resultado esperado, escopo, fora de escopo, restricoes, riscos, dependencias, decisoes ja tomadas, perguntas abertas, criterios de sucesso, limites de autoridade e aprovacoes humanas obrigatorias.

Sem Product SOT, cada worker pode construir um produto diferente:

- frontend imagina uma experiencia,
- backend imagina outro modelo de dados,
- seguranca revisa outra superficie de ameaca,
- docs explicam outra promessa,
- release prepara outro ambiente.

Product SOT nao e enfeite. E a verdade compartilhada que impede a linha de producao de virar varios chutes em paralelo.

## Resultado, Escopo E Metodo Vem Antes Da Execucao

A Factory nao pergunta so o que fazer. Ela pergunta qual transformacao importa.

"Criar dashboard" e fraco. Melhor: "um operador abre uma tela, ve pedidos pendentes, filtra por status e exporta CSV sem abrir o banco."

Esse resultado mostra:

- quem usa,
- o que essa pessoa faz,
- como sucesso sera provado,
- qual evidencia deve existir,
- o que seria fracasso.

Depois a Factory cobre o escopo. Ela procura buracos: login, admin, estado vazio, erro, loading, mobile, documentacao, deploy, rollback, seguranca, observabilidade, acesso, secrets, testes, migracao e onboarding.

Depois ela escolhe o Method Contract. Metodo e a regra de como esse tipo de trabalho sera construido e provado.

Corrigir typo nao exige o mesmo processo de lancar token mainnet. Prototipo local nao exige a mesma autoridade de producao. Reescrever documentacao publica nao exige a mesma prova de um sistema que mexe com dinheiro.

O Method Contract define fases, workers, gates, evidencia, acoes proibidas, autoridade humana, risco e nivel de prova.

## Experiencia Do Produto Faz Parte Do Produto

A Factory nao trata produto como "backend mais codigo". Produto tem rosto:

- web,
- mobile,
- CLI ou TUI,
- documentacao,
- chat,
- carteira/onchain,
- painel admin,
- onboarding,
- estados de erro e vazio.

Product Face Packet e o plano da superficie do produto. Product Face Result e a prova de que a superficie existe e foi verificada.

"Frontend pronto" nao basta. Para trabalho visual, a Factory deve esperar screenshots, desktop e mobile, jornada principal, botoes funcionando, erros, console saudavel, acessibilidade basica, overflow e evidencia de design system.

Para CLI vale o mesmo: instalacao, help, comando real, saida, erro util e comportamento no terminal.

## Arquitetura Precisa Ajudar A Execucao

Arquitetura responde: quais pecas existem e como elas conversam?

Ela deve identificar frontend, backend, banco, filas, login, storage, APIs externas, pagamento, smart contracts, admin, deploy, observabilidade e rollback quando relevante.

Boa arquitetura diz aos workers o que construir, onde os dados ficam, quem chama quem, quem acessa o que, onde estao secrets, quais fronteiras importam, como testar, monitorar e recuperar.

Arquitetura decorativa e inutil. Arquitetura que nao ajuda execucao, seguranca ou verificacao e ruido.

## Seguranca, Acesso E Orcamento Entram Cedo

Seguranca nao e scanner no final. Comeca antes da execucao.

A Factory deve detectar dado sensivel, login, permissoes, abuso, prompt injection, risco de agente com ferramenta, supply chain, chave, token, wallet, assinatura, dinheiro, producao, custo cloud, API paga, GPU, mainnet ou contas externas.

Se falta capacidade, a Factory nao deve jogar o problema imediatamente para o operador. Primeiro tenta aquisicao segura de capacidade: skill, provider, referencia, CLI, docs, exemplo, smoke test ou capability pack.

Mas segredo, dinheiro, producao, billing, conta, fundo, assinatura e mainnet exigem autoridade humana explicita.

## Work Units E Worker Packets Limitam A Execucao

Product Creation Plan liga a verdade do produto ao trabalho executavel. Ele decide ordem, dependencias, paralelismo, workers, prova, gates e definicao de pronto.

O plano vira work units. Uma work unit ruim diz: "fazer backend." Uma boa diz: "criar POST /orders com validacao X, persistencia Y, teste Z, sem deploy, com saida pytest e exemplo curl."

Cada work unit define objetivo, escopo, fora de escopo, entrada, saida, worker, reviewer, risco, autoridade, acoes proibidas, dependencias, done e evidencias obrigatorias.

Depois vira card Hermes e worker packet. O packet diz ao worker quem ele e, o que pode fazer, quais fontes usar, o que nao pode fazer, quais testes rodar e como devolver evidencia.

A Factory nao depende do "bom senso" do worker. Ela da trilho.

## Hermes E O Chao De Fabrica

O repositorio define o kernel. Hermes e onde o trabalho vivo acontece.

Hermes fornece sessoes, ferramentas, Kanban, perfis, workers, gateways, Telegram ou Discord, cron, logs, memoria, execucao e evidencia.

Hermes Kanban continua sendo a fonte de verdade de runtime. Chat pode explicar status, mas o trabalho precisa aparecer no estado vivo. Se Telegram diz "feito", mas nao ha card, evidencia e Receipt Five, nao esta feito. Se o Kanban tem bloqueio e o operador nunca recebeu a decisao, a Factory falhou na interface.

## A Ponte Do Gerente Nao Executa Trabalho Da Factory

O `overkill-factory-gerente` e a recepcao entre a conversa humana e o chao da Factory. Ele ajuda o operador a perguntar, iniciar, decidir, mudar ou entender trabalho, mas ele must not execute factory work.

Os bridge modes sao:

- `status_bridge`: explicar estado atual por evidencia e referencias de runtime,
- `start_bridge`: transformar um pedido novo em `factory_bridge_start_request`,
- `question_bridge`: responder perguntas sem mutar a Factory,
- `decision_bridge`: registrar decisoes humanas explicitas,
- `change_bridge`: rotear mudancas para o caminho correto da Factory,
- `exception_bridge`: expor situacoes inseguras, ambiguas ou bloqueadas,
- `handoff_bridge`: preservar contexto quando precisa handoff,
- `learnback_forwarding`: mandar licoes reais para o loop de aprendizado.

A ponte pode preparar ou rotear mensagens, mas o `factory-orchestrator` controla a execucao da Factory. A ponte usa o Durable Operator Inbox para decisoes humanas e mensagens pendentes nao se perderem entre chat, Hermes e default Hermes store.

The bridge cannot approve, execute or mutate factory work on behalf of the operator.

Factory Mechanic remains the self-improvement owner. A ponte pode reportar atrito, mas nao reescreve a Factory silenciosamente.

## Estados Do Trabalho Importam

Estados basicos:

- Todo: a tarefa existe, mas nao esta pronta,
- Ready: um worker pode pegar,
- Running: alguem esta executando,
- Blocked: nao pode continuar com seguranca,
- Review: precisa de verificacao independente,
- Done: saida, evidencia, criterios, revisao e risco foram tratados o suficiente para a proxima etapa consumir.

Done nunca deve significar "o worker disse que acabou". Done significa que a saida existe, a evidencia existe, os criterios foram cumpridos, a revisao passou quando exigida, riscos foram tratados e a proxima etapa consegue usar o resultado.

## Bloqueado Nao E Fracasso

Bloqueio real e saudavel quando protege o produto.

Bons bloqueios:

- producao sem aprovacao,
- mainnet sem autoridade de fundos/assinatura,
- Product SOT travado por conflito de fonte,
- worker declarou artefato inexistente,
- evidencia nao sustenta a conclusao.

Bloqueios ruins:

- "depende do usuario" sem pergunta clara,
- precisa de review mas ninguem criou a tarefa,
- falta artefato mas ninguem criou repair,
- card parado porque ninguem olhou,
- pronto sem prova.

A Factory deve diferenciar bloqueio honesto de espera passiva.

## No-Idle Evita Parada Silenciosa

No-idle significa que a Factory nao deve ficar parada quando pode avancar com seguranca.

Ela deve perceber work ready sem worker, running morto, bloqueio reparavel, review PASS nao consumido, artefato declarado inexistente, gate humano escondido, dependencia invertida e trabalho obrigatorio fora do grafo.

Se o problema e interno, a Factory repara ou despacha. Se a decisao e humana de verdade, entrega uma pergunta clara. Ela nao deve esperar o operador perguntar "e ai?"

## Human Gate E Autoridade, Nao Educacao

Human gate aparece quando a Factory precisa da autoridade do dono:

- gastar dinheiro,
- usar producao,
- mudar escopo,
- aceitar risco residual,
- usar secrets,
- mexer em fundos,
- assinar,
- mainnet,
- arquitetura de alto impacto,
- publicacao sensivel,
- acao destrutiva.

Human gate ruim pergunta "aprova?" sem contexto.

Human gate bom entrega pacote: decisao exata, opcoes, consequencias, recomendacao, riscos, o que aprova, o que nao aprova, evidencia e formato de resposta.

O humano nao deve ser chamado para tarefas da Factory como "esqueci de ler arquivo" ou "nao criei review". Isso e responsabilidade da fabrica.

## Revisao, Readback E Evidencia Sao O Motor De Confianca

A Factory nao deve deixar executor aprovar o proprio trabalho.

Reviewer verifica card, evidencia, teste, escopo, acoes proibidas, seguranca, docs, utilidade do output e risco residual.

Readback e conferir a realidade. Se um worker diz que criou arquivo, a Factory le. Se diz que rodou teste, confere saida. Se diz que a UI esta boa, confere screenshot, viewport, console e jornada.

Evidencia solta nao basta. O evidence-reconciler pergunta: esta evidencia sustenta esta conclusao?

Um log existe, mas prova o que? Uma screenshot existe, mas mostra o fluxo pedido? Um teste passou, mas cobre o risco certo? Um PR abriu, mas o CI passou?

## Receipt Five Fecha O Ciclo

Receipt Five e o recibo de entrega. Ele responde:

1. O que foi pedido?
2. O que foi produzido?
3. Qual evidencia sustenta?
4. Quem revisou?
5. Qual e o estado final: aceito, bloqueado, precisa reparo ou risco restante?

Receipt Five evita "done" vazio. Ele permite que alguem depois inspecione a entrega sem confiar na confianca do agente original.

## Release E Serio

Release e quando algo sai do ambiente seguro: merge em main, deploy, publicacao de docs, tag, GitHub Release, bot em producao, contrato, versao publica ou mainnet.

A Factory deve saber o que esta sendo lancado, para quem, em qual ambiente, como provar que esta vivo, como reverter, quem e dono, quais riscos restam, se CI passou, se docs estao coerentes e se URL ou objeto final foi verificado.

Release profissional em GitHub publico nao para em "PR aberto". Se escopo esta completo e aprovado, o ciclo inclui merge, fechar issue, limpar branch, sincronizar main, tag/release quando aplicavel e verificacao final.

## Learnback Melhora A Factory

Toda falha real deve melhorar a fabrica:

- gate escondido vira regra,
- worker raso vira quality firewall,
- card parado vira no-idle,
- documentacao confusa vira rewrite,
- risco escapado vira check,
- capacidade faltante vira capability pack,
- repeticao manual vira automacao.

Learnback nao deve ser anotacao bonita. Quando serio, vira teste, validador, skill, contrato, script, issue, pull request ou mudanca de fluxo.

## Entrega Ruim Versus Entrega Boa

Entrega ruim tem trabalho sem prova, card vago, worker sem limite, executor revisando a si mesmo, gate escondido, Product SOT raso, arquitetura decorativa, seguranca tardia, docs inuteis, release sem rollback, producao sem aprovacao, progresso so em texto, Kanban movimentado sem artefato e publico GitHub com sobras internas.

Entrega boa tem produto definido, escopo claro, risco explicito, work units pequenas, worker certo, autoridade limitada, execucao real, prova real, evidencia legivel, revisao independente, human gate so quando necessario, decisao humana clara, release com rollback quando preciso, documentacao util, recibo final, estado rastreavel e learnback incorporado.

## O Que O Operador Deve Cobrar

Voce nao precisa entender todos os schemas. Voce deve conseguir perguntar:

- o que a Factory sabe com certeza?
- o que ela esta assumindo?
- o que falta decidir?
- qual e o proximo passo seguro?
- o que esta bloqueado?
- isso precisa de mim ou e trabalho da Factory?
- onde esta a evidencia?
- quem revisou?
- isso autoriza producao ou e prova parcial?
- qual e o Receipt Five?
- qual risco restou?

Se as respostas sao claras, a Factory esta saudavel. Se sao vagas, provavelmente existe teatro.

## Limite Honesto

A Factory nao e magica. Ela nao elimina erro. Ela faz o erro aparecer mais cedo, com rastro, dono e proximo passo.

Repo passando check local nao prova entrega viva. Mapa visual nao prova runtime. Gateway conectado nao prova Factory Run especifica. Registry de worker nao prova que todo worker executou bem.

Prova real de produto exige estado Hermes vivo, card real, worker result, evidencia especifica, readback, revisao independente, Receipt Five e human gate quando necessario.

A regra de ouro permanece: nada esta pronto porque um agente disse que esta pronto. Esta pronto quando a Factory mostra pedido, trabalho produzido, prova, reviewer, risco restante e estado final autorizado.
