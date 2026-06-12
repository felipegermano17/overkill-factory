# Discord da Fabrica: Guia de Subida para Producao

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: Este guia configura cockpit; placeholders de setup nao sao prova de runtime nem aprovacao de release.

Este guia explica como transformar o Discord no painel de controle da Overkill
Factory sem deixar o Discord virar a fonte da verdade.

## Ideia simples

- Discord e a tela onde o dono acompanha, aprova e recebe alertas.
- Hermes continua sendo o lugar onde o estado real da execucao fica gravado.
- A fabrica continua decidindo gates, tarefas, evidencias e conclusao.
- O Concierge da Fabrica e a voz que fala com o dono no Discord.

## O que precisa existir antes do PASS

A Control Tower so pode virar `PASS` quando quatro coisas forem verdade:

1. O servidor Discord real existe.
2. O bot da fabrica esta dentro do servidor e consegue ler/escrever nos canais certos.
3. Uma aprovacao estruturada do dono sai do Discord e entra no Hermes como evento real.
4. O health da ponte prova que bot, ponte, leitura do runtime e registro de aprovacao estao funcionando.

Se qualquer item faltar, o recibo publico deve continuar `BLOCKED`.

## O que o dono precisa fazer

O dono so precisa criar ou conceder acesso ao servidor Discord e ao bot.

### 1. Criar o servidor

Nome sugerido:

```text
Overkill Factory Control Tower
```

Estrutura recomendada:

```text
01 COMECE AQUI
  #torre-de-controle
  #falar-com-gerente
  #saude-do-bot
  sala-de-voz-gerente

02 PROJETOS E KANBAN
  #projetos-recebidos
  kanban-da-fabrica

03 DECISOES E PENDENCIAS
  #aprovacoes-formais
  #acessos-pendentes
  #bloqueios-reais

04 PROVAS E PRODUCAO
  #provas-e-evidencias
  #producao-e-releases

99 ARQUIVO
  canais antigos ou migrados
```

`kanban-da-fabrica` deve ser um forum quando possivel. Isso permite um topico
por projeto, com tags de fase e bloqueio.

### 2. Criar o bot no Discord Developer Portal

No Discord Developer Portal:

1. Crie uma application.
2. Crie o bot.
3. Ative os intents:
   - Server Members Intent.
   - Message Content Intent.
4. Gere o token do bot.
5. Convide o bot para o servidor com permissoes para:
   - ver canais;
   - enviar mensagens;
   - ler historico;
   - anexar arquivos;
   - enviar embeds;
   - usar threads;
   - registrar comandos.

O token nunca entra no repo publico.

### 3. Coletar os identificadores privados

Com Developer Mode ligado no Discord, copie em local privado:

- ID do seu usuario Discord;
- ID do servidor;
- ID dos canais principais;
- ID da mensagem fixa do dashboard, depois que ela existir.

Esses IDs tambem nao entram no repo publico.

## O que a fabrica faz depois

Depois que o servidor e o token existem, a fabrica executa esta sequencia:

1. Configura o Hermes com:
   - `DISCORD_BOT_TOKEN`;
   - `DISCORD_ALLOWED_USERS`;
   - `DISCORD_HOME_CHANNEL`;
   - canais permitidos ou canais livres, se necessario.
2. Reinicia ou recarrega o gateway do Hermes.
3. Confirma que `hermes status` mostra Discord configurado.
4. Confirma que o bot aparece online no servidor.
5. Envia uma mensagem de health em `#saude-do-bot`.
6. Publica ou atualiza o dashboard em `#torre-de-controle`.
7. Registra uma aprovacao estruturada de teste em `#owner-approvals`.
8. Confirma que essa aprovacao foi registrada de volta no Hermes.
9. Preenche o kit privado de evidencia.
10. Roda o doctor privado.
11. Roda o proof publico-safe.

## Kit privado de evidencia

O kit privado fica fora do repo publico e contem:

```text
discord-control-tower-mapping.json
runtime-approval-event.json
bridge-health.json
```

O kit ja pode existir com placeholders, mas isso nao e prova de producao.
Ele so vira prova quando todos os campos vierem do Discord e do Hermes reais.

Comandos:

```bash
python scripts/operator_control_tower_private_evidence_doctor.py \
  --mapping /private/path/discord-control-tower-mapping.json \
  --runtime-registration-event /private/path/runtime-approval-event.json \
  --bridge-health /private/path/bridge-health.json
```

Depois do doctor passar:

```bash
python scripts/operator_control_tower_proof.py \
  --mapping /private/path/discord-control-tower-mapping.json \
  --runtime-registration-event /private/path/runtime-approval-event.json \
  --bridge-health /private/path/bridge-health.json
```

## O que deve aparecer no recibo publico

O repo publico pode dizer:

- se o mapping existe;
- se o evento do runtime existe;
- se o health passou;
- se o proof passou ou bloqueou;
- quais checks falharam.

O repo publico nao pode conter:

- token;
- webhook;
- IDs crus do Discord;
- URLs privadas;
- paths privados;
- logs crus;
- detalhes sensiveis do servidor.

## Canais e responsabilidade

| Canal | Para que serve | Quem fala ali |
| --- | --- | --- |
| `#torre-de-controle` | status resumido, fase atual, previsao e proximos passos | ponte |
| `#falar-com-gerente` | conversa direta com o GERENTE | dono e GERENTE |
| `#projetos-recebidos` | registro operacional de projetos recebidos | ponte |
| `#aprovacoes-formais` | aprovacoes estruturadas | dono por botao/fallback/evento e ponte |
| `#acessos-pendentes` | pedidos de acesso, contas, cloud, GitHub e chaves | ponte |
| `#bloqueios-reais` | bloqueios que impedem progresso | ponte |
| `#provas-e-evidencias` | links de evidencia e recibos | ponte |
| `#producao-e-releases` | decisao de release e producao | ponte |
| `#saude-do-bot` | health do bot, ponte e Hermes | ponte |
| `kanban-da-fabrica` | um topico por projeto | ponte |
| `#arquivo-projetos-antigo` | arquivo, nao uso diario | ponte |

O canal `#falar-com-gerente` e a portaria humana principal. O dono menciona o
GERENTE ali para abrir uma thread de atendimento. Depois disso, conversa,
perguntas, respostas, paper e decisoes daquele atendimento ficam dentro da
thread.

Essa decisao tem um detalhe importante: o canal principal nao e sala de projeto.
Ele so abre a porta. A experiencia certa e:

```text
mensagem no #falar-com-gerente com mencao ao GERENTE -> thread de atendimento
duvida curta -> resposta dentro da thread de atendimento
paper/projeto/piloto -> mesma thread vira intake + cartao no forum
```

`#projetos-recebidos` nao deve ser uma segunda porta humana para mandar paper.
Ele existe para registrar que um projeto entrou e apontar para o topico/card
correto. Se o dono estiver em duvida, deve falar com o GERENTE.

Pedido operacional sobre Discord, canal, thread, botao, mensagem, limpeza,
recriacao ou correcao visual nao e intake de projeto. Mesmo que a frase tenha
as palavras "projeto" ou "produto", ela deve ser tratada como manutencao da
torre de controle, nao como novo produto.

Importante: a thread do projeto nao e o lugar da aprovacao formal. A thread
pode explicar que existe uma decisao pendente e apontar para ela, mas o pedido
formal precisa aparecer em `#aprovacoes-formais`, criado pela bridge a partir
de um `approval-request` estruturado. Mensagem solta na thread, mesmo escrita
pelo GERENTE, nao aprova gate.

Mensagens ativas tambem precisam seguir uma regra simples:

```text
notificacao, health ou painel -> pode ficar sem thread
pergunta, decisao, acesso, bloqueio, evidencia discutivel ou projeto -> thread
```

Em outras palavras: toda mensagem do bot que convida conversa ou acao deve
nascer com thread, estar dentro de uma thread ou apontar claramente para a
thread certa. Apenas notificacoes puramente informativas devem ficar soltas.

O GERENTE deve usar `discord.require_mention=true`,
`discord.auto_thread=true` e `discord.thread_require_mention=false`: o dono
menciona uma vez na portaria, o Hermes abre a thread, e dentro dela o dono nao
precisa ficar mencionando o bot a cada resposta.

Os canais de cockpit precisam ser protegidos por politica de canal. O runtime
deve deixar `DISCORD_FREE_RESPONSE_CHANNELS` e `DISCORD_NO_THREAD_CHANNELS`
vazios, permitir conversa apenas na portaria e na lane de aprovacao formal, e
colocar as superficies de painel/registro em `DISCORD_IGNORED_CHANNELS`. Isso
impede que o GERENTE responda em `#torre-de-controle`,
`#projetos-recebidos`, `kanban-da-fabrica`, evidencias, bloqueios, acessos,
producao e health.

O perfil GERENTE tambem deve desligar progresso interno no Discord:
`display.platforms.discord.tool_progress=off`,
`interim_assistant_messages=false`, `long_running_notifications=false` e
`busy_ack_detail=false`. O dono precisa ver resposta final limpa; leitura de
arquivo, patch, terminal e rascunho do agente nao sao UI da fabrica.

Detalhe critico do runtime: no Hermes, variaveis do `.env` ganham do
`config.yaml`. Entao o perfil de producao do GERENTE nao pode deixar o canal do
GERENTE dentro de `DISCORD_NO_THREAD_CHANNELS` ou
`DISCORD_FREE_RESPONSE_CHANNELS`, e `DISCORD_THREAD_REQUIRE_MENTION` precisa
ser `false`. Se isso ficar errado, o bot responde por mencao, mas nao abre a
thread de atendimento.

Se alguem deixar um paper solto diretamente em `#falar-com-gerente`, a
automacao publica ignora esse texto ate existir uma thread de atendimento. Isso
evita criar um projeto novo para cada resposta do dono.

## Camada dinamica

O Discord nao deve ser apenas um chat. O modelo recomendado e:

- `#torre-de-controle` como portfolio global, com projetos ativos, etapa,
  percentual, alerta e proximo marco;
- mensagem fixada curta em cada canal operacional explicando quando usar;
- botoes de atalho para os canais principais;
- forum como indice limpo de projetos, com um topico por projeto;
- cockpit detalhado dentro de cada topico de projeto;
- intake thread-first: paper ou briefing nasce dentro da thread de atendimento;
- tags de fase no forum;
- `#aprovacoes-formais` para decisoes formais;
- `#acessos-pendentes` como checklist do que falta para autonomia;
- `#bloqueios-reais` para impedimentos reais;
- `#provas-e-evidencias` para provas e recibos;
- `#saude-do-bot` para health;
- voz apenas quando ajudar a conversa com o GERENTE.

O Kanban global nao deve carregar tudo. Se houver muitos projetos, ele continua
legivel porque mostra apenas o indice:

```text
Projeto | etapa | porcentagem | alerta | proxima acao
```

O detalhe mora dentro do topico de cada projeto.

## Cockpit por projeto

Cada topico de projeto precisa ter um painel de esteira.

Esse painel responde, de forma visual e direta:

- em que etapa estamos;
- qual porcentagem estimada da fabrica ja foi vencida;
- quais etapas faltam;
- o que falta para avancar;
- se existe bloqueio real;
- quais acessos faltam;
- quais aprovacoes faltam;
- qual e a proxima acao;
- qual foi a ultima prova;
- se o dado veio do Hermes ou e projecao manual/stale.

Modelo simples:

```text
Projeto: Nome
Etapa atual: Planejamento
Conclusao estimada: 22%
Proxima acao: fechar Product SOT
Bloqueado por: nenhum
Falta para avancar: acesso X + aprovacao Y

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

A porcentagem nao deve ser inventada como certeza. Ela e previsao operacional e
precisa ser recalculada pela bridge a partir do Hermes quando a automacao
existir. Enquanto for manual, deve ser marcada como estimativa visual.

Para o dono, a experiencia principal deve ser um unico chat:

```text
#falar-com-gerente
```

O dono nao deve precisar decorar comandos em ingles. Quando Hermes tiver comandos
nativos em ingles, eles ficam como camada tecnica por baixo. A interface humana
deve ser em portugues, conduzida pelo GERENTE e por botoes, menus ou formularios
em portugues.

Para atalhos operacionais e formularios, a fabrica precisa da
`Factory Concierge Discord Bridge`. O Hermes ja suporta perguntas com botoes via
`clarify`. Aprovacao formal no Discord usa botoes claros: `Aprovar`,
`Rejeitar` e `Pedir ajuste`. Se a interacao expirar, o fallback e responder
`aprovado`, `rejeitado` ou `pedir ajuste` na thread daquele pedido. A ponte
valida usuario, escopo, prazo e registra o evento no Hermes antes de valer.

Especialistas nao devem ficar interrompendo o dono diretamente. Eles falam com
o runtime; o Concierge consolida o que importa.

## Bridge de projecao do projeto

A ponte real para projetar um projeto no Discord e:

```bash
python scripts/factory_concierge_discord_bridge.py \
  --projection /private/path/project-projection.json \
  --state /private/path/discord-bridge-state.json \
  --env /private/path/hermes.env \
  --apply \
  --out /private/path/bridge-health.json
```

Antes de usar `--apply`, rode `--dry-run`. A bridge deve:

- achar o servidor e os canais pelo bot;
- atualizar o dashboard global em `#torre-de-controle`;
- atualizar o registro em `#projetos-recebidos`;
- criar ou reutilizar um topico no `kanban-da-fabrica`;
- atualizar o painel de esteira dentro do topico;
- salvar IDs reais apenas no estado privado;
- gerar recibo publico-safe sem IDs, tokens, paths privados ou logs crus.

O recibo live atual esta em:

```text
validation/control-tower/discord-bridge-projector-live-2026-06-11.json
```

## Automacao viva da Control Tower

A camada completa de automacao e:

```bash
python scripts/factory_concierge_discord_automation.py \
  --projection-dir /private/path/projections \
  --event-dir /private/path/events \
  --approval-dir /private/path/approvals \
  --scan-intake \
  --post-health \
  --state /private/path/discord-bridge-state.json \
  --env /private/path/hermes.env \
  --apply \
  --out /private/path/last-bridge-health.json
```

Ela cobre:

- thread de atendimento do GERENTE vira intake quando contem paper/projeto;
- mensagem solta no `#falar-com-gerente` nao vira projeto automaticamente;
- projeto vira topico/cockpit no `kanban-da-fabrica`;
- eventos de acesso, bloqueio, prova, release e health vao para os canais
  certos;
- mensagem ativa cria thread ou aponta para thread existente;
- aprovacao formal aparece com reacoes simples em portugues;
- aprovacao formal nasce em `#aprovacoes-formais`, nao como texto solto na
  thread do projeto;
- decisao de aprovacao so vira evento depois de validar id, papel, escopo e
  prazo;
- health da ponte e atualizado em `#saude-do-bot`;
- repeticao da automacao atualiza as mesmas mensagens, sem duplicar.

O recibo live da automacao completa esta em:

```text
validation/control-tower/discord-control-tower-automation-live-2026-06-11.json
```

Observacao importante: botao ou texto curto nao significa aprovacao magica. Em
producao, so vale depois que a ponte confirma dono autorizado, escopo, prazo e
evento duravel no Hermes. Smoke, teste ou silencio nunca aprovam execucao,
gasto, release ou producao.

## Rollback seguro

Se algo der errado:

1. Remova ou desative o token do Hermes.
2. Reinicie o gateway.
3. Revogue o token no Discord Developer Portal, se houver suspeita de vazamento.
4. Remova o bot do servidor se necessario.
5. Rode o proof novamente para garantir que o recibo voltou a `BLOCKED`.

Rollback correto nao apaga historico do Hermes. Ele so corta a ponte com o
Discord ate a configuracao estar saudavel de novo.

## Definicao de pronto

O Discord da fabrica esta pronto quando:

- o Hermes mostra Discord configurado;
- o bot esta online no servidor certo;
- o dashboard reflete o estado real do Hermes;
- o dono consegue aprovar uma solicitacao estruturada;
- a aprovacao aparece como evento real no Hermes;
- o health da ponte passa;
- o doctor privado passa;
- o proof publico-safe passa;
- o recibo final da atualizacao deixa de estar bloqueado.

Antes disso, a fabrica pode estar bem encaminhada, mas ainda nao deve ser
tratada como 100% pronta para producao com cockpit Discord.
