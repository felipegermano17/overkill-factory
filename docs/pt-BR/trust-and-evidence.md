# Confiança e Evidência

A fábrica parte de uma regra direta: processo parecendo vivo não é a mesma coisa que progresso.

Isso importa porque sistemas com agentes podem produzir status convincente enquanto fazem o trabalho errado, pulam verdade de fonte, escondem bloqueios ou declaram conclusão sem evidência. A Overkill Factory trata isso como falha de produto, não como problema de estilo de comunicação.

## Evidência antes de confiança

Declaração de worker não basta. A fábrica espera evidência que possa ser inspecionada depois: arquivos, comandos, saída de testes, registros de readback, screenshots, receipts, registros de revisão ou artefatos estruturados.

A evidência mais forte tem três propriedades:

1. aponta para um artefato real;
2. pode ser lida de volta depois que o worker termina;
3. se conecta à verdade de produto ou ao método que diz satisfazer.

## Readback

Readback significa que a fábrica verifica se os artefatos declarados ainda existem e contêm o conteúdo esperado. Isso impede que um worker cite arquivos que nunca foram criados, foram criados no workspace errado ou sumiram depois da execução.

Para artefatos críticos, readback não é burocracia. É a diferença entre "o agente disse" e "o sistema consegue provar".

## Revisão independente

Execução e revisão são trabalhos diferentes. Um builder pode terminar uma tarefa, mas um reviewer precisa inspecionar se o resultado satisfaz o contrato. Em trabalho material, a mesma identidade não deve ser executor e reviewer.

Um resultado de revisão precisa ser reduzido de volta no estado original do runtime. Se a revisão passa mas o card original fica bloqueado para sempre, a fábrica ainda está falhando.

## No-idle

No-idle não deve ser autoridade normal de rota. Ele é uma proteção. Sua função é perceber quando o board está parado, quando um worker declarou artefatos que não podem ser lidos, quando trabalho ready não é despachado ou quando um loop de reparo está se duplicando.

Um sistema no-idle válido precisa falhar alto quando ainda existe trabalho incompleto. Heartbeat não é progresso.

## Bloqueios

A fábrica separa bloqueios em dois tipos amplos:

- bloqueios não humanos que a fábrica deve reparar ou re-rotear;
- gates de autoridade humana que exigem decisão real do operador.

Artefato faltando, worker stale, readback falhando ou revisão interna necessária não devem ser jogados no operador. Acesso de produção, fundos, autoridade de signer, aprovação de release ou aceite de risco podem exigir humano.

## Receipt Five

Receipt Five é o pacote final de evidência. Ele deve incluir pedido, evidência de artefato, evidência de verificação, evidência de revisão, decisão de release/bloqueio e riscos restantes.

Um Receipt Five não é resumo decorativo. É a fronteira de prova entre trabalho em andamento e uma afirmação que a fábrica consegue defender.

## Segurança e risco

Segurança não é checklist tardio. É questão de rota e arquitetura. Risco material pode exigir threat modeling, trust boundaries, identidade/autorização, supply chain, segredos, privacidade, incident response e dono de risco residual.

A fábrica não deve prometer segurança perfeita. Ela deve prometer a melhor postura possível sustentada por evidência, gates e decisões explícitas sobre risco residual.

## Fronteira honesta de afirmação

Validação local pode provar que o kernel público está coerente. Não pode provar que uma execução privada de produto está pronta para produção. Readiness de produto exige estado de runtime, evidência específica do produto, revisão, Receipt Five e aprovação humana quando o risco exigir.
