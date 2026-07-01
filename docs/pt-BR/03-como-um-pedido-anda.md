# Como um pedido anda

A máquina tem um workflow detalhado. Você não precisa começar por ele.

O caminho humano é este:

```text
pedido -> fonte preservada -> entendimento -> verdade do produto -> rota e método -> trabalho pequeno -> Hermes -> worker result -> readback -> review -> decisão humana quando precisa -> entrega, bloqueio ou aprendizado
```

## 1. Pedido

Tudo começa com um sinal: frase, bug, repo, documento, incidente, tela, release ou decisão.

Nesse momento a fábrica ainda não sabe o suficiente. Executar direto seria chute.

## 2. Fonte preservada

A fábrica guarda mensagem original, anexos, links, repo, documentos e contexto antes de resumir.

Isso evita que um resumo ruim destrua justamente a parte que explicaria uma decisão depois. O nome interno `F0 — Pre-Start / Sealed Source Envelope` existe para a máquina e para os testes. A leitura humana é simples: selar a fonte antes de interpretar.

## 3. Entendimento

A fábrica separa cinco coisas:

- fato: veio da fonte;
- inferência: parece provável, mas não é fonte;
- decisão: já foi escolhido por autoridade válida;
- conflito: duas fontes dizem coisas incompatíveis;
- lacuna: falta informação para seguir com segurança.

Sem isso, palpite vira escopo e lacuna vira trabalho invisível.

## 4. Verdade do produto

Agora a fábrica define o que será entregue, para quem, com quais limites, que risco existe e que prova encerra a discussão.

O nome interno é Product SOT. A tradução útil é verdade do produto. Ele impede que frontend, backend, QA, segurança e operador trabalhem em versões diferentes do mesmo pedido.

## 5. Rota e método

Bug, release, incidente, interface, documentação, segurança, agente, integração e Solana não pedem a mesma prova.

A rota responde: que tipo de trabalho é esse?

O método responde: como esse trabalho será feito e provado?

Se o método não muda a prova, é só rótulo.

### Verdade do produto não é resumo

Um resumo diz: “o usuário quer onboarding”. Verdade do produto diz o que onboarding significa neste produto, quem entra no fluxo, onde a jornada começa, onde termina, o que está fora de escopo, quais riscos importam e que prova encerra a discussão.

Um Product SOT fraco parece assim:

```text
Construir onboarding. Deixar bom. Usar o design atual.
```

Isso não sustenta produção controlada. Essa frase dá permissão para o worker inventar o produto.

Um Product SOT utilizável é explícito:

```text
Usuário: admin novo de workspace.
Objetivo: criar workspace e chegar ao primeiro estado útil do dashboard.
Precisa incluir: criação de conta, nome do workspace, etapa de convite, loading, vazio, confirmação.
Fora de escopo: billing, KYC, editor de papéis do time, migração de email em produção.
Riscos: permissão de conta, entregabilidade de email, estado vazio confuso, overflow mobile.
Prova de aceite: screenshots Product Face, teste de primeira jornada, checagem de estado no backend, review, Receipt Five.
Lacuna aberta: convite usa provider real existente ou provider mockado em staging.
```

A Factory trata esses campos de formas diferentes. “Precisa incluir” vira trabalho. “Fora de escopo” protege contra deriva. “Riscos” viram gates. “Prova de aceite” vira contrato de evidência. “Lacuna aberta” vira descoberta da própria fábrica ou decisão real do operador.

### Rota muda o formato do trabalho

Uma rota de bug não deve agir como produto greenfield. Uma rota de release não deve agir como documentação. Uma rota mainnet não deve agir como UI local.

```text
Tipo de pedido                    Melhor rota/método                 Prova exigida
Bug com regressão                 reparo de bug / test-first          reprodução falhando antes, regressão passando depois
Jornada visual de UI              experiência / design-first          Product Face packet, screenshots, prova da jornada
Dependência sensível              segurança / security-first          revisão de risco, scan, risco residual, review independente
Legado desconhecido               diagnóstico / baseline-first        baseline, hipótese, rollback, guarda de regressão
Promoção para produção            release / gate-first                memo de release, rollback, evidência, aprovação humana
Mainnet ou fundos                 onchain / authority-first           dry run, limite de assinatura, pacote de risco, aprovação explícita
```

Método que não muda artefatos, worker packets, reviewers, gates ou evidência não é método. É decoração.

### Exemplo contínuo

Se o pedido é “construir o fluxo de onboarding do cliente”, a Factory não deve criar imediatamente um card chamado “codar onboarding”. Primeiro ela decide se isso é criação de produto, reparo de UI, workflow backend, documentação, release ou descoberta. Se falta usuário, estado de sucesso, fora de escopo e prova de aceite, executar é prematuro.

Se o pedido é “usuários não conseguem resetar senha depois do último release”, a Factory não deve pedir pacote de design primeiro. Ela preserva a fonte de reprodução, cria rota de regressão, exige teste falhando ou reprodução equivalente e bloqueia done até provar aquele comportamento corrigido.

Se o pedido é “promover versão 1.2.0 para produção”, a Factory não deixa worker se autoaprovar. Ela monta evidência de release, rollback, risco residual e autorização humana.

## 6. Capacidade e autoridade

Antes de mandar worker, a fábrica confere se existe capacidade, acesso, pack especializado e autoridade.

Se toca segredo, produção, mainnet, carteira, assinatura, fundos ou risco material, a régua sobe. Se falta capacidade, bloqueia. Se falta decisão humana, prepara pacote. Se falta readback, anexo ou revisão, a fábrica resolve; não joga no operador.

## 7. Trabalho pequeno

O produto vira unidades executáveis.

Unidade boa tem entrada, saída, dono, dependência, prova, reviewer e regra de pronto. Unidade ruim diz apenas “construa o produto”.

Sem isso, o agente recebe intenção, não tarefa.

## 8. Hermes como chão vivo

Hermes Kanban continua sendo a fonte de verdade do runtime.

Cards, dependências, workers, comentários, anexos, bloqueios e transições aparecem ali. A Factory não deve manter estado paralelo escondido. Ela cobra contrato; Hermes mostra o trabalho vivo.

## 9. Worker result e readback

O worker devolve resultado estruturado e evidência. A fábrica relê.

Se o worker disse que criou arquivo, a fábrica lê. Se disse que anexou prova, confere. Se disse que rodou teste, olha comando e saída. Se disse que a interface ficou boa, olha a superfície.

## 10. Review consumido

Review só vale quando muda estado.

Se passa, destrava. Se falha, cria reparo. Se aponta risco, registra dono e consequência. Se pede decisão, vira pacote humano.

## 11. Decisão humana

Algumas decisões pertencem ao operador: produção, mainnet, fundos, segredos, orçamento, release, waiver, risco residual e mudança de autoridade.

Nesses casos, a fábrica prepara contexto. O humano não aprova no escuro.

## 12. Fechamento

O pedido termina em estado honesto:

- entregue, quando há prova suficiente;
- bloqueado, quando falta algo material;
- aprendizado, quando a execução mostra que a própria fábrica precisa mudar.

A fábrica boa não força final feliz. Ela diz a verdade operacional.
