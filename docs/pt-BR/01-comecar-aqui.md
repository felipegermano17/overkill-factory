# Começar aqui

A Overkill Factory é um sistema de produção para trabalho com agentes.

Ela transforma pedidos vagos em trabalho pequeno, rastreável e provado. A ideia é simples: o agente pode executar, mas não pode inventar escopo, esconder risco, aprovar o próprio trabalho ou dizer “pronto” sem prova.

Isso é produção controlada.

## Para quem isso existe

Existe para quem usa agentes em produto, código, release, revisão, operação, incidente ou documentação e cansou de virar fiscal do processo.

Sem fábrica, você precisa conferir se o agente entendeu o pedido, se a fonte não foi resumida errado, se o teste prova o comportamento certo, se o risco foi aceito por alguém, se o review foi consumido e se o bloqueio é seu ou da própria fábrica.

Se você precisa fazer isso manualmente a cada card, o agente pode até ser útil, mas a operação ainda depende demais de você.

## O exemplo mais simples

Você escreve:

> Quero lançar o onboarding novo amanhã.

Um agente solto pode responder “ok, fazendo” e começar pela tela. Isso parece produtivo, mas talvez já esteja errado.

Cliente de quê? Usuário final, operador interno, investidor, admin, wallet holder? Onboarding até onde? Criar conta, conectar carteira, passar por KYC, assinar transação, fazer primeiro depósito, entrar num grupo, ver dashboard? Toca pagamento, dados sensíveis, produção, mainnet, fundos ou segredo? Existe Figma? Existe backend? O que conta como sucesso?

A fábrica segura a pressa. Ela guarda a fonte, separa fato de palpite, identifica conflito, define a verdade do produto, escolhe a rota, quebra o trabalho e só então manda workers executarem pelo Hermes.

## O que você recebe

Você recebe leitura do pedido, definição de produto, plano pequeno, status no Hermes, bloqueios com dono, pedido humano bem formado quando necessário e recibo final.

O recibo final não é “o agente disse que terminou”. É uma história verificável: o pedido era este, a fonte usada foi esta, o trabalho feito foi este, a prova é esta, a revisão disse isto, o que ainda falta é aquilo.

## O que ela não promete

Ela não promete que agentes nunca erram. Ela não substitui decisão humana. Ela não transforma teste local em prova de produto vivo. Ela não deve fingir que um pedido vago virou produto completo se ainda faltam fonte, autoridade, capacidade ou evidência.

A promessa é outra: tornar erro, lacuna, risco e bloqueio visíveis cedo o bastante para você não descobrir tarde demais.

## Continue

Leia [O problema do produto](02-fluxo-da-fabrica-e-arquitetura-hermes.md) se quiser entender por que agente bom não basta. Leia [Como um pedido anda](02-fluxo-da-fabrica-e-arquitetura-hermes.md) se quiser ver o fluxo completo.
