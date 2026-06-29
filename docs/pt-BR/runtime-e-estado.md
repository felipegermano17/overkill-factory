# Runtime e estado

A Overkill Factory separa runtime de método.

Essa separação é uma das ideias mais importantes do sistema.

## Hermes é o runtime

Hermes guarda o chão de fábrica:

- boards;
- cards;
- dependências;
- status;
- bloqueios tipados;
- dispatch;
- tarefas de workers;
- runs;
- logs;
- comentários.

Se a próxima ação vive só no chat, ela é frágil. Se vive no Hermes, pode ser retomada, inspecionada e reparada.

## A fábrica é o método

A fábrica define as regras:

- fronteira de fonte;
- definição de produto / PRD;
- método;
- rota de risco;
- rota de capacidade;
- formato de worker packet;
- gates;
- evidência;
- revisão;
- gate humano;
- release;
- Receipt Five.

A fábrica não substitui Hermes. Ela usa Hermes como runtime e falha fechado quando alguém tenta burlar esse caminho.

## Por que importa

Sem essa separação, um agente pode falar com confiança e parecer a fábrica.

Isso não é aceitável.

Trabalho oficial precisa de estado durável e contratos. Resultado de worker precisa se conectar a packet, card, evidência e requisito pai. Release precisa se conectar a gates, revisão e Receipt Five.

## Categorias de estado

Uma run saudável separa:

- estado de fonte;
- estado de produto;
- estado de runtime;
- estado de evidência;
- estado de decisão;
- estado de fechamento.

Quando essas coisas se misturam, fica difícil confiar.
