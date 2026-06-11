# Estudo: Discord Dinamico para Hermes

Este estudo responde a uma pergunta simples:

```text
Como transformar o Discord em uma central de controle viva, e nao em um chat
com um monte de mensagens soltas?
```

## Resposta curta

Faz sentido usar Discord como frente da fabrica, mas em tres camadas:

1. Discord nativo para estrutura visual, canais, forum, botoes de link, voz,
   topicos e comandos.
2. Hermes nativo para conversa com o GERENTE, comandos, anexos, threads,
   respostas em canal livre, voz e perguntas com botoes.
3. Ponte propria da fabrica para aprovacoes formais, painel editado em tempo
   real, previsao de proximos passos, status por projeto e registro de eventos
   no Hermes.

O erro seria usar Discord como historico solto. O acerto e usar Discord como
cockpit, mantendo Hermes como fonte da verdade.

## Criterio de excelencia

A torre de controle so esta boa quando o dono consegue operar sem aprender
comandos tecnicos e sem entender a estrutura interna do Hermes.

Regras:

- a interface humana deve ser em portugues;
- o canal principal deve ser `#falar-com-gerente`;
- comandos em ingles do Hermes podem existir por baixo, mas nao devem ser a
  experiencia principal do dono;
- decisoes importantes devem aparecer como botoes, menus ou formularios em
  portugues;
- o painel deve mostrar estado atual, nao historico baguncado;
- o Kanban real deve continuar no Hermes, mas o Discord deve ter um espelho
  visual facil de entender;
- cada projeto deve ter um lugar proprio, com fase, bloqueios, acessos,
  evidencias e proximo passo;
- o dono nao deve precisar descobrir se uma coisa esta em
  `#aprovacoes-formais`, `#acessos-pendentes` ou `#bloqueios-reais`; o GERENTE
  deve conduzir isso.

## O que o Discord permite

Discord nao e so chat. A documentacao oficial mostra recursos que servem bem
para uma fabrica agentica:

- comandos de aplicacao, incluindo slash commands;
- componentes de mensagem, como botoes, menus e campos de formulario;
- interacoes, onde um clique ou formulario vira um evento para o bot;
- canais, threads e forum channels;
- mensagens editaveis, fixadas, com embeds e anexos;
- canais de voz.

Isso permite uma interface mais parecida com um painel operacional:

- um painel fixo que muda de estado em vez de mandar spam;
- um topico por projeto no forum;
- botoes em portugues para navegar ou iniciar decisoes;
- formularios para coletar dados estruturados;
- tags visuais para fase, bloqueio, revisao e producao;
- mensagens fixadas curtas em cada canal operacional;
- sala de voz com o GERENTE quando fizer sentido.

## O que o Hermes ja permite

No runtime real estudado, Hermes ja tem suporte util para Discord:

- bot em DM ou canais de servidor;
- canais livres, onde o usuario fala sem mencionar o bot;
- allowlist de usuarios e canais;
- auto-thread para manter conversas isoladas;
- canais onde a resposta nao cria thread;
- anexos, imagens, documentos e audio;
- slash commands;
- comandos de skill expostos como slash commands;
- perguntas interativas via `clarify`, com botoes de escolha;
- voz, incluindo mensagens de voz e modo de voz;
- forum channels, onde Hermes cria topicos automaticamente quando precisa
  postar em um forum.

Isso ja e suficiente para um cockpit inicial bom. A parte que ainda precisa ser
da Overkill Factory e a camada operacional propria.

## Melhor uso do Discord para esta fabrica

| Recurso do Discord | Uso correto na fabrica | Observacao |
| --- | --- | --- |
| Forum | Espelho visual do Kanban por projeto | Um topico por projeto ou macro-entrega |
| Tags de forum | Fase e situacao | Planejamento, Executando, Bloqueado, Revisao, Producao |
| Mensagem fixada | Painel principal | Deve ser editada, nao duplicada |
| Botoes | Acoes curtas | Sempre em portugues |
| Menus | Escolha entre opcoes | Bom para fase, prioridade, tipo de aprovacao |
| Formularios | Entrada estruturada | Bom para novo projeto, acesso, aprovacao e release |
| Threads | Conversas isoladas | Bom para discussao de uma tarefa especifica |
| Reacoes | Sinal rapido de recebido/processando/concluido | Nao substitui evidencia |
| Voz | Conversa com o GERENTE | Opcional, quando for mais natural falar |
| Anexos | Papers, imagens, documentos e provas | Precisam ser registrados no Hermes quando virarem fonte |

O Discord nao tem um Kanban nativo completo com arrastar-e-soltar. O melhor
equivalente e usar forum + tags + mensagens editadas pela ponte. Isso cria um
Kanban visual sem transformar Discord na fonte da verdade.

## O que precisa ser da fabrica

Hermes generico nao sabe sozinho o que e uma aprovacao de release, um gate de
seguranca, uma pendencia de acesso, uma previsao de entrega ou um Receipt Five.

Por isso, a fabrica precisa de uma ponte propria:

```text
Evento do Hermes
-> projecao limpa para Discord
-> acao do dono no Discord
-> validacao da fabrica
-> evento estruturado de volta no Hermes
```

Essa ponte nao deve confiar em texto livre como aprovacao. Se a decisao e
importante, ela precisa virar evento estruturado.

## Experiencia ideal do dono

O dono usa principalmente um unico canal:

```text
#falar-com-gerente
```

Esse e o ponto principal: o dono nao deve ter duas portas para o mesmo ato.
Paper, piloto, pedido novo e duvida comecam pelo GERENTE. O canal
`#projetos-recebidos` existe como registro operacional, nao como segundo lugar
para o dono mandar o paper.

Mas o chat principal nao pode virar um corredor infinito de mensagens. Ele e
portaria, nao sala de projeto. A regra de UX da fabrica e:

```text
@GERENTE no #falar-com-gerente -> abre thread de atendimento
duvida curta -> o GERENTE responde dentro da thread
paper, briefing ou projeto novo -> a mesma thread vira intake + cartao no Kanban visual
```

Isso e importante porque o Hermes nativo trata `free_response_channels` como
chat leve. Para a fabrica, o melhor comportamento e o oposto: o dono menciona
o GERENTE uma vez no canal principal, o Hermes abre a thread, e a conversa
continua ali sem nova mencao a cada resposta. A bridge reconhece o pedido
grande dentro da thread, cria o topico certo e aponta o dono para la.

Exemplos de pedidos naturais:

```text
Como esta a fabrica?
O que falta para executar?
Mostre o Kanban visual.
O que esta bloqueado?
Quais acessos faltam?
O que eu preciso aprovar?
Explique o projeto X.
```

O GERENTE responde em portugues e aponta para o lugar certo quando houver algo
visual:

- painel geral;
- topico do projeto no forum;
- pedido de aprovacao;
- checklist de acessos;
- evidencia de validacao;
- sala de release.

Assim, os canais deixam de ser "coisas que o dono precisa entender" e viram
areas organizadas que o GERENTE usa para mostrar o trabalho.

## Kanban visual recomendado

O Kanban visual no Discord deve ser um indice visual limpo do Kanban real do
Hermes, nao um despejo de todas as tarefas.

Modelo:

```text
Forum: kanban-da-fabrica

Topico: Nome do projeto
Tags: Planejamento / Executando / Bloqueado / Revisao / Producao

Painel do topico:
- fase atual
- porcentagem estimada da esteira
- dono da proxima acao
- bloqueios
- acessos faltantes
- aprovacoes pendentes
- etapas restantes
- proximos passos
- ultima evidencia
```

O painel geral tambem pode mostrar uma visao resumida:

```text
Entrada      Planejamento      Executando      Bloqueado      Revisao      Producao
Projeto A    Projeto B         Projeto C       Projeto D      Projeto E    Projeto F
```

Essa mensagem deve ser atualizada pela ponte. Se o Hermes mudar, o Discord
muda. Se o Discord estiver desatualizado, o Hermes continua valendo.

Para varios projetos, o forum mostra apenas a lista limpa:

```text
Projeto A - Planejamento - 18% - sem bloqueio
Projeto B - Execucao - 47% - acesso pendente
Projeto C - Revisao - 76% - aprovacao pendente
```

O detalhe fica dentro de cada topico. Isso evita poluicao quando a fabrica
trabalha em mais de um produto ao mesmo tempo.

## Regra thread-first para projeto

Todo paper, briefing longo, novo produto ou pedido de piloto precisa gerar:

1. uma thread de atendimento ligada ao `#falar-com-gerente`;
2. um cartao no forum `kanban-da-fabrica`;
3. uma resposta curta dentro da thread dizendo onde o projeto passou a morar;
4. uma ligacao public-safe com o estado real no Hermes quando o runtime criar
   ou atualizar a card graph.

Regra para mensagens ativas do bot:

```text
notificacao / health / painel -> pode ficar sem thread
pergunta / decisao / acesso / bloqueio / revisao / projeto -> thread
```

Se a mensagem chama o dono para uma acao ou conversa, ela deve abrir thread,
estar dentro de uma thread ou apontar para a thread certa.

Mensagem de projeto deixada solta no `#falar-com-gerente` nao deve ser
processada como novo projeto. O dono precisa iniciar ou usar a thread de
atendimento; isso evita que uma resposta de pergunta vire um segundo projeto.

Pedido de manutencao da propria Control Tower nao e intake. Se o dono pedir
para recriar, corrigir, limpar ou mover mensagem, canal, thread, botao,
Kanban, aprovacao ou painel, a fabrica deve tratar isso como ajuste do
Discord/cockpit. A palavra "projeto" dentro dessa frase nao autoriza criar
produto novo.

O nome do topico deve ser humano e curto, por exemplo:

```text
Piloto - Front jogo da fabrica
```

O topico nao substitui o Hermes. Ele e a sala visual do projeto para o dono.
O forum e o quadro visual. Hermes continua sendo a fonte de verdade.

## Cockpit do projeto

O topico de projeto precisa ser mais do que conversa. Ele deve ser o cockpit
visual daquele projeto.

Toda fabrica e previsivel por definicao. Por isso, cada projeto precisa mostrar
uma esteira com:

- etapa atual;
- percentual estimado;
- etapas concluidas;
- etapas pendentes;
- bloqueios reais;
- acessos faltantes;
- aprovacoes pendentes;
- proxima acao;
- ultima prova;
- previsao/frescor do dado.

Modelo recomendado:

```text
Painel de Esteira do Projeto

Etapa atual: Fonte/SOT
Conclusao estimada: 12%
Proxima acao: consolidar Product SOT
Bloqueio: nenhum
Falta para avancar: confirmar escopo e acessos

Entrada: done
Fonte/SOT: current
Metodo/planejamento: pending
Arquitetura/UX/seguranca: pending
Acessos/gates: pending
Execucao: pending
Revisao/provas: pending
Producao: pending
Operacao/aprendizado: pending
```

Esse painel deve ser editado pela ponte, nao duplicado a cada evento.

## Hierarquia anti-poluicao

```text
#torre-de-controle
  portfolio global: poucos projetos, etapa, porcentagem, alerta

kanban-da-fabrica
  indice: um topico por projeto

topico do projeto
  cockpit: esteira, previsibilidade, bloqueios, acessos, provas, decisoes

canais de decisao/acesso/bloqueio/prova/release
  alertas e registros com link de volta para o topico do projeto
```

## Modelo visual recomendado

### 01 COMECE AQUI

Lugar para ver e falar com a fabrica.

| Canal | Uso |
| --- | --- |
| `#torre-de-controle` | painel fixo com status, fase, pendencias e atalhos |
| `#falar-com-gerente` | portaria: mencione o GERENTE para abrir atendimento |
| `#saude-do-bot` | health do bot, Hermes, gateway e ponte |
| `sala-de-voz-gerente` | conversa por voz quando fizer sentido |

### 02 PROJETOS E KANBAN

Lugar para entrada e acompanhamento visual.

| Canal | Uso |
| --- | --- |
| `#projetos-recebidos` | registro operacional do que entrou pela porta do GERENTE |
| `kanban-da-fabrica` | forum com um topico por projeto |

### 03 DECISOES E PENDENCIAS

Lugar para entrada, decisao e desbloqueio.

| Canal | Uso |
| --- | --- |
| `#aprovacoes-formais` | decisoes formais que precisam virar evento no Hermes |
| `#acessos-pendentes` | cloud, GitHub, contas, chaves e permissoes |
| `#bloqueios-reais` | o que impede a fabrica de avancar |

### 04 PROVAS E PRODUCAO

Lugar para prova e promocao.

| Canal | Uso |
| --- | --- |
| `#provas-e-evidencias` | recibos, validacoes e provas public-safe |
| `#producao-e-releases` | release, rollback, producao e decisao final |

### 99 ARQUIVO

Lugar para preservar canais antigos sem atrapalhar o uso diario.

## Como o painel deve se comportar

O painel nao deve ser um feed infinito.

O comportamento certo e:

1. Uma mensagem fixa mostra o estado principal.
2. A ponte edita essa mensagem quando o Hermes muda.
3. Alertas importantes vao para o canal certo.
4. Cada projeto tem um topico proprio no forum.
5. Decisoes formais aparecem em `#aprovacoes-formais`.
6. Evidencias aparecem em `#provas-e-evidencias`.
7. Bloqueios aparecem em `#bloqueios-reais`.

Assim o dono ve o estado atual sem procurar em dezenas de mensagens.

## Como deve funcionar uma aprovacao

Aprovacao nao deve ser:

```text
"ok pode fazer"
```

Aprovacao boa deve ser:

```text
Projeto: X
Pedido: aprovar plano / aprovar acesso / aprovar release
Escopo: exatamente o que esta sendo autorizado
Risco: o que esta sendo aceito
Expira em: data ou janela de tempo
Quem aprovou: dono autorizado
Registro: evento real no Hermes
```

No Discord isso pode aparecer como botao, menu ou formulario. Mas o clique so
vale depois que a ponte valida usuario, canal, prazo, escopo e registra o evento
no Hermes.

A thread do projeto pode avisar "ha uma aprovacao pendente" e apontar para o
canal certo. Ela nao deve conter o pedido formal como texto solto. Pedido
formal fica em `#aprovacoes-formais`, com escopo, risco, botoes e caminho de
registro no Hermes.

## O que ja esta pronto no Discord real

A estrutura real foi ajustada para:

- categorias em portugues;
- canais com nomes em portugues;
- categorias em ordem de uso: comecar, projetos, decisoes, entrega;
- forum de projetos;
- canal direto `#falar-com-gerente`;
- sala de voz do GERENTE;
- dashboard fixado com atalhos;
- mensagens fixadas explicativas em todos os canais operacionais;
- canal `#projetos-recebidos` como registro operacional, nao segunda porta de entrada;
- guia do Kanban separado por tag `Guia`, sem parecer projeto bloqueado;
- canais padrao antigos arquivados ou removidos quando vazios;
- health real enviado pelo bot.

Isso melhora a usabilidade imediatamente, mas ainda nao e a camada completa de
interacoes operacionais.

## O que ainda precisa virar produto da fabrica

### 1. Dashboard editado em tempo real

O `#torre-de-controle` deve ser atualizado em cima da mesma mensagem:

- estado geral;
- projeto ativo;
- fase atual;
- proximo passo;
- bloqueio real;
- confianca da previsao;
- ultima evidencia;
- alerta de risco.

### 2. Topico vivo por projeto

Cada projeto no forum deve ter:

- resumo curto;
- fase atual;
- responsavel atual;
- pendencias de acesso;
- pendencias de aprovacao;
- proximas etapas previstas;
- evidencias principais;
- historico resumido.

Esse topico deve nascer no intake, nao depois que o projeto ja virou um bloco
de conversa perdido no chat. O dono menciona o GERENTE no `#falar-com-gerente`,
o Hermes abre a thread de atendimento, e a ponte cria o topico e o cartao a
partir do conteudo dessa thread.

### 3. Aprovacao com botao e formulario

O dono deve conseguir aprovar pelo Discord, mas a ponte precisa registrar isso
no Hermes como evento estruturado.

O Discord pode coletar a decisao. Hermes decide se a decisao e valida.

### 4. Pedidos de acesso como checklist

`#acessos-pendentes` deve mostrar:

- o que falta;
- por que e necessario;
- qual risco se faltar;
- se bloqueia execucao ou apenas limita qualidade;
- quando foi resolvido.

### 5. Previsibilidade visivel

Como a fabrica so executa depois do plano estar pronto, o Discord deve mostrar:

- etapa atual;
- etapas restantes;
- dependencia que falta;
- decisao humana pendente;
- risco de atraso;
- proximo marco.

### 6. Antisspam e autoridade

Especialistas nao devem falar todos com o dono.

Fluxo certo:

```text
workers -> Hermes -> Concierge -> Discord
```

O GERENTE consolida, traduz e pergunta. O Discord nao vira um grupo caotico de
agentes.

## Decisao tecnica simples

Para producao, a fabrica deve ter um componente chamado:

```text
Factory Concierge Discord Bridge
```

Ele deve:

- ler eventos do Hermes;
- atualizar dashboard e topicos;
- criar pedidos de aprovacao;
- receber clique, menu ou formulario do Discord;
- validar permissao, escopo e prazo;
- registrar evento no Hermes;
- impedir duplicidade;
- gerar evidencia public-safe;
- bloquear quando algo estiver estranho.

## Limites importantes

- Discord nao armazena segredo.
- Discord nao e fonte da verdade.
- Chat livre nao aprova risco.
- Botao clicado nao significa aprovacao valida sem registro no Hermes.
- Canais livres devem ser poucos; hoje o canal livre certo e
  `#falar-com-gerente`.
- IDs, tokens, URLs privadas e logs crus ficam fora do repo publico.
- O painel deve ser editado em vez de gerar spam.

## Conclusao

Vale a pena usar Discord como frente da Overkill Factory, mas nao como "chat da
fabrica".

O modelo maduro e:

```text
Discord = cockpit vivo
GERENTE = voz oficial com o dono
Hermes = fonte da verdade
Overkill Factory = metodo, gates, workers e evidencias
Bridge = tradutor seguro entre Discord e Hermes
```

Com a estrutura atual, ja temos um cockpit inicial em portugues. A proxima
evolucao real e implementar a ponte dinamica da fabrica para dashboard vivo,
topicos por projeto e aprovacoes formais por interacao.

## Fontes estudadas

- Discord Developers: Message Components.
  `https://discord.com/developers/docs/interactions/message-components`
- Discord Developers: Application Commands.
  `https://discord.com/developers/docs/interactions/application-commands`
- Discord Developers: Channel Resource.
  `https://discord.com/developers/docs/resources/channel`
- Hermes Agent: Discord messaging.
  `https://hermes-agent.nousresearch.com/docs/user-guide/messaging/discord`
- Hermes Agent: Slash commands.
  `https://hermes-agent.nousresearch.com/docs/reference/slash-commands`
- Runtime Hermes real usado pela fabrica: docs e adapter Discord instalados no
  ambiente operacional.
