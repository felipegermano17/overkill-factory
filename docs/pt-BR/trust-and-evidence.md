# Confiança e prova

A pergunta certa é: "como eu sei que isso não é só um agente falando bonito?"

A resposta começa por uma verdade incômoda: processo parecendo vivo não é a mesma coisa que progresso.

Um sistema pode ter cards andando, comentários novos, arquivos criados e mensagens confiantes. Ainda assim, o produto pode estar errado.

## O que é teatro de progresso

Teatro de progresso é quando a aparência de trabalho substitui a entrega.

O worker diz "feito", mas não aponta evidência.

O teste passa, mas não testa o risco.

A tela existe, mas o fluxo quebra no segundo estado.

A revisão aprova, mas não leu o artefato.

O humano aprova, mas não recebeu o material.

O board se move, mas a dependência real ficou de fora.

A fábrica foi criada para tratar isso como falha central, não como detalhe.

## Prova precisa ter ligação com o pedido

Evidência solta não basta.

Um log, uma screenshot, um diff, um teste, um arquivo ou um link só vale se estiver ligado ao que foi pedido.

Se o pedido era provar onboarding, a evidência precisa mostrar a jornada.

Se era release, precisa mostrar prontidão, rollback e decisão.

Se era segurança, precisa mostrar risco, fronteira, revisão e o que ficou aceito.

Se era documentação, precisa mostrar que o leitor consegue entender e usar, não só que o Markdown compila.

## Readback: a fábrica lê de volta

Readback é simples: a fábrica confere o que foi entregue.

Se um worker disse que criou um documento, a fábrica lê o documento.

Se disse que anexou prova, a fábrica confere se a prova existe, abre, pode ser relida e não depende de um arquivo temporário.

Se disse que rodou teste, a fábrica olha o teste e o resultado.

Se disse que a interface está boa, a fábrica olha a superfície.

Sem readback, a fábrica fica confiando no próprio processo. E processo pode estar correto enquanto o produto está ruim.

## Receipt Five: o recibo do pronto

Receipt Five é o recibo de conclusão.

Ele responde cinco perguntas:

1. O que foi pedido?
2. O que foi feito ou decidido?
3. Que prova sustenta isso?
4. Quem revisou e o que a revisão disse?
5. O que ainda falta, bloqueia ou fica como risco?

Se uma resposta importante está vazia, o estado não é pronto.

Pode ser "pronto para revisão". Pode ser "bloqueado". Pode ser "parcial". Pode ser "aguardando humano".

Mas não é pronto.

## Revisão independente precisa ser consumida

A revisão não existe para enfeitar o processo.

Ela precisa mudar o estado do trabalho.

Se passou, destrava. Se falhou, cria reparo. Se encontrou risco, registra. Se pediu decisão, vira pacote humano. Se não foi consumida, não serviu.

E quando o risco é material, o executor não deveria ser o juiz final do próprio trabalho.

## Bloqueio precisa ser honesto

Bloqueio bom é específico.

Ele diz o que falta, por que falta, quem é dono e qual é o menor próximo passo seguro.

Também diz se precisa do humano ou não.

Muita coisa não precisa do humano. Falta de readback, falta de anexo, falta de revisão, worker raso, artefato quebrado, prova insuficiente. Isso é trabalho da fábrica.

O humano só deve ser chamado quando existe autoridade real a exercer.

## Gate humano sem material é inválido

Um gate humano não é "posso seguir?".

É uma decisão com artefato.

Se a fábrica pede aprovação de Product SOT, entrega o Product SOT. Se pede release, entrega o pacote de release. Se pede arquitetura, entrega a arquitetura. Se pede risco de segurança, entrega o risco, as opções e a consequência.

O operador precisa saber o que aprovar permite e o que aprovar não permite.

A pergunta pode ser curta. O material não pode ser ausente.

## Segurança entra cedo

Segurança não é maquiagem de fim de PR.

Se o trabalho toca segredo, permissão, produção, supply chain, privacidade, wallet, assinatura, Solana, fundos ou mainnet, segurança entra no caminho desde cedo.

Às vezes isso vira arquitetura. Às vezes vira scan. Às vezes vira revisão. Às vezes vira gate humano. Às vezes vira bloqueio.

A fábrica não promete risco zero. Ela promete não esconder risco atrás de um "pass" genérico.

## Prova local não é entrega viva

Um comando local passando prova que o checkout está coerente.

Um estado Hermes vivo prova que o trabalho existiu naquele runtime.

Um worker result prova que um worker devolveu algo naquele escopo.

Um Receipt Five bem formado prova que a conclusão foi reconciliada.

Essas coisas não são iguais.

Não dá para usar smoke local como prova de produto entregue. Não dá para usar arquivo existente como prova de readback. Não dá para usar aprovação genérica como autorização de mainnet.

A fábrica precisa manter essa fronteira visível, mesmo quando seria mais conveniente fingir que está tudo pronto.
