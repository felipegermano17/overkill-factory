# Linha de produção

## Pedido

Se o pedido chega no meio de um trabalho já existente, a fábrica não abre um ciclo paralelo sem ligação. Ela verifica se o pedido altera uma unidade em andamento, se cria nova unidade, se muda a verdade do produto ou se exige decisão. Essa leitura evita que uma mensagem nova sobrescreva silenciosamente o estado do Hermes. O pedido pode virar comentário, alteração de escopo, bloqueio, pacote de decisão ou nova entrada de fonte.

O pedido é a primeira entrada da fábrica. Ele pode chegar por mensagem, issue, call, documento, comentário, print, repositório ou card já existente. A fábrica registra o pedido como sinal inicial e mantém ligação com tudo que veio junto: anexos, links, prints, decisões anteriores, conversas ou arquivos.

Nesse estado, o pedido ainda não é plano. A frase “arrumar o onboarding” não vira automaticamente uma lista de tarefas. Primeiro ela fica registrada como entrada recebida e fonte a preservar. Se o pedido inclui um link de Figma, esse link segue junto como fonte visual. Se inclui um print de erro, o print segue como evidência de estado observado. Se inclui uma conversa antiga, a conversa entra como contexto, mas não como decisão nova sem leitura.

O pedido avança quando a fábrica consegue apontar de onde ele veio e que fonte precisa ser preservada. Se o pedido não tem fonte suficiente, ele não desaparece. Ele fica em estado de entrada incompleta, com a lacuna registrada. No Hermes, isso pode aparecer como card inicial, comentário ou bloqueio de intake. A retomada acontece quando a fonte faltante chega ou quando a fábrica registra que aquela lacuna não impede a próxima leitura.

A saída do pedido é a ligação com a fonte. Essa ligação alimenta a etapa seguinte.

## Fonte

A fonte continua consultável depois que o trabalho começa. Um reviewer pode voltar à fonte para verificar se o resultado respondeu ao pedido. Um humano decisor pode voltar à fonte para entender a consequência de aprovar. Um mantenedor pode voltar à fonte quando o recibo declara pendência. A ligação não serve como decoração; ela sustenta leitura, revisão e fechamento.

Fonte é o material preservado antes da interpretação. A fonte pode ser a mensagem original, documento, link, repositório, print, arquivo, conversa anterior, card anterior, decisão anterior ou anexo. A fábrica não começa reescrevendo a fonte como plano. Ela preserva o material, cria referência e deixa esse material consultável durante o ciclo.

Quando a fonte entra, cada item mantém seu papel. Uma mensagem guarda intenção. Um documento guarda especificação recebida. Um link de Figma guarda desenho. Um print guarda estado observado. Um repositório guarda implementação atual. Um card anterior guarda histórico de trabalho. Uma decisão anterior guarda autoridade já registrada. Esses itens ficam ligados ao pedido para que entendimento, rota, método, revisão e recibo possam voltar à base quando necessário.

A fonte muda estado quando deixa de ser apenas material solto e passa a ter referência dentro da fábrica. Essa referência pode aparecer em um registro de fonte, em comentário de card, em anexo, em link de artefato ou em campo de card Hermes. Se um item de fonte é privado, sensível ou transitório, o registro precisa indicar limite de uso em vez de publicar o conteúdo.

A etapa bloqueia quando a fonte necessária não existe, não pode ser acessada, conflita com outra fonte ou depende de autoridade. O bloqueio registra o item faltante, quem pode liberar, qual parte do fluxo está parada e qual próxima ação destrava. Quando o material chega, o bloqueio é retomado sem perder a ligação com o pedido original.

A saída da fonte é material preservado e referenciado. Esse material alimenta entendimento.

## Entendimento

Entendimento é a leitura estruturada da fonte. A fábrica lê o material preservado e separa fatos, afirmações do pedido, decisões já tomadas, restrições, dependências, dúvidas, lacunas, conflitos, inferências e itens fora de escopo.

Uma frase como “lançar amanhã” entra como restrição de prazo, não como prova de prontidão. Um print de erro entra como estado observado, não como causa confirmada. Um comentário “o cliente aprovou” entra como afirmação, mas pode precisar de decisão registrada. Um documento antigo entra como contexto, mas pode estar superado por decisão posterior. Uma inferência feita pela fábrica precisa ficar marcada como inferência, não como fato.

O resultado é um registro de entendimento. Esse registro mostra quais partes do pedido estão firmes, quais partes dependem de autoridade humana, quais partes dependem de acesso, quais conflitos precisam ser resolvidos e quais lacunas não podem alimentar trabalho executável. Ele também indica o que está fora de escopo para evitar que trabalho pequeno seja criado a partir de material solto.

No Hermes, o entendimento aparece como atualização do card, comentário estruturado, anexo de leitura ou campo ligado à unidade inicial. Quando a fábrica encontra conflito, o card pode ficar bloqueado. Quando falta decisão, a fábrica prepara um pacote de decisão. Quando a lacuna é interna e resolvível, a fábrica cria próxima ação sem jogar trabalho de reconciliação para o operador.

A etapa avança quando o registro de entendimento é suficiente para montar a verdade do produto. Ela bloqueia quando há conflito material, fonte ausente, acesso faltando ou autoridade necessária. A retomada acontece com nova fonte, decisão registrada, acesso concedido ou escopo reduzido de forma explícita.

A saída do entendimento é uma leitura que alimenta a verdade do produto.

## Verdade do produto

Quando a verdade do produto muda, a fábrica precisa tratar isso como mudança de estado. Uma alteração de escopo pode invalidar rota, método, unidades já criadas ou evidência já coletada. O Hermes precisa mostrar o que foi mantido, o que foi reaberto e o que ficou fora. A mudança não deve ficar apenas em uma frase solta de conversa.

A verdade do produto é a referência central do que será produzido. O nome interno pode ser `Product SOT`, mas o papel humano é simples: ela concentra o que a fábrica sabe sobre objetivo, destinatário, escopo, estado atual, estado desejado, restrições, riscos, dependências, prova e autoridade.

Ela nasce a partir da fonte lida e do entendimento registrado. A fábrica pega afirmações firmes, decisões já tomadas, lacunas conhecidas e restrições visíveis e transforma isso em um artefato que pode orientar rota, método e trabalho. A verdade do produto não é resumo bonito. Ela precisa dizer quem recebe o resultado, o que entra no escopo, o que fica fora, qual estado atual existe, qual estado desejado deve aparecer, quais critérios de aceitação contam, que prova será necessária e quais decisões ainda estão pendentes.

Se o pedido é “criar onboarding”, a verdade do produto precisa separar usuário, telas, estados, dados, convite, erro, loading, responsividade, prova de navegação e fronteiras como cobrança ou KYC fora do escopo. Se o pedido é “corrigir reset de senha”, ela precisa declarar comportamento atual, comportamento esperado, ambiente, usuário afetado, prova de reprodução, prova de correção e limite para não redesenhar autenticação inteira.

No Hermes, a verdade do produto fica ligada ao card principal ou ao conjunto de cards. Ela vira referência para workers e reviewers. Um worker não deve inventar escopo fora dela. Um reviewer usa a verdade do produto para comparar resultado e evidência. Uma decisão humana usa essa verdade para entender o que está sendo autorizado.

A etapa avança quando a verdade do produto tem escopo dentro, escopo fora, prova necessária e pendências visíveis. Ela bloqueia quando escopo é ambíguo, autoridade está faltando, riscos não têm dono ou critérios de aceitação não sustentam trabalho. A retomada acontece com ajuste de fonte, decisão humana, redução explícita de escopo ou complementação do registro.

A saída da verdade do produto alimenta rota, método e trabalho.

## Rota

Rota é a classificação do tipo de trabalho. A rota é escolhida a partir da verdade do produto, não a partir de uma palavra solta no pedido. Um pedido pode parecer documentação, mas envolver release. Pode parecer bug, mas exigir segurança. Pode parecer interface, mas depender de integração. A rota registra qual caminho de produção a fábrica vai usar.

rotas comuns incluem documentação, bug, feature, interface, CLI, integração, release, incidente, segurança, blockchain/Solana, dados, operação e manutenção. Cada rota muda o que precisa acontecer depois. Documentação exige leitura, navegação, clareza, primeiro sucesso do leitor e fronteira da claim. CLI exige instalação, comando, saída, erro e retorno. Interface exige telas, estados, interação, erro, loading e responsividade quando aplicável. Release exige readiness, rollback, dono, janela e decisão. Segurança exige escopo, risco, autoridade e cuidado com evidência sensível. Solana exige rede, carteira, assinatura, simulação, transação, fundos e autoridade humana quando aplicável.

A rota fica registrada como parte do contrato de produção. No Hermes, ela pode aparecer no card, no comentário de planejamento, no campo de roteamento ou no artefato usado para criar unidades. A rota define quais métodos, workers, gates e provas entram no ciclo.

A rota avança quando a classificação sustenta método e trabalho. Ela bloqueia quando a verdade do produto não permite distinguir tipo de trabalho, quando há risco sem classe, quando o trabalho mistura rotas incompatíveis ou quando uma autoridade humana precisa escolher entre caminhos com consequências diferentes. A retomada acontece quando a verdade do produto é refinada ou quando a decisão registra qual caminho será seguido.

A saída da rota alimenta método e capacidade.

## Método

Método é a régua de execução para uma rota. Ele define os passos mínimos, que tipo de evidência conta, que revisão precisa existir, que decisão humana pode ser necessária, que trabalho pode ser automatizado, que check precisa rodar e que estado precisa existir antes de avanço.

Para documentação, o método pode exigir navegação limpa, explicação humana, comando de validação, ausência de claim de runtime e revisão contra o briefing. Para CLI, pode exigir instalação, `doctor`, comando mínimo, saída observada, erro esperado e retorno. Para interface, pode exigir estados visuais, interação, console, screenshot e revisão de produto. Para release, pode exigir plano, rollback, janela, dono, health check, aprovação e monitoramento. Para segurança, pode exigir escopo sensível, tratamento de segredo, evidência privada ou pública e revisão especializada. Para Solana, pode exigir rede declarada, carteira, simulação, assinatura, transação, fundos, autoridade humana e recibo específico.

Para trabalho de segurança, a matriz pública de perfis usa estes domínios internos como referência de capacidade: networking, linux-systems, web-security, ethical-hacking, security-tools, cloud-security, detection-monitoring, cryptography, security-operations, future-security, supply-chain e onchain-solana-quasar. Esses nomes não viram títulos do caminho principal; eles ajudam mantenedores e validadores a ligar rota, worker e método.

O método transforma rota em regra prática. Ele não é só um rótulo. Se o método não muda evidência, revisão, gate ou estado, ele não está cumprindo seu papel. A fábrica usa o método para montar unidades pequenas, escolher workers, exigir proof e decidir quando um card pode avançar.

No Hermes, o método aparece na forma de campos de card, worker packets, checks esperados, bloqueios e revisão. Um card de CLI sem saída de comando fica bloqueado por evidência. Um card de release sem rollback fica bloqueado por readiness. Um card de segurança sem escopo sensível pode voltar para entendimento ou método.

A etapa avança quando a régua está clara para criar unidades executáveis. Ela bloqueia quando a rota não tem método aplicável, quando a prova exigida não existe, quando a decisão humana é necessária ou quando falta capacidade para executar o método. A retomada acontece com método ajustado, capacidade liberada, escopo reduzido ou decisão registrada.

A saída do método alimenta capacidade e trabalho.

## Capacidade

Capacidade é a checagem das condições para executar. A fábrica verifica worker disponível, permissão, acesso, segredo, ambiente, ferramenta, repositório, especialista, janela de execução, autoridade humana e risco residual.

Sem capacidade, a unidade não é executável. Se falta acesso ao repositório, o card fica bloqueado por acesso. Se falta segredo, a fábrica registra segredo necessário sem expor valor. Se falta ambiente, o bloqueio aponta ambiente e dono. Se falta especialista, o trabalho aguarda worker compatível. Se a ação envolve produção, fundos, mainnet, gasto ou risco residual, a capacidade inclui decisão humana.

A ausência de capacidade vira estado operacional. Ela pode gerar bloqueio, pendência ou pacote de decisão. O bloqueio precisa dizer o que falta, quem pode liberar, qual unidade está parada e qual próximo estado será aplicado quando a capacidade existir. A fábrica não transforma falta de acesso em trabalho concluído, nem pede ao operador para resolver uma pendência sem contexto.

No Hermes, capacidade aparece como bloqueio, dependência, comentário, anexo de decisão ou campo de card. Quando a capacidade é liberada, a unidade volta para a fila executável com a mesma ligação à fonte, à verdade do produto e ao método.

A saída de capacidade é autorização operacional suficiente para quebrar ou executar trabalho.

## Trabalho

Uma unidade boa permite revisão objetiva. Se a saída esperada é "documentação atualizada", a unidade precisa dizer quais arquivos, que leitura o documento deve permitir, que comando valida navegação e que fronteira de claim precisa aparecer. Se a saída esperada é "bug corrigido", a unidade precisa dizer qual reprodução falha antes, qual evidência passa depois e qual risco precisa ser revisado.

Trabalho é a quebra da verdade do produto em unidades pequenas. Uma unidade de trabalho não é “fazer a feature”. Ela é uma parte executável com entrada, saída esperada, dono, worker ou perfil de worker, dependência, evidência exigida, reviewer, regra de pronto, relação com card Hermes e estado de bloqueio ou avanço.

A fábrica lê a verdade do produto e o método e cria unidades que podem ser executadas sem inventar escopo. Uma unidade pode ser “validar instalação local e registrar saída de comando”, “revisar telas de onboarding contra estados exigidos”, “reproduzir bug de reset de senha”, “gerar pacote de decisão de release” ou “comparar documentação contra briefing”. Cada unidade tem material de entrada e saída esperada.

As dependências ficam explícitas. Uma revisão não começa antes de resultado e evidência. Um release não avança antes de readiness, rollback e decisão. Uma unidade bloqueada não some: ela fica no Hermes com motivo, dono e próxima ação.

O trabalho aparece no Hermes como card ou atualização de card. O card liga a unidade à fonte, à verdade do produto, ao método, ao worker, à evidência e à revisão. Quando a unidade termina, o resultado retorna para esse mesmo ponto. Quando há reparo, a fábrica cria continuação ligada à unidade original em vez de fechar o ciclo como se nada tivesse acontecido.

A saída do trabalho é uma fila executável, revisável e rastreável no Hermes.

## Hermes

Quando a fábrica retoma um fluxo, ela lê o Hermes antes de criar trabalho novo. O estado vivo mostra cards abertos, anexos existentes, workers que já responderam, revisões pendentes e bloqueios ainda válidos. Se essa leitura mostra evidência suficiente, a fábrica pode avançar. Se mostra lacuna, a próxima ação precisa apontar para a lacuna em vez de repetir trabalho às cegas.

Hermes é o lugar onde a execução fica visível. A fábrica usa Hermes para criar ou atualizar cards, ligar cards à fonte e à verdade do produto, registrar dependências, atribuir workers, receber comentários, guardar anexos, registrar bloqueios, registrar revisão, mudar status, preparar decisão, fechar ou reabrir ciclo.

Quando uma unidade é criada, ela pode virar card. O card carrega o estado da unidade. Se a unidade depende de outra, essa dependência fica registrada. Se um worker precisa agir, a atribuição aparece ali. Se falta acesso, o bloqueio aparece ali. Se o worker devolve resultado, o comentário, anexo ou campo de resultado aparece ali. Se a revisão consome evidência, a transição de estado aparece ali.

Hermes não é só um quadro de tarefas. Ele é o chão operacional onde o estado vivo aparece. A Factory não deve esconder a execução em arquivos locais quando o ciclo exige estado vivo. Arquivos locais podem ser prova de coerência, contratos, relatórios ou preparação. Execução viva exige o card, o worker, o resultado e a evidência no fluxo do Hermes.

A etapa Hermes bloqueia quando o card não existe, quando a dependência está aberta, quando o worker não recebeu pacote, quando o resultado não voltou ou quando a evidência não está ligada. A retomada acontece com criação de card, resolução de dependência, worker packet enviado, resultado retornado ou evidência anexada.

A saída de Hermes é estado vivo para execução, evidência, revisão e decisão.

## Execução

Execução é trabalho feito por workers dentro dos limites da unidade. O worker recebe um pacote com contexto necessário, entrada, saída esperada, limite de autoridade, evidência exigida e campo de retorno. O pacote de worker prepara execução; ele não é execução por si só.

Durante execução, o worker trabalha na unidade e não deve inventar escopo. Se a unidade pede reproduzir um bug, o worker reproduz e registra o resultado. Se a unidade pede alterar arquivo, o worker altera o arquivo e devolve diff ou referência. Se a unidade pede rodar comando, o worker devolve comando, saída e código de retorno. Se encontra bloqueio, devolve bloqueio com motivo e próxima ação em vez de declarar pronto.

O resultado volta para Hermes ligado à unidade. Ele precisa carregar evidência suficiente para revisão. Uma frase “feito” não basta. O resultado precisa mostrar o que foi executado, onde, com que saída, qual artefato mudou ou qual material sustenta avanço.

A execução avança quando resultado e evidência voltam ao ciclo. Ela bloqueia quando o worker não tem acesso, quando o pacote está amplo demais, quando a saída esperada é ambígua, quando a ferramenta falha ou quando a evidência exigida não pode ser produzida. A retomada acontece com pacote corrigido, acesso liberado, dependência resolvida ou nova unidade de reparo.

A saída da execução alimenta evidência e revisão.

## Evidência

A evidência também precisa ter classe. Uma saída de comando pode ser pública. Um log com segredo precisa ser privado ou sanitizado. Um print de tela pode conter dado sensível. Uma transação onchain pode exigir rede, assinatura, carteira e autoridade. A fábrica registra essa classe para que o material possa ser consumido sem vazar informação e sem fingir que prova privada virou documento público.

Evidência é material ligado à execução e à revisão. Ela pode ser saída de comando, log, screenshot, diff, arquivo alterado, teste rodado, relatório, comentário de revisão, decisão registrada, link para artefato, anexo, checklist consumido, prova de leitura, prova de rollback, prova de ambiente ou prova de transação quando aplicável.

A evidência fica ligada assim:

```text
unidade de trabalho -> card Hermes -> resultado do worker -> revisão -> decisão/fechamento
```

Depois que o worker executa a unidade, o resultado volta para o card com evidência anexada ou referenciada. A revisão lê essa evidência. Se a unidade pedia comprovar instalação e execução de comando, a revisão procura o comando, a saída, o código de retorno e a mensagem exibida. Se a unidade pedia tela, a revisão procura screenshot, estado, erro, loading, interação e console quando aplicável. Se a unidade pedia release, a revisão procura build, testes, rollback, dono, janela, health check e decisão.

Evidência solta não muda estado. Um arquivo existente não é evidência consumida. Um link sem leitura não fecha unidade. Um teste local mostra coerência local, não execução viva no Hermes. A evidência só altera a etapa quando fica ligada à unidade, é consumida por revisão e sustenta uma transição.

A etapa bloqueia quando a evidência está ausente, incompleta, privada sem referência segura, fora de escopo, contraditória, sem ligação com o card ou insuficiente para o método. A retomada acontece com nova execução, novo anexo, leitura explícita, revisão complementar ou decisão humana quando a evidência sustenta risco residual.

A saída da evidência alimenta revisão.

## Revisão

Revisão é leitura do resultado e da evidência. Ela não é opinião solta e não é carimbo automático. A revisão consome o que o worker devolveu, compara com a verdade do produto, com o método, com a regra de pronto e com a evidência ligada ao card.

Os estados possíveis incluem aprovado, precisa reparo, bloqueado, decisão humana necessária, evidência insuficiente, fora de escopo, risco aceito, risco não aceito e reaberto. Cada estado precisa mudar algo no Hermes. Aprovado pode mover a unidade para próxima etapa. Reparo cria continuação ligada à unidade original. Bloqueado registra motivo e dono. Decisão humana prepara pacote. Evidência insuficiente devolve a unidade para execução ou anexação. Fora de escopo ajusta verdade do produto ou encerra aquele desvio.

Se a unidade pedia comprovar instalação, a revisão procura saída do comando e código de retorno. Se falta saída, ela não fecha. Se a unidade pedia mudança de documentação, a revisão procura arquivo alterado, navegação atualizada, claim limitada e validação local. Se o texto virou copy de produto, a revisão devolve para reescrita. Se a unidade pedia release, a revisão procura readiness, rollback, decisão e monitoramento.

A revisão avança quando evidência e resultado sustentam a regra de pronto. Ela bloqueia quando há lacuna, contradição, risco sem dono, decisão pendente ou método descumprido. A retomada acontece com reparo, nova evidência, decisão registrada ou reabertura do entendimento.

A saída da revisão alimenta decisão, recibo ou nova execução.

## Decisão

Decisão é o ponto em que autoridade humana pode ser necessária. A fábrica não simula autoridade humana. Ela prepara o pacote de decisão e aguarda o registro da escolha.

Casos comuns incluem produção, release, mainnet, fundos, segredos, gasto, mudança irreversível, risco residual, waiver, exceção de método, escopo ambíguo e conflito de prioridade. A fábrica reúne pedido, contexto, evidência, opções, risco, consequência, recomendação quando houver, limite do que já foi verificado e próximo estado após cada escolha.

Um pacote de decisão não é uma pergunta solta. Ele mostra o que está sendo autorizado e o que não está. Se a decisão é release, o pacote mostra versão, ambiente, janela, rollback, health check, evidência, risco residual e consequência de aprovar ou rejeitar. Se a decisão envolve segredo, o pacote registra necessidade e limite sem expor o valor. Se envolve mainnet ou fundos, a decisão precisa declarar rede, carteira, assinatura, transação, valor, risco e autoridade.

No Hermes, a decisão aparece como bloqueio aguardando humano, comentário estruturado, anexo de pacote, registro de aprovação ou registro de rejeição. Depois da escolha, o card muda para próximo estado autorizado: executar, bloquear, reparar, reduzir escopo, liberar release, arquivar ou reabrir.

A saída da decisão alimenta execução, revisão, recibo ou bloqueio continuado.

Quando a decisão rejeita avanço, a fábrica não apaga o trabalho anterior. Ela mantém a evidência já consumida, registra a razão da rejeição e cria uma continuação compatível com a escolha. Se a decisão aprova com limite, o limite acompanha a próxima unidade. Se a decisão pede novo escopo, a verdade do produto pode ser reaberta antes de qualquer worker continuar. Assim a autoridade humana muda estado sem virar autorização genérica para todo o restante do projeto.

## Recibo

O recibo final é o fechamento legível do ciclo. O nome interno pode ser `Receipt Five`. Ele registra cinco partes: o que foi pedido, o que foi produzido, que evidência sustenta, quem revisou ou decidiu e o que ficou pendente, bloqueado, fora de escopo ou como risco.

O recibo liga pedido, verdade do produto, cards Hermes, evidência, revisão e decisão. Ele não deve esconder pendência em frase genérica. Se algo ficou fora de escopo, o recibo declara. Se algo está bloqueado, declara motivo e dono. Se há risco residual aceito, aponta a decisão. Se a evidência é local, declara limite local. Se houve execução viva no Hermes, aponta o estado e os registros correspondentes.

O recibo avança quando consegue reconstruir o ciclo de forma legível. Ele bloqueia quando falta evidência, revisão, decisão, card, vínculo com a verdade do produto ou explicação de pendência. A retomada acontece com leitura de evidência, revisão complementar, decisão humana ou reparo de unidade.

A saída do recibo alimenta fechamento.

## Fechamento

O fechamento também alimenta aprendizado. Se o ciclo bloqueou porque faltou acesso, a fábrica pode registrar que o próximo trabalho semelhante precisa checar acesso mais cedo. Se a revisão devolveu texto por falta de mecanismo, a regra de documentação pode ser reforçada. Esse aprendizado não ativa mudança crítica sozinho; ele vira proposta ou ajuste rastreável para mantenedores.

Fechamento é a relação final entre pedido, produção, evidência, revisão e pendências. Ele não é apenas “terminou”. Os estados finais possíveis incluem entregue, bloqueado, parcial, reaberto, aprendido, arquivado e aguardando decisão.

Entregue significa que o pedido foi produzido dentro da verdade do produto, com evidência consumida, revisão registrada e recibo final. Bloqueado significa que a fábrica sabe o que impede avanço e quem pode destravar. Parcial significa que uma parte foi produzida e outra ficou fora, pendente ou bloqueada. Reaberto significa que revisão, decisão ou nova fonte alterou o estado. Aprendido significa que a fábrica registrou melhoria de processo sem ativar mudança crítica sem aprovação. Arquivado significa que o ciclo foi encerrado com estado conhecido. Aguardando decisão significa que a próxima mudança depende de autoridade humana.

No Hermes, fechamento precisa aparecer no card ou no conjunto de cards. O estado final precisa apontar para recibo, evidência, revisão e pendências. Se uma etapa futura precisa retomar, a retomada deve saber de onde partir: fonte, verdade do produto, card, worker, evidência, decisão ou recibo.

A fábrica fecha um ciclo quando o estado final é claro, as ligações estão preservadas e a próxima pessoa consegue ler o caminho sem depender de memória de chat. Se a próxima ação existir, ela precisa estar ligada ao card ou ao recibo; se não existir, o arquivamento precisa dizer por que o ciclo não continua.
