# Definição de produto / PRD

A definição de produto é o alvo da run.

Em linguagem comum, essa é a área de PRD. Alguns contratos internos antigos podem usar Product SOT. A documentação pública deve explicar primeiro PRD / definição de produto, porque é mais claro para quem está lendo.

## Por que a fábrica precisa disso

Agentes conseguem executar rápido sem entender completamente o produto. Isso é perigoso.

Um worker pode implementar uma fatia visível e perder o resultado real. Uma tarefa de documentação pode criar páginas sem explicar o produto. Um bugfix pode corrigir sintoma e ignorar risco de release.

A definição de produto evita isso ao declarar o alvo antes da execução oficial.

## O que contém

Uma definição útil responde:

- o que será construído;
- para quem;
- qual problema resolve;
- o que está no escopo;
- o que está fora;
- quais jornadas importam;
- como sucesso será provado;
- quais exemplos definem aceite;
- quais riscos importam;
- quais dependências existem;
- que acesso/ambiente é necessário;
- que evidência prova conclusão;
- que decisões exigem humano.

## Fonte versus verdade de produto

A mensagem do operador é fonte. Ela não vira verdade final automaticamente.

A fábrica pode inferir uma definição candidata, mas precisa rotular inferência. Se a inferência muda direção de produto, pode exigir aprovação humana.

## PRD e Product SOT

Product SOT é um nome técnico/interno antigo para essa mesma região de controle: a fonte de verdade da intenção de produto.

Para o público, PRD / definição de produto é melhor.

## Estados possíveis

A definição pode estar:

- candidata;
- aprovada;
- parcial;
- bloqueada;
- substituída.

A fábrica não deve parar por qualquer imperfeição. Ela deve seguir no que for seguro e pedir decisão só quando o ponto realmente muda a rota.

## Como controla execução

A definição alimenta cobertura de escopo, método, decomposição, exemplos de aceite, evidência, release e Receipt Five.

Se um resultado de worker não aponta para a definição de produto, ele pode ser útil, mas não basta para fechar o trabalho.
