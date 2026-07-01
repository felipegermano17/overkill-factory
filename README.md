# Overkill Factory

A Overkill Factory é uma fábrica de trabalho para projetos operados com Hermes.

Ela recebe um pedido, preserva a fonte, registra entendimento, monta a verdade do produto, escolhe rota e método, quebra o trabalho em unidades pequenas e acompanha a execução no Hermes até evidência, revisão, decisão e fechamento.

## Documentação

- [Entrada](docs/pt-BR/index.md)
- [Manual](docs/pt-BR/manual.md)
- [Linha de produção](docs/pt-BR/linha-de-producao.md)
- [Uso](docs/pt-BR/uso.md)
- [Para mantenedores](docs/pt-BR/para-mantenedores.md)
- [Mapa visual público](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)

## Primeiro teste local

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Um teste local passando significa que o checkout e o kernel público estão coerentes. Ele não prova execução viva no Hermes, entrega de produto privado, aprovação de produção ou evidência de worker de um run real.

## Estrutura

```text
docs/pt-BR/           documentação pública canônica
factory/              scripts, schemas, templates, agents, exemplos e testes
factory/legacy-docs/  documentação antiga preservada como histórico
```
