# Overkill Factory

A Overkill Factory é uma fábrica de produto para trabalho com agentes em cima do Hermes.

Ela não é chatbot, não é SaaS, não é um segundo Hermes. O Hermes é dono do chão de runtime: boards, cards, dependências, typed blocks, dispatch, execução de workers, comentários, logs e transições de estado. A Overkill Factory é dona do método de produção: intake, verdade de fonte, definição de produto, escolha de método, gates, autoridade de workers, evidência, revisão, decisões de release e learnback.

O kernel público neste repositório está na versão `3.0.2`. A superfície executável atual contém 26 fases compiladas, 14 classes de rota, 8 method engines, 17 áreas de operating system, 40 workers públicos, 244 schemas, 156 templates e 97 testes.

## A explicação mais curta que ainda é útil

Um pedido entra na fábrica. A fábrica não manda imediatamente um agente construir. Ela primeiro protege a fonte, entende o material, confirma a verdade do produto, escolhe o método correto, checa risco e capacidade, transforma o trabalho em unidades limitadas, despacha especialistas pelo Hermes, exige evidência, revisa o resultado e só então libera, bloqueia ou aprende.

```text
fonte -> entendimento -> verdade do produto -> método -> plano -> work units
-> workers Hermes -> evidência -> revisão -> release ou bloqueio -> learnback
```

O objetivo não é deixar agentes lentos. O objetivo é tornar a velocidade confiável.

## Para quem esta documentação existe

Leia se você é:

- operador que quer rodar trabalho de produto pela fábrica;
- investidor ou parceiro técnico tentando entender o sistema;
- pessoa não técnica querendo entender a ideia sem jargão interno;
- engenheiro que precisa inspecionar ou contribuir com o kernel público;
- agente que precisa continuar trabalho sem depender de memória privada do chat.

## Caminho de leitura

1. **Manual** explica o produto e o modelo mental.
2. **Modelo Operacional** explica a fábrica em movimento.
3. **Ciclo da Fábrica** explica cada fase compilada.
4. **Confiança e Evidência** explica como a fábrica evita falso progresso.
5. **Modelo Técnico** explica a implementação.
6. **Uso** traz os comandos do primeiro teste local.
7. **Referência** junta termos, comandos, paths e registries.

English version: [English](../en/index.md).

## Primeiro teste local

Em um checkout deste repositório:

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Um teste local passando significa que o kernel público e o caminho mínimo estão coerentes. Não significa que um runtime Hermes real de operador entregou um produto específico. Entrega real de produto ainda exige estado Hermes, resultado de workers, readback, revisão, Receipt Five e qualquer gate humano necessário.
