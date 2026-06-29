# Experiência do operador

A experiência do operador é o que o humano deve sentir ao usar a fábrica.

A fábrica pode ter muitos contratos, scripts e workers por dentro. Mas o operador não deve ser obrigado a acompanhar essa máquina no detalhe. Ele deve sentir organização, honestidade e progresso.

## O que o operador envia

O operador envia um sinal: ideia, brief, repo, bug, release, incidente, migração, screenshot, design ou documento.

O sinal não precisa vir perfeito. A fábrica existe para estruturar.

## O que o gerente faz primeiro

O gerente responde com entendimento controlado.

Uma boa resposta inicial explica:

- o que foi entendido;
- que tipo de trabalho parece ser;
- qual fonte foi recebida;
- quais suposições foram feitas;
- o que pode avançar sem input;
- o que exige decisão humana;
- qual é o próximo estado da fábrica.

## O que o operador não deveria fazer

O operador não deveria precisar:

- lembrar a próxima tarefa do agente;
- abrir Kanban só para acordar a fábrica;
- aprovar retry interno;
- interpretar log cru;
- repetir fonte já registrada;
- perguntar se “done” tem evidência;
- manter contexto vivo manualmente.

Se a fábrica pode continuar com segurança, ela continua. Se não pode, ela explica exatamente por quê.

## Atualizações de progresso

Atualização ruim:

```text
F12 waiting_dependency, reducer pending.
```

Atualização boa:

```text
A definição do produto foi aprovada. A fábrica dividiu o trabalho em seis unidades. Duas podem rodar agora, uma espera prova visual e uma precisa da sua aprovação porque afeta produção.
```

O estado interno pode existir. Ele só não deve ser a linguagem principal para o operador.

## Gate humano

Gate humano é pedido de decisão.

Ele deve trazer decisão necessária, motivo, evidência, opções, consequências, recomendação, padrão seguro e o que acontece depois.

## Entrega final

A entrega final deve vir com Receipt Five: o que mudou, onde está, como foi verificado, o que revisou e o que resta.
