# Discord da Fabrica: Guia de Subida para Producao

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
| `#torre-de-controle` | status resumido, fase atual, previsao e proximos passos | Concierge |
| `#falar-com-gerente` | conversa direta com o GERENTE | dono e Concierge |
| `#projetos-recebidos` | registro operacional de projetos recebidos | Concierge |
| `#aprovacoes-formais` | aprovacoes estruturadas | dono e ponte |
| `#acessos-pendentes` | pedidos de acesso, contas, cloud, GitHub e chaves | Concierge |
| `#bloqueios-reais` | bloqueios que impedem progresso | Concierge |
| `#provas-e-evidencias` | links de evidencia e recibos | ponte |
| `#producao-e-releases` | decisao de release e producao | dono e Concierge |
| `#saude-do-bot` | health do bot, ponte e Hermes | ponte |
| `kanban-da-fabrica` | um topico por projeto | Concierge e dono |
| `#arquivo-projetos-antigo` | arquivo, nao uso diario | ponte |

O canal `#falar-com-gerente` e a porta humana principal: o dono fala
com o GERENTE sem precisar mencionar o bot. Os outros canais devem ser mais
controlados para evitar barulho e aprovacao acidental.

Essa decisao tem um detalhe importante: no Hermes nativo, canal livre responde
inline e pode pular auto-thread. Por isso, `#falar-com-gerente` nao pode ser o
unico mecanismo de organizacao de projetos. A experiencia certa e:

```text
mensagem curta -> resposta curta no chat
paper/projeto/piloto -> topico do projeto + cartao no forum
```

`#projetos-recebidos` nao deve ser uma segunda porta humana para mandar paper.
Ele existe para registrar que um projeto entrou e apontar para o topico/card
correto. Se o dono estiver em duvida, deve falar com o GERENTE.

Mensagens ativas tambem precisam seguir uma regra simples:

```text
notificacao, health ou painel -> pode ficar sem thread
pergunta, decisao, acesso, bloqueio, evidencia discutivel ou projeto -> thread
```

Em outras palavras: toda mensagem do bot que convida conversa ou acao deve
nascer com thread, estar dentro de uma thread ou apontar claramente para a
thread certa. Apenas notificacoes puramente informativas devem ficar soltas.

Se `DISCORD_NO_THREAD_CHANNELS` incluir `#falar-com-gerente`, isso deve ser
tratado como configuracao apenas para conversa curta. A fabrica ainda precisa
do `Factory Concierge Discord Bridge` para criar topicos de projeto e cartoes
no `kanban-da-fabrica`.

## Camada dinamica

O Discord nao deve ser apenas um chat. O modelo recomendado e:

- `#torre-de-controle` como portfolio global, com projetos ativos, etapa,
  percentual, alerta e proximo marco;
- mensagem fixada curta em cada canal operacional explicando quando usar;
- botoes de atalho para os canais principais;
- forum como indice limpo de projetos, com um topico por projeto;
- cockpit detalhado dentro de cada topico de projeto;
- intake thread-first: paper ou briefing nunca fica apenas como mensagem solta;
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

Para botoes operacionais, formularios e aprovacoes clicaveis, a fabrica precisa
da `Factory Concierge Discord Bridge`. O Hermes ja suporta perguntas com botoes
via `clarify`, mas aprovacoes de fabrica precisam ser validadas e registradas no
Hermes antes de valerem.

Especialistas nao devem ficar interrompendo o dono diretamente. Eles falam com
o runtime; o Concierge consolida o que importa.

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
