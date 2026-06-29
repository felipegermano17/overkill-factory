# Como funciona

Esta página acompanha a experiência normal do operador: da primeira mensagem até o recibo final.

## 1. Você manda o sinal

A run começa quando o operador manda material para o gerente.

Pode ser uma ideia, bug, repo, documento, incidente, migração, pedido de release ou um conjunto de notas. O operador não precisa escrever no formato interno da fábrica.

## 2. O gerente cria o intake

O gerente identifica o tipo de trabalho, o material recebido, se é run nova ou continuação, o que é fato, o que é inferência, o que falta e o que exige decisão humana.

O gerente não deve prometer conclusão nessa hora. Ele deve transformar o pedido em estado inicial seguro.

## 3. A fábrica separa fonte de suposição

Uma mensagem pode misturar fato, opinião, exemplo, frustração, preferência e dúvida. A fábrica precisa separar isso.

Fonte é o que foi realmente fornecido. Suposição é o que o modelo inferiu. Decisão em aberto é o que ainda não pode ser tratado como verdade.

## 4. A definição de produto / PRD vira o alvo

Depois da fonte, a fábrica cria ou atualiza a definição de produto.

Essa é a camada de PRD em linguagem humana. Contratos internos antigos podem chamar isso de Product SOT, mas a ideia pública é simples: a run precisa de um alvo claro antes de decompor trabalho.

A definição registra escopo, fora de escopo, usuários, jornadas, aceite, riscos e evidência necessária.

## 5. O escopo é conferido

A fábrica verifica se todos os requisitos importantes estão contabilizados.

Cada item precisa estar planejado, feito com evidência, bloqueado, adiado, fora de escopo, sob decisão humana ou substituído por decisão aprovada.

Nada deve sumir silenciosamente.

## 6. O método é escolhido

O método depende do trabalho.

Documentação exige fonte, público, arquitetura de informação, escrita e build. Bug exige reprodução, correção e regressão. Produto exige PRD, arquitetura, experiência e prova. Release exige rollback, dono, monitoramento e gate.

## 7. Risco e capacidade são roteados

A fábrica identifica se o trabalho toca frontend, backend, dados, docs, IA, runtime de agentes, Solana/onchain, pagamentos, segredos, privacidade, produção ou segurança.

Se falta capacidade, ela deve procurar skills/providers/capability packs antes de pedir ajuda ao operador.

## 8. O plano vira Hermes

A fábrica transforma o produto em unidades de trabalho e materializa no Hermes.

Hermes guarda cards, dependências, status, bloqueios tipados, dispatch, runs, logs e comentários. Isso tira a próxima ação da memória do chat e coloca em estado durável.

## 9. Workers executam tarefas limitadas

Workers recebem packets, mas packet é só atribuição.

A fábrica espera resultado real do worker. Esse resultado precisa validar, ter evidência e poder ser consumido pelo trabalho pai.

## 10. O que é recuperável vai para reparo

Se falta artefato gerável, se uma leitura pode tentar de novo, se uma dependência do grafo está errada, se um resultado precisa de reconciliação, a fábrica deve reparar.

O operador não é fila de reparo.

## 11. O gerente chama o humano só quando precisa

O operador é chamado para aprovar/corrigir PRD, fornecer fonte privada, liberar acesso, aprovar custo, produção, risco, segredo, mainnet, fundos ou direção de produto.

Um bom gate humano vem com contexto, opções, consequência, recomendação e próximo passo.

## 12. Fecha com Receipt Five

Receipt Five responde:

1. o que mudou;
2. onde está;
3. como foi verificado;
4. quem ou o que revisou;
5. o que resta.

Sem isso, a run pode estar útil, mas não está fechada.
