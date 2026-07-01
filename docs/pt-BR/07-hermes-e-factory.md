# Hermes e a Factory

Hermes e Overkill Factory não fazem a mesma coisa.

Hermes é o runtime vivo. A Factory é o contrato de produção em volta dele.

## O que Hermes guarda

Hermes guarda cards, status, workers, dependências, comentários, anexos, workspaces, bloqueios, transições e estados concluídos.

É ali que o trabalho vivo precisa aparecer. Se existe execução real, ela deve aparecer no Hermes.

## O que a Factory define

A Factory define rotas, métodos, gates, worker packets, worker results, requisitos de evidência, Receipt Five, autoridade proibida, readback, revisão e política de bloqueio.

Ela não deve criar um segundo quadro escondido. Estado paralelo vira fonte de mentira.

## Por que essa divisão importa

Se Hermes tenta decidir tudo sozinho, vira Kanban com confiança demais.

Se a Factory tenta guardar estado vivo fora do Hermes, vira mini-Hermes escondido.

A fronteira correta é: Hermes mostra o chão; a Factory define a disciplina de produção.

## No-idle

No-idle existe para perceber silêncio perigoso.

Se há trabalho pronto, despacha. Se há dependência real, espera. Se falta decisão humana e o pacote está pronto, chama o operador. Se falta readback, artefato, revisão ou evidência, a fábrica repara.

No-idle não inventa autoridade, não aprova gate, não conclui card e não usa o operador como lixeira de bloqueio interno.

## Adapter e gates

Adapters e hooks podem transportar contexto e bloquear transições inseguras. Eles não devem transformar presença de arquivo em pass, nem fechar card sem Receipt Five, nem promover worker sem rota.

## Perfis Hermes

Perfis Hermes materializam papéis de worker. Profile names alone are not enough. O worker precisa de registry, profile, permission class, binding, packet route e validação.

A fonte pública de profiles é `agents/hermes-profile-bindings.public.json`. A prontidão viva ainda exige smoke/eval atual quando alguém quiser afirmar runtime readiness.
