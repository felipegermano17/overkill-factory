# Overkill Factory

A Overkill Factory é uma fábrica de produto para trabalho com agentes. Não é um prompt grande, não é uma lista de tarefas e não é só uma casca em volta de um agente de código. Ela pega um pedido ainda meio cru e transforma isso em produção controlada: fonte, definição do produto, método, pacotes de trabalho, execução no Hermes, revisão, evidência, entrega ou bloqueio, e depois aprendizado.

O kernel público atual está na versão `3.0.2`. Ele expõe 26 fases compiladas, 14 classes de rota, 8 motores de método, 17 áreas de sistema operacional da fábrica, 40 workers públicos, 244 schemas JSON, 156 templates JSON e 97 testes. Esses números não estão aqui para enfeitar. Eles mostram que esta documentação está presa ao repositório que roda, não a uma narrativa bonita.

## Por que isso existe

Trabalho com agente costuma falhar de jeitos bem comuns. O agente começa cedo demais. O briefing está frouxo. O worker errado assume a tarefa. Um revisor diz "parece bom" sem reler a evidência. Um gate humano vira uma pergunta vaga no chat. Uma execução é marcada como pronta porque um arquivo existe, não porque o produto pedido ficou realmente usável.

A Overkill Factory existe para tornar esses erros mais difíceis.

O objetivo é tornar a velocidade confiável. Não adianta o agente ser rápido se a fábrica não sabe exatamente o que ele deve fazer, quem tem autoridade para fazer, qual prova precisa voltar e o que acontece quando a prova não aparece.

## A imagem simples

Um pedido entra na fábrica. Antes de sair fazendo, a fábrica protege a fonte: o que o operador pediu de verdade, que material existe, o que falta e o que não pode ser inventado. Depois ela cria a verdade do produto, escolhe um método, divide o trabalho em unidades pequenas, manda os workers certos pelo Hermes, checa os resultados e decide: entrega, bloqueia ou aprende.

Por dentro isso é complexo. Tem que ser. Criar produto de verdade é complexo. Mas a experiência do operador deveria ser simples: pedir, ver o estado, receber decisões claras e exigir prova quando alguém disser que terminou.

## Por onde começar

Leia nesta ordem:

1. [Manual](manual.md), para entender a ideia sem jargão.
2. [Modelo operacional](operating-model.md), para ver o que acontece numa execução.
3. [Ciclo da fábrica](lifecycle.md), para acompanhar fase por fase.
4. [Confiança e evidência](trust-and-evidence.md), para entender como a fábrica evita progresso falso.
5. [Uso](usage.md), para rodar comandos agora.

Quem vai contribuir no código pode seguir para [Modelo técnico](technical-model.md) e [Referência](reference.md). Quem só quer entender o produto consegue parar no manual e no modelo operacional sem ficar perdido.

## Primeira prova local

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Um teste local passando significa que o kernel público está coerente. Não significa que um produto privado foi entregue, que um runtime Hermes vivo está configurado, nem que um humano aprovou uma decisão de risco. A documentação deixa essa fronteira visível de propósito.

## O que mudou nesta documentação

A documentação antiga tinha valor para manutenção, mas parecia um conjunto de departamentos internos. A documentação atual é um manual de produto. O material antigo foi preservado em `factory/legacy-docs/` por histórico e compatibilidade. A árvore pública `docs/` agora é a explicação canônica.
