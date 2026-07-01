# Guia de manutenção

A documentação pública é parte do produto. Se ela apodrece, a fábrica volta a depender de memória de chat.

## Quando uma mudança precisa mexer na doc

Atualize docs quando mudar comportamento público, comando, schema, route class, method engine, worker, gate, boundary, claim, README, mapa público ou validação.

## Como atualizar README

README é entrada, não inventário. Ele deve continuar curto, claro e sem jargão inicial. Detalhes técnicos vão para referência, validação ou status.

## Como atualizar MkDocs

A navegação deve responder perguntas reais, não nomes internos. Não reintroduza `manual.md`, `lifecycle.md` ou estrutura antiga como navegação canônica.

## Como atualizar manifest

`docs/public-surface.manifest.json` protege links, frases obrigatórias, source refs e fronteiras de prova. Ao criar página pública nova, registre no manifest.

## Como atualizar testes

`tests/test_open_source_docs.py` deve proteger estrutura, profundidade, ausência de claims falsas e build MkDocs. Não use testes para congelar copy ruim.

## Como atualizar contagens

Conte fases, routes, methods, operating-system areas, workers, schemas, templates e tests com ferramenta. Não atualize número manualmente sem verificar.

## Como preservar legado

Docs antigas ficam em `factory/legacy-docs/`. Use como evidência histórica, não como copy canônica. Se trouxer conteúdo de volta, traduza para a nova estrutura.

## O que nunca publicar

Não publique segredo, caminho privado, runtime evidence privado, generated worker packet, gate report sensível, screenshot com dados privados, output temporário ou decisão humana não sanitizada.

## Checklist antes de PR

- README continua humano?
- Páginas principais começam pela dor do leitor?
- Termos internos aparecem depois da explicação humana?
- Exemplos bons e ruins existem onde importam?
- Local proof vs live delivery está claro?
- Manifest atualizado?
- MkDocs strict passa?
- Validadores públicos passam?
- Suíte relevante passa?

## Checklist antes de merge

- CI verde.
- Nenhuma página antiga voltou à navegação canônica.
- Não há claim de runtime sem prova viva.
- Não há arquivo gerado trackeado por acidente.
- EN e PT têm a mesma estrutura e os mesmos fatos, mesmo que a voz seja nativa em cada idioma.
