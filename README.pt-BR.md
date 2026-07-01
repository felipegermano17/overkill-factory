# Overkill Factory

Idioma: [English](README.md) | Português

Agente ajuda. Mas agente também sabe parecer pronto antes de estar provado.

A Overkill Factory é um sistema de produção para trabalho com agentes em cima do Hermes. Você manda um pedido; a fábrica preserva a fonte, transforma aquilo em trabalho pequeno, roda os agentes pelo Hermes, cobra prova, consome revisão e só chama de pronto quando existe recibo.

A ideia é simples: andar rápido sem transformar o operador em QA, auditor, gerente e detetive de cada agente.

## O problema

Sem uma fábrica, o operador vira o sistema de qualidade. Ele precisa conferir se o agente entendeu o pedido, se não inventou escopo, se testou o comportamento certo, se alguém revisou, se o risco foi aceito e se o “feito” quer dizer alguma coisa.

Isso funciona para uma tarefa pequena. Não funciona para produto, release, segurança, operações ou trabalho com dinheiro, produção, mainnet, segredo ou decisão humana.

## O que a Factory faz

Ela não tenta substituir o Hermes. Hermes é o chão vivo: cards, workers, dependências, comentários, anexos, bloqueios e transições.

A Factory é o contrato de produção em volta desse chão. Ela define como o pedido vira fonte preservada, verdade de produto, rota, método, worker packet, worker result, readback, review, gate humano e Receipt Five.

Em português claro:

- a fonte original não pode ser destruída por resumo cedo;
- fato, palpite, conflito e lacuna precisam ficar separados;
- worker não recebe “faz o produto”, recebe trabalho limitado;
- prova precisa provar o pedido certo;
- humano só entra quando a autoridade é humana;
- teste local não vira prova de entrega viva;
- pronto quer dizer recibo, não confiança no tom do agente.

## Comece por aqui

- [Documentação em português](docs/pt-BR/index.md)
- [English documentation](docs/en/index.md)
- [Mapa visual público](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)

Se você está chegando agora, leia `docs/pt-BR/01-comecar-aqui.md` e depois `docs/pt-BR/03-como-um-pedido-anda.md`.

Se você vai operar, leia `docs/pt-BR/04-experiencia-do-operador.md`, `docs/pt-BR/05-prova-e-recibos.md` e `docs/pt-BR/06-decisoes-humanas.md`.

Se você vai manter o repo, leia `docs/pt-BR/10-validacao-local.md`, `docs/pt-BR/11-referencia-do-repositorio.md` e `docs/pt-BR/13-guia-de-manutencao.md`.

## Primeiro teste local

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Um teste local passando significa que o kernel público está coerente. Não prova que um runtime Hermes real de operador entregou um produto específico.

## O que este repositório prova

O repositório público prova contratos verificáveis: docs públicas, workflow compilado, catálogos públicos, rotas, métodos, operating-system areas, schemas, templates, worker registries, exemplos, fixtures, scripts e testes.

Ele não prova sozinho entrega privada, aprovação humana real, execução em Hermes vivo, prontidão de produção, mainnet, fundos ou autorização operacional. Essas coisas precisam de estado atual no Hermes, worker results, evidência específica, revisão consumida, Receipt Five e gate humano quando o risco pedir.

## Estrutura

```text
README.md              entrada pública em inglês
README.pt-BR.md        entrada pública em português
docs/                  documentação pública canônica e catálogos públicos
factory/               implementação, schemas, templates, workers, testes, exemplos, docs legadas
```

Dentro de `factory/`, as áreas públicas importantes são `agents/`, `examples/`, `fixtures/`, `schemas/`, `scripts`, `skills`, `templates` e `tests`.

As docs públicas antigas foram preservadas em `factory/legacy-docs/` por compatibilidade histórica. Elas não são fonte canônica de verdade.

## Status público

O status, as contagens e os limites de prova ficam em `docs/pt-BR/09-status-limites-e-prova.md`. O conjunto atual inclui 40 workers públicos. Números de fases, rotas, métodos, schemas, templates e testes devem ser lidos dos registries e validadores, não copiados manualmente para toda página.

## Contribuir sem quebrar a verdade pública

Antes de abrir PR que altera documentação pública, rode:

```bash
cd factory
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
python3 scripts/generate_factory_reference_docs.py --check
python3 -m unittest tests.test_open_source_docs -q
```

Generated worker packets, gate reports, private runtime evidence and temporary outputs belong in `.tmp/`, not in public documentation.
