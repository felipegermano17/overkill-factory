# Confiança e prova

A pergunta certa é: como eu sei que o agente não está só falando bonito?

A resposta começa por uma verdade incômoda: processo parecendo vivo não é a mesma coisa que progresso.

Card andando, arquivo criado, teste verde e mensagem confiante podem coexistir com produto errado.

## Teatro de progresso

Teatro de progresso é a aparência de trabalho substituindo a entrega.

O worker diz "feito", mas não aponta evidência.

O teste passa, mas testa o caminho fácil.

A tela existe, mas quebra no erro.

A revisão aprova, mas não leu o artefato.

O humano aprova, mas não recebeu o material.

O board anda, mas a dependência real ficou fora do grafo.

A fábrica trata isso como falha central.

## Prova solta não resolve

Prova solta não resolve. Ela precisa provar o pedido certo.

Se o pedido era onboarding, a prova precisa mostrar a jornada.

Se era release, precisa mostrar prontidão, rollback, dono e decisão.

Se era segurança, precisa mostrar risco, fronteira, revisão e o que ficou aceito.

Se era documentação, precisa mostrar que o texto guia uma pessoa de verdade, não só que o Markdown compila.

Exemplo fraco:

> Teste passou.

Exemplo bom:

> O teste de regressão `test_onboarding_email_error` falhou antes da correção, passou depois e cobre exatamente o erro descrito no pedido.

## Readback: reler antes de acreditar

Readback é a fábrica relendo o que o worker entregou.

Se ele disse que criou um documento, a fábrica lê o documento.

Se disse que anexou prova, a fábrica confere se a prova existe, abre, pode ser relida e não vaza segredo.

Se disse que rodou teste, a fábrica olha o comando e o resultado.

Se disse que a interface ficou boa, a fábrica olha a superfície.

Sem readback, o processo pode estar perfeito e a entrega pode estar ruim.

## Recibo de conclusão

No fim, você recebe um recibo de conclusão. Internamente ele pode aparecer como Receipt Five.

Ele responde cinco perguntas:

1. O que foi pedido?
2. O que foi feito ou decidido?
3. Que prova sustenta isso?
4. Quem revisou e o que a revisão disse?
5. O que ainda falta, bloqueia ou fica como risco?

Se uma dessas respostas importantes está vazia, não está pronto.

Pode estar pronto para revisão. Pode estar bloqueado. Pode estar parcial. Pode estar aguardando humano. Mas pronto, não.

## Review não é carimbo

Review precisa mudar o estado do trabalho.

Se passou, destrava ou fecha o item certo. Se falhou, cria reparo. Se apontou risco, registra dono e consequência. Se pediu decisão, vira pacote humano.

Reviewer e executor não deveriam ser a mesma identidade quando o risco é material.

## Bloqueio honesto

Bloqueio bom diz quatro coisas: o que falta, por que falta, quem é dono e qual é o menor próximo passo seguro.

Também diz se precisa do operador.

Muita coisa não precisa. Falta de anexo, falta de readback, worker raso, prova quebrada, revisão não consumida. Isso é trabalho da fábrica.

O operador entra quando há autoridade real: produção, mainnet, fundos, segredo, orçamento, release, waiver, risco residual.

## Gate humano tem que respeitar o humano

Um gate humano não é "aprova aí?".

É um pacote de decisão.

A pessoa precisa receber o artefato ou uma projeção fiel, entender o que está aprovando, quais opções existem, o que cada opção autoriza e qual risco fica.

JSON cru é evidência interna. Não é experiência de aprovação.

## Segurança não fica para o fim

Se o trabalho toca segredo, permissão, supply chain, produção, wallet, assinatura, Solana, fundos ou mainnet, segurança entra cedo.

Às vezes como arquitetura. Às vezes como scan. Às vezes como revisão. Às vezes como bloqueio. Às vezes como decisão humana.

A fábrica não promete risco zero. Promete não esconder risco atrás de um pass genérico.

## Prova local não é entrega viva

Um comando local passando prova que o checkout está coerente.

Um Hermes vivo prova que o trabalho existiu naquele runtime.

Um worker result prova que um worker devolveu algo naquele escopo.

Um Receipt Five bem formado prova que a conclusão foi reconciliada.

Essas coisas não são iguais. Smoke local não prova produto entregue. Arquivo existente não prova readback. Aprovação genérica não prova mainnet.

A confiança vem dessa disciplina.
