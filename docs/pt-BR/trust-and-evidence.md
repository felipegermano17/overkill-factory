# Confiança e evidência

A Overkill Factory parte de uma verdade incômoda: processo parecendo vivo não é a mesma coisa que progresso.

Agentes podem escrever arquivos, mover cards, produzir resumos confiantes e ainda errar o produto. Um painel pode mostrar atividade enquanto o bloqueio real continua parado. Uma revisão pode dizer pass sem ler o artefato. Um humano pode ser chamado para aprovar algo sem receber o material que está aprovando.

A fábrica trata tudo isso como falha de produto.

## Evidência antes de confiança

A fábrica prefere evidência a tom de voz. Um worker dizendo "done" só ajuda se os artefatos existem, podem ser relidos e batem com o trabalho pedido. Um teste só ajuda se testa o comportamento certo. Uma revisão só ajuda se verifica o artefato certo e volta para a tarefa original.

É por isso que muitos registros da fábrica parecem rígidos. Eles não são rígidos porque o projeto gosta de papelada. Eles são rígidos porque evidência frouxa cria progresso falso.

## Receipt Five

Receipt Five é o recibo de conclusão. Ele precisa responder cinco tipos de pergunta:

1. O que foi pedido?
2. O que foi feito ou decidido?
3. Que evidência prova isso?
4. Quem revisou e o que a revisão disse?
5. O que continua bloqueado, arriscado ou pendente?

Se o Receipt Five não consegue responder isso, o estado honesto não é pronto. Pode ser pronto para revisão, bloqueado, parcialmente completo ou aguardando decisão humana. Mas não é pronto.

## Readback

Readback quer dizer que a fábrica confere o artefato que o worker disse ter produzido. Não basta o worker dizer "escrevi o SOT" ou "adicionei o teste". A fábrica precisa ler o arquivo, confirmar que ele existe e decidir se ele tem qualidade para alimentar a próxima fase.

Isso protege contra uma falha muito comum: processo correto com produto ruim. O worker pode ter seguido o card, mas a entrega pode estar rasa, errada ou ausente.

## Revisão independente

Trabalho material deve ser revisado por outra identidade quando o risco pede. O executor pode explicar o que fez. Ele não deveria ser o juiz final.

A revisão pode passar, falhar ou pedir reparo. Se passa, precisa destravar ou fechar a tarefa original. Se falha, precisa gerar trabalho de reparo. Revisão parada, sem ser consumida, também é progresso falso.

## No-idle e bloqueios

No-idle não é truque de produtividade. É um guard contra paradas silenciosas. Se o board tem trabalho que deveria andar, mas nada material muda, a fábrica deve reparar o estado, despachar o próximo worker seguro ou falhar de forma visível.

Bloqueio também precisa ser honesto. Alguns bloqueios são decisões humanas reais. Muitos não são. Se a fábrica precisa de revisão interna, readback, artefato faltando ou reparo, isso é trabalho da própria fábrica. Não deveria chegar ao operador como se o humano tivesse que resolver.

## Gates humanos

Gate humano é coisa séria. Ele pertence a decisões em que a autoridade é do operador: release em produção, mainnet, fundos, segredos, orçamento, risco relevante ou uma fronteira explícita de aprovação.

Um bom gate humano é legível. Ele diz qual decisão precisa ser tomada, que evidência existe, o que pode dar errado e o que cada opção significa. O operador não deveria ter que decifrar JSON cru ou reconstruir a história por comentários espalhados.

## Segurança e risco

Segurança não é checklist no fim. É rota e arquitetura. Risco material pode exigir threat modeling, fronteiras de confiança, identidade e autorização, supply chain, segredos, privacidade, incidente e dono explícito para risco residual.

A fábrica não deve prometer segurança perfeita. Ela deve prometer a melhor postura possível com evidência, gates e decisão explícita sobre risco residual.

A matriz pública de segurança agora faz parte deste modelo de confiança, em vez de ficar num arquivo operacional separado. Os domínios checáveis incluem `networking`, `linux-systems`, `web-security`, `application-security`, `ethical-hacking`, `security-tools`, `cloud-security`, `detection-monitoring`, `security-operations`, `cryptography`, `key-management`, `future-security`, `supply-chain` e `onchain-solana-quasar`.

## A fronteira honesta

Checks locais provam que o kernel público está coerente. Eles não provam que uma execução privada entregou um produto. Conclusão real de produto exige estado vivo no Hermes, evidência específica do produto, revisão e aprovação humana quando o risco pede.

Essa fronteira não é fraqueza. É o jeito da fábrica continuar honesta.

## Pacote de decisão antes da decisão

Um gate humano sem artefato é inválido. Se a fábrica pede aprovação para Product SOT, arquitetura, segurança, release ou Product Face, ela precisa entregar o material que está sendo aprovado ou uma projeção fiel com referência completa.

A primeira mensagem deve caber na cabeça do operador: decisão pedida, resumo em português claro, o que aprovar autoriza, o que não autoriza, opções de resposta, consequência e urgência. O anexo pode carregar o documento completo. O JSON é evidência interna, não experiência primária do operador.

## Blocos tipados e fronteira com o humano

Nem todo bloqueio é pergunta para o operador. `dependency_wait` é espera de dependência. `capability` é busca ou ativação de pack. `transient` é retry ou reparo. `needs_input` só chega ao operador quando existe pacote de decisão completo.

Essa separação evita um vício comum: transformar qualquer falha de processo em “preciso que o humano decida”. Muitas vezes a decisão correta é a fábrica reparar o próprio estado.

## Evidência local, evidência viva e evidência pública

Um comando local passando prova coerência do checkout. Um worker result prova que um worker rodou naquele escopo. Um Receipt Five prova fechamento quando consegue apontar para pedido, mudança, evidência, review e próximo estado. Uma publicação pública precisa ainda passar segurança de superfície e segredo.

Essas provas não são intercambiáveis. Não se deve usar smoke local para afirmar entrega de produto vivo, nem usar artifact existence como se fosse readback, nem usar uma aprovação humana genérica como waiver de release, segurança, fundos ou mainnet.

## Prontidão de implementação

Product Implementation Readiness é o ponto em que a fábrica pergunta: “já temos SOT, método, pesquisa, arquitetura, packs, acesso, workers, reviewers e prova suficiente para deixar a execução material começar?”.

Se essa resposta é fraca, a fábrica deve bloquear antes de gastar worker. Isso é mais barato do que descobrir no Receipt Five que o produto inteiro foi construído em cima de uma lacuna antiga.
