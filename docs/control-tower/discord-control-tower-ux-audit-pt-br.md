# Auditoria UX da Torre de Controle Discord

Este documento registra a revisao de UX do Discord da Overkill Factory como
produto de uso real, nao como simples teste tecnico do bot.

## Veredito

O Discord real ficou muito melhor como cockpit inicial, mas ainda nao deve ser
tratado como Control Tower 100% dinamica.

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

O que ainda precisa virar produto:

- a ponte precisa criar topico e card automaticamente quando um paper/projeto
  chega pelo chat do GERENTE;
- o Kanban multi-projeto precisa de mapping idempotente para cada topico/card;
- a previsibilidade por projeto precisa ser automatizada pela bridge a partir
  do Hermes;
- aprovacoes precisam virar interacoes estruturadas, com registro real no
  Hermes;
- acessos, bloqueios, provas, releases e saude precisam ser projetados do
  Hermes para o Discord sem depender de postagem manual;
- retries precisam ser idempotentes, sem duplicar card, thread ou pedido de
  aprovacao.

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

### P1: intake de projeto ainda precisa de automacao real

O Discord real foi corrigido manualmente para o piloto, mas a ponte ainda
precisa provar que cria topico e card automaticamente quando o dono manda um
paper, briefing longo, novo produto ou piloto.

### P1: Kanban multi-projeto precisa de idempotencia provada

O forum do Discord suporta varios topicos, entao o desenho visual e adequado
para varios projetos se o forum for usado como indice. O detalhe precisa morar
dentro do topico/cockpit de cada projeto. Isso so fica pronto para producao
quando a ponte usa um mapping estavel por projeto e atualiza o card existente em
vez de duplicar topicos em retries.

### P1: previsibilidade precisa virar superficie de produto

A fabrica e previsivel por desenho, mas isso precisa aparecer visualmente. Cada
topico de projeto precisa ter um painel de esteira com etapa atual, percentual,
etapas restantes, bloqueios, acessos, aprovacoes, proxima acao e ultima prova.
Hoje o painel do piloto foi criado como correcao visual, mas ainda falta a
bridge projetar esse painel automaticamente a partir do Hermes.

### P1: aprovacoes ainda precisam de interacao estruturada

Canal e orientacao existem, mas a UX madura precisa de botoes, menus ou
formularios que gerem evento valido no Hermes. Texto livre nao deve aprovar
risco, release, custo ou producao.

### P2: canais vazios agora tem orientacao, mas precisam de projecao viva

Os canais deixaram de ser vazios e misteriosos, mas ainda devem receber estado
projetado pelo Hermes: acessos, bloqueios, provas, releases e saude.

### P2: o Kanban visual precisa ser espelho vivo

O forum esta certo como indice visual, mas a ponte precisa atualizar tags,
resumos e o painel de esteira do projeto conforme o Hermes muda.

### P2: regra de thread precisa ser aplicada pela ponte

O principio correto e: mensagem ativa precisa de thread. A excecao sao
notificacoes, health e painel. Pergunta, decisao, acesso, bloqueio, revisao,
evidencia discutivel e projeto precisam nascer em thread, continuar em thread
ou apontar para uma thread existente.

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

Enquanto isso nao estiver provado, o Discord e um cockpit inicial bom, mas nao
uma Control Tower completamente dinamica.
