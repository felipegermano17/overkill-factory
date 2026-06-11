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

Mas esse canal nao pode virar um corredor infinito de mensagens. A regra de UX
da fabrica e:

```text
duvida curta -> o GERENTE responde no proprio chat
paper, briefing ou projeto novo -> abre topico do projeto e cartao no Kanban visual
```

Isso e importante porque o Hermes nativo trata `free_response_channels` como
chat leve: o usuario nao precisa mencionar o bot, mas a resposta tende a ficar
inline. A fabrica nao deve depender apenas desse comportamento nativo para
intake de projeto. O `Factory Concierge Discord Bridge` precisa reconhecer
pedido grande, criar o topico certo e apontar o dono para la.

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

O Kanban visual no Discord deve ser um espelho do Kanban real do Hermes.

Modelo:

```text
Forum: kanban-da-fabrica

Topico: Nome do projeto
Tags: Planejamento / Executando / Bloqueado / Revisao / Producao

Mensagem fixa do topico:
- fase atual
- dono da proxima acao
- bloqueios
- acessos faltantes
- aprovacoes pendentes
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

## Regra thread-first para projeto

Todo paper, briefing longo, novo produto ou pedido de piloto precisa gerar:

1. um topico de conversa ligado a mensagem original ou ao canal de intake;
2. um cartao no forum `kanban-da-fabrica`;
3. uma resposta curta no `#falar-com-gerente` dizendo onde o projeto passou a
   morar;
4. uma ligacao public-safe com o estado real no Hermes quando o runtime criar
   ou atualizar a card graph.

O nome do topico deve ser humano e curto, por exemplo:

```text
Piloto - Front jogo da fabrica
```

O topico nao substitui o Hermes. Ele e a sala visual do projeto para o dono.
O forum e o quadro visual. Hermes continua sendo a fonte de verdade.

## Modelo visual recomendado

### 01 PAINEL DA FABRICA

Lugar para ver e falar com a fabrica.

| Canal | Uso |
| --- | --- |
| `#torre-de-controle` | painel fixo com status, fase, pendencias e atalhos |
| `#falar-com-gerente` | conversa direta com o GERENTE, sem precisar mencionar |
| `#saude-do-bot` | health do bot, Hermes, gateway e ponte |
| `sala-de-voz-gerente` | conversa por voz quando fizer sentido |

### 02 OPERACAO

Lugar para entrada, decisao e desbloqueio.

| Canal | Uso |
| --- | --- |
| `#novos-projetos` | paper, ideia, pedido novo ou briefing inicial |
| `#aprovacoes-formais` | decisoes formais que precisam virar evento no Hermes |
| `#acessos-pendentes` | cloud, GitHub, contas, chaves e permissoes |
| `#bloqueios-reais` | o que impede a fabrica de avancar |

### 03 ENTREGA

Lugar para prova e promocao.

| Canal | Uso |
| --- | --- |
| `#provas-e-evidencias` | recibos, validacoes e provas public-safe |
| `#producao-e-releases` | release, rollback, producao e decisao final |

### 04 PROJETOS

Lugar para acompanhar cada projeto sem bagunca.

| Canal | Uso |
| --- | --- |
| `kanban-da-fabrica` | forum com um topico por projeto |
| `#arquivo-projetos-antigo` | legado ou material antigo |

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

## O que ja esta pronto no Discord real

A estrutura real foi ajustada para:

- categorias em portugues;
- canais com nomes em portugues;
- forum de projetos;
- canal direto `#falar-com-gerente`;
- sala de voz do GERENTE;
- dashboard fixado com atalhos;
- topicos explicativos nos canais;
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
de conversa perdido no chat. Se o dono mandar o paper em `#falar-com-gerente`,
a ponte deve criar o topico e o cartao automaticamente.

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
