# O problema do produto

A Overkill Factory não existe porque agentes são inúteis. Existe porque agentes são úteis o bastante para serem perigosos quando trabalham sem contrato.

O risco não é só o agente falhar. Falha clara é fácil de ver: comando quebra, teste falha, arquivo não existe. O problema caro é o agente que erra com aparência de progresso.

## Progresso falso

Progresso falso é quando a operação produz movimento sem produzir confiança.

O card anda. O agente comenta. O arquivo aparece. O teste passa. A tela abre. A revisão recebe um “LGTM”. Mas ninguém provou que aquilo resolve o pedido certo.

Exemplos:

- bug “corrigido” sem teste que reproduziu o bug antes;
- release “pronto” sem rollback, dono, monitoramento ou decisão humana;
- tela “finalizada” sem erro, loading, vazio, mobile, permissão ou console limpo;
- documentação publicada sem mostrar que uma pessoa chega ao primeiro sucesso;
- worker dizendo “feito” sem readback do artefato.

## O operador vira a fábrica

Quando não há fábrica, o operador vira PM, QA, auditor, security reviewer, release manager e detetive.

Ele precisa lembrar o contexto, perguntar pela prova, conferir se a fonte foi preservada, descobrir se o bloqueio é dele, exigir revisão, comparar escopo, desconfiar de prints e interpretar logs. Isso não escala.

A Factory existe para tirar esse trabalho invisível das costas do operador.

## Kanban sem contrato não basta

Um quadro ajuda a ver movimento. Mas movimento não é entrega.

Um card em “done” só importa se existe regra de pronto, prova ligada ao pedido, revisão consumida e recibo. Sem isso, o quadro vira teatro organizado.

Hermes é necessário porque guarda o estado vivo. A Factory é necessária porque define o contrato que impede esse estado de virar bagunça.

## Teste verde também não basta

Teste verde pode ser excelente. Mas ele precisa provar o comportamento certo.

Um teste genérico não prova bug. Um build não prova produto. Um smoke local não prova Hermes vivo. Uma screenshot não prova jornada. Um JSON válido não prova aprovação humana.

A Factory força a pergunta certa: esta evidência prova qual pedido?

## Aprovação humana ruim é falsa segurança

“Posso seguir?” não é gate humano.

Gate humano de verdade mostra o que está sendo aprovado, o que não está, que prova existe, que risco sobra e o que acontece se a pessoa recusar. Sem isso, o humano apenas absorve responsabilidade sem receber contexto.

## Por que isso exige uma fábrica

Prompt melhor ajuda, mas não resolve sozinho. O problema é de produção: fonte, escopo, autoridade, método, worker, prova, revisão, bloqueio, decisão e aprendizado.

A Factory organiza esses elementos em uma linha de produção. Ela não promete perfeição. Promete que o sistema não pode se esconder atrás de frases confiantes.
