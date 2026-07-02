# Overkill Factory

Idioma: [English](README.md) | Portugues

A Overkill Factory e uma fabrica de produto operada por agentes de IA.

A funcao dela e simples de falar e dificil de fazer: transformar um pedido humano bruto em uma entrega verificavel sem deixar agente fingir que houve progresso.

Em vez de pedir para uma IA "faz esse app" e torcer para ela entender, planejar, implementar, testar, revisar e entregar certo, a Factory transforma o pedido em uma linha de producao:

1. preserva a fonte,
2. separa fato de suposicao,
3. define a verdade oficial do produto,
4. escolhe o metodo certo para o risco,
5. quebra o trabalho em unidades pequenas,
6. despacha workers especializados,
7. exige evidencia,
8. faz revisao independente,
9. chama o humano so quando existe autoridade real,
10. fecha com Receipt Five ou com bloqueio honesto.

O objetivo nao e fazer a IA parecer mais organizada. O objetivo e impedir teatro: arquivos bonitos, cards movimentados, resumos confiantes e mensagens de "pronto" sem prova.

## Leia Primeiro

- [Manual da fabrica](docs/pt-BR/factory-manual.md) - explicacao completa, humana e direta.
- [Referencia tecnica](docs/pt-BR/technical-reference.md) - repo, Hermes, fases, rotas, workers, comandos e limites de prova.
- [Mapa visual](docs/assets/public-map/overkill-factory-map-v1.0.3.html) ([copia publica](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)) - explicacao visual completa criada com Archify.
- [Manual em ingles](docs/en/factory-manual.md) e [referencia tecnica em ingles](docs/en/technical-reference.md) - superficie primaria do projeto.

## O Modelo Mental Simples

Voce e o dono da fabrica.

O gerente e quem fala com voce.

Hermes e o chao de fabrica onde trabalho vivo, cards, sessoes, workers e evidencias existem.

O Kanban e a parede viva do trabalho.

Workers sao especialistas.

Schemas e templates sao formularios oficiais.

Validadores sao fiscais.

Evidencias sao o rastro de recibos.

Human gates sao decisoes reais de autoridade.

Receipt Five e o recibo final.

Learnback e como a Factory melhora depois de falhas reais.

## O Que Existe Neste Repositorio

Este repositorio contem o kernel publico da Factory.

- `docs/`: a superficie pequena de documentacao publica.
- `factory/`: implementacao, contratos, validadores, exemplos, fixtures, testes e adaptadores Hermes.
- `docs/assets/public-map/overkill-factory-map-v1.0.3.html`: o mapa visual completo.

O kernel publico neste checkout tem 26 fases compiladas, 14 classes de rota, 8 motores de metodo, 17 areas operacionais, 40 workers publicos, 251 schemas JSON, 163 templates JSON e 102 arquivos de teste Python.

Esses numeros provam que o repo tem kernel estruturado. Eles nao provam que uma execucao privada de produto foi entregue.

## Prova Local Rapida

A partir da raiz do repositorio:

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Um teste local passando significa que o kernel publico esta coerente. Isso nao prova entrega viva no Hermes, deploy de producao, mainnet, execucao de workers em board real ou aprovacao humana.

Para provar uma entrega real de produto, a Factory precisa de estado Hermes vivo, cards atuais, resultado de worker, evidencia, readback, revisao independente, human gates obrigatorios e Receipt Five.

## Regra De Ouro

Nada esta realmente pronto porque um agente disse que esta pronto.

Esta pronto quando a Factory consegue mostrar o que foi pedido, o que foi produzido, qual evidencia sustenta a entrega, quem revisou, qual risco restou e qual estado final foi autorizado.
