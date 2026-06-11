# Auditoria UX da Torre de Controle Discord

Este documento registra a revisao de UX do Discord da Overkill Factory como
produto de uso real, nao como simples teste tecnico do bot.

## Veredito

O Discord real agora tem uma Control Tower dinamica inicial, com intake,
projecao, threads, aprovacoes estruturadas, canais operacionais e health
provados no servidor real.

O que esta corrigido:

- estrutura em portugues e em ordem de uso;
- dashboard principal com orientacao e atalhos;
- cada canal operacional com mensagem fixada explicando como usar;
- canal de projeto refinado para `#projetos-recebidos`;
- Kanban visual com topico de guia separado de projeto real;
- tags adicionais no Kanban para guia, acao do dono e fabrica trabalhando;
- piloto ativo com topico de conversa e card visual no forum.
- painel global ajustado para portfolio, sem despejar detalhe de cada projeto;
- piloto ativo com painel de esteira dentro do topico do projeto.
- bridge de projecao criada como ferramenta real da fabrica;
- mapping idempotente provado no Discord real: repetir a projecao atualiza as
  mesmas superficies, sem criar duplicata;
- dashboard, registro de projeto, topico do Kanban e cockpit do piloto agora
  sao atualizados por `project-projection.json`.
- intake do GERENTE cria ou reutiliza thread;
- eventos ativos caem na lane correta e abrem thread;
- aprovacao formal tem reacoes simples em portugues e validacao de decisao;
- health da ponte e atualizado em `#saude-do-bot`;
- a automacao completa foi aplicada duas vezes e o read-back confirmou que nao
  houve duplicata.

O que ainda precisa virar produto:

- manter runner privado vivo, monitorado e sem rate-limit excessivo;
- usar somente interacao real do dono ou evento duravel do Hermes para
  aprovacoes que liberem execucao, gasto, release ou producao.

## Jornada revisada

O dono nao deve precisar escolher o canal perfeito.

Fluxo correto:

```text
dono fala com o GERENTE
-> GERENTE entende se e duvida curta ou projeto
-> duvida curta fica no chat
-> projeto cria topico + card no Kanban
-> topico vira cockpit do projeto
-> cockpit mostra etapa, porcentagem, bloqueio, falta e proxima acao
-> registro aparece em #projetos-recebidos
-> pendencias aparecem nas lanes certas
-> decisoes formais sao registradas no Hermes
-> provas e releases aparecem como espelho visual
```

## Estrutura atual esperada

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
```

## O que cada area resolve

| Area | Funcao real |
| --- | --- |
| `#torre-de-controle` | Mostrar estado atual, atalhos e como usar o cockpit. |
| `#falar-com-gerente` | Porta principal de conversa com o dono. |
| `#projetos-recebidos` | Registro operacional do que entrou pela porta do GERENTE. |
| `kanban-da-fabrica` | Indice visual de projetos, com um topico por projeto. |
| topico do projeto | Cockpit do projeto, com esteira, percentual, faltas e bloqueios. |
| `#aprovacoes-formais` | Decisoes com escopo, risco e validade. |
| `#acessos-pendentes` | O que falta conceder antes de executar com autonomia. |
| `#bloqueios-reais` | O que esta impedindo progresso de verdade. |
| `#provas-e-evidencias` | Recibos, validacoes e evidencias public-safe. |
| `#producao-e-releases` | Release, rollback, monitoramento e producao. |
| `#saude-do-bot` | Saude do GERENTE, Hermes, gateway e ponte. |

## Achados principais

### Resolvido: superficies bridge-owned nao sao conversa

`#torre-de-controle`, `#projetos-recebidos`, `kanban-da-fabrica`,
`#acessos-pendentes`, `#bloqueios-reais`, `#provas-e-evidencias`,
`#producao-e-releases` e `#saude-do-bot` sao superficies de exibicao,
registro ou health. O GERENTE nao deve conversar ali.

A conversa humana fica em `#falar-com-gerente` e nas threads abertas a partir
dele. A excecao operacional e `#aprovacoes-formais`, que pode receber clique
ou evento de decisao, mas ainda nao deve virar sala de conversa.

### Resolvido: pedido operacional nao vira projeto

A automacao de intake agora rejeita pedidos sobre Discord, canal, thread,
botao, mensagem, limpeza, recriacao ou correcao visual. Uma frase como
"recrie o projeto/produto nesses dois canais" e manutencao do cockpit, nao
briefing de produto.

Um projeto novo precisa ter intencao clara: paper, briefing, novo produto,
pedido explicito de criar/construir produto, texto longo de demanda ou anexo
de entrada. Palavras soltas como "projeto" e "produto" nao bastam.

### Resolvido: GERENTE sem bastidor tecnico no Discord

O GERENTE nao deve exibir progresso interno de ferramenta no Discord. Mensagens
como leitura de arquivo, patch, terminal, busca ou rascunho intermediario
poluem a experiencia e confundem o dono. O perfil de producao deve manter o
progresso de ferramentas e mensagens intermediarias desligados no Discord,
entregando resposta final limpa ou evento estruturado da ponte.

### Resolvido: intake thread-first pelo GERENTE

A automacao `factory_concierge_discord_automation.py` escaneia
threads de atendimento abaixo de `#falar-com-gerente`, detecta mensagens com
cara de projeto/paper dentro dessas threads e cria ou reutiliza:

- a propria thread de atendimento como thread de intake;
- registro em `#projetos-recebidos`;
- topico/cockpit no `kanban-da-fabrica`;
- dashboard global atualizado.

Mensagem de projeto solta diretamente em `#falar-com-gerente` e ignorada pela
automacao. O canal principal fica como portaria: o dono menciona o GERENTE,
entra na thread, e a conversa do projeto continua ali.

### Resolvido: mapping e cockpit projetado sem duplicar

A bridge `factory_concierge_discord_bridge.py` recebe um
`project-projection.json` e atualiza quatro superficies:

- dashboard global em `#torre-de-controle`;
- registro em `#projetos-recebidos`;
- topico do projeto no `kanban-da-fabrica`;
- painel de esteira dentro do topico do projeto.

Ela grava o mapping em estado privado e tambem procura mensagens/topicos
existentes por marcador ou titulo. Isso permite repetir a execucao sem criar
duplicata. A prova live foi feita duas vezes no Discord real e confirmou:

```text
1 topico do piloto
1 dashboard marcado
1 registro marcado
1 cockpit marcado
```

O recibo publico-safe esta em:

```text
validation/control-tower/discord-bridge-projector-live-2026-06-11.json
```

### Resolvido: aprovacao simples por botao com fallback

Quando o botao expira, o Discord responde "Esta interacao falhou". Isso nao
pode virar uma explicacao burocratica. A camada de ponte deve manter botoes
claros e aceitar um fallback curto na thread do pedido:

```text
Aprovar
Rejeitar
Pedir ajuste
fallback: aprovado / rejeitado / pedir ajuste
```

A decisao so vale quando a ponte valida dono autorizado, `approval_id`, papel,
escopo e prazo antes de gerar um evento
`approval_recorded`.

Limite importante: em producao, isso so pode liberar algo quando vier de clique
real, fallback textual claro do dono na thread correta ou evento duravel do
Hermes. Smoke ou teste nao e aprovacao.

### Resolvido: canais operacionais vivos

Eventos da bridge agora caem nas lanes certas. O smoke live provou evento em
`#acessos-pendentes`, aprovacao em `#aprovacoes-formais`, health em
`#saude-do-bot` e cockpit no topico do projeto.

### Resolvido: Kanban visual como espelho vivo

O forum atualiza tags, resumo e cockpit por `project-projection.json`. A camada
de automacao tambem aceita diretorios privados de projeções/eventos/aprovacoes,
o que permite runner recorrente sem mudar o contrato publico.

### Resolvido: regra de thread aplicada pela ponte

O principio correto e: mensagem ativa precisa de thread. A excecao sao
notificacoes, health e painel. Pergunta, decisao, acesso, bloqueio, revisao,
evidencia discutivel e projeto precisam nascer em thread, continuar em thread
ou apontar para uma thread existente.

O read-back live confirmou:

```text
1 topico do piloto no Kanban
1 thread do piloto no GERENTE
1 dashboard marcado
1 registro marcado
1 evento operacional marcado
1 aprovacao marcada
1 health marcado
```

## Definicao de pronto UX

A Control Tower Discord fica pronta quando:

- o dono consegue iniciar um projeto pelo GERENTE sem escolher canal;
- cada projeto cria automaticamente topico e card visual;
- o canal `#projetos-recebidos` funciona como registro, nao como segunda porta;
- o Kanban visual reflete fase, bloqueio, acesso, aprovacao e evidencia;
- o Kanban atualiza varios projetos sem duplicar topicos;
- cada projeto tem cockpit proprio com esteira e percentual;
- o portfolio global mostra poucos dados por projeto e nao fica poluido;
- aprovacoes passam por interacao estruturada e registro real no Hermes;
- mensagens ativas do bot usam thread ou link claro para thread;
- o dashboard principal e editado em vez de gerar spam;
- mensagens repetidas nao criam duplicatas;
- health da ponte prova Discord, Hermes, mapping e registro de evento.

O recibo live da automacao completa esta em:

```text
validation/control-tower/discord-control-tower-automation-live-2026-06-11.json
```
