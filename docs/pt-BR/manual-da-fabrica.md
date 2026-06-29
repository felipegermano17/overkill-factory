# Manual da fábrica

Este manual explica a Overkill Factory como sistema de produto.

Ele é para quem quer entender o que a fábrica faz, por que ela existe e como ela se comporta quando chega trabalho real.

## 1. A promessa

A Overkill Factory pega um sinal inicial e transforma em trabalho de produto controlado.

Esse sinal pode estar bagunçado. Pode ser uma ideia, bug, repo, documento de produto, incidente, migração, pedido de release ou notas soltas.

A promessa não é “um agente vai tentar”.

A promessa é:

- fonte separada de suposição;
- definição de produto explícita;
- método escolhido antes da execução;
- trabalho materializado no Hermes;
- workers com tarefas limitadas;
- reparo automático do que for recuperável;
- humano chamado só para decisão humana real;
- conclusão com evidência;
- fechamento com Receipt Five.

## 2. Por que isso existe

Trabalho com agente costuma falhar entre uma etapa e outra.

O modelo esquece. O plano parece completo, mas não vira estado durável. Um worker é criado, mas não entrega resultado. Um teste passa, mas o produto continua ruim. Um release é chamado de pronto sem rollback, dono ou monitoramento. Uma tarefa sensível começa sem pensar em segurança. Um humano recebe pedido de aprovação sem evidência suficiente.

A fábrica transforma esses problemas em controles claros.

Se a fonte está confusa, é problema de fonte.
Se o alvo do produto está vago, é problema de definição de produto.
Se o caminho não foi escolhido, é problema de método.
Se falta capacidade, é problema de capacidade.
Se existe pacote de worker mas não existe resultado, a execução ainda não aconteceu.
Se falta evidência, não fecha.
Se precisa de decisão humana, o gerente apresenta o pacote de decisão.

## 3. Papéis

### Operador

É a pessoa que pede trabalho e toma decisões humanas reais.

### Gerente

É a voz da fábrica para o humano. Recebe o sinal, organiza entendimento, faz perguntas limitadas, apresenta gates humanos e entrega progresso.

### Hermes

É o runtime. Guarda boards, cards, dependências, status, bloqueios tipados, dispatch, runs, logs e estado das tarefas.

### Fábrica

É o método. Define fonte, PRD, método, gates, pacotes de worker, evidência, revisão, release e Receipt Five.

### Workers

São especialistas limitados. Executam ou revisam uma parte. Não viram a fábrica inteira.

## 4. Primeiro passo: fronteira de fonte

O primeiro passo não é codar.

O primeiro passo é separar o que foi realmente fornecido do que foi inferido.

A fábrica registra:

- o que o operador mandou;
- de onde veio;
- se é produto novo, bug, incidente, release, migração ou continuação;
- quais fatos são explícitos;
- quais suposições foram inferidas;
- o que está faltando;
- o que exige decisão humana.

Isso impede a fábrica de construir em cima de suposição invisível.

## 5. Definição de produto / PRD

Depois da fonte, a fábrica cria ou atualiza a definição de produto.

Em linguagem comum, isso é a área de PRD. Alguns contratos internos antigos podem chamar isso de Product SOT. Para o público, PRD / definição de produto é mais claro.

A definição responde:

- o que será construído;
- para quem;
- qual problema resolve;
- o que entra no escopo;
- o que fica fora;
- quais jornadas importam;
- quais exemplos provam aceite;
- quais riscos existem;
- quais dependências existem;
- qual evidência prova conclusão;
- o que exige aprovação humana.

Não é resumo. É o alvo do trabalho.

## 6. Cobertura de escopo

A fábrica não pode deixar a primeira fatia útil virar o produto inteiro por acidente.

Todo requisito importante precisa ter estado: planejado, feito com evidência, bloqueado, adiado, fora de escopo, dono humano ou substituído por decisão aprovada.

## 7. Método

A fábrica escolhe método antes de executar.

Bug, documentação, produto novo, segurança, design, incidente e release não usam o mesmo processo.

O método define gates, artefatos e evidências.

## 8. Risco e capacidade

A fábrica identifica se o trabalho toca frontend, backend, dados, docs, IA, runtime de agentes, Solana/onchain, pagamentos, chaves, segredos, privacidade, produção, segurança ou release.

Se falta capacidade, ela procura skill, provider, capability pack ou referência antes de bloquear com o operador.

## 9. Arquitetura, experiência e segurança

Trabalho bom é moldado antes da implementação.

Arquitetura define limites e responsabilidades.
Experiência define jornada, estados e prova visual.
Segurança define acesso, segredos, exposição, rollback, monitoramento e revisão.

## 10. Plano e grafo Hermes

A definição vira unidades de trabalho.

Cada unidade tem requisito, dono, revisor, dependências, regra de pronto, regra de bloqueado, regra de feito e evidência exigida.

Depois isso vira estado durável no Hermes.

## 11. Worker packet e worker result

Worker packet é uma tarefa atribuída.

Não é execução.

A ordem correta é:

```text
packet criado
-> dispatch no Hermes
-> tarefa rodando
-> resultado do worker
-> validação do resultado
-> consumo pelo trabalho pai
```

Só resultado válido, com evidência, pode avançar o trabalho.

## 12. Gates

Gate decide se o trabalho pode avançar.

Gates existem para fonte, PRD, escopo, método, capacidade, arquitetura, experiência, segurança, resultado de worker, decisão humana e Receipt Five.

Sem prova, falha fechado.

## 13. Autonomia e no-idle

Autonomia não é o agente lembrar.

Autonomia vem de estado durável no Hermes, contratos da fábrica e no-idle lendo a fronteira atual para acordar a próxima ação segura.

No-idle pode consumir resultado, reparar gap recuperável, despachar trabalho pronto ou emitir bloqueio tipado.

No-idle não aprova gate, não marca done, não substitui Hermes e não transforma reparo interno em pergunta humana.

## 14. Receipt Five

Receipt Five fecha a run respondendo:

1. o que mudou;
2. onde está;
3. como foi verificado;
4. quem ou o que revisou;
5. o que resta.

Sem Receipt Five, não está fechado.

## 15. Status honesto

Teste local prova caminho local. Não prova automaticamente experiência live.

Prova live exige: sinal real do operador, gerente, FactoryRun, board Hermes, workers, progresso entregue e Receipt Five retornando para o operador.
