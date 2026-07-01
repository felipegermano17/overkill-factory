# Referência

Esta página reúne os fatos curtos para quem já leu o manual e quer se localizar no repo. Não substitui os registries nem a referência gerada; traduz os nomes mais importantes para quem precisa operar ou avaliar a fábrica.

## Onde cada coisa mora

- `README.md` e `README.pt-BR.md`: entrada pública curta.
- `docs/en/` e `docs/pt-BR/`: manual público canônico.
- `docs/factory-workflow.catalog.json`: workflow público compilado.
- `docs/promise-implementation-map.public.json`: mapa de promessa pública para implementação.
- `docs/public-surface.manifest.json`: manifest das superfícies públicas.
- `factory/scripts/factoryctl.py`: principal superfície de comando.
- `factory/schemas/`: contratos JSON que dizem o que é registro válido.
- `factory/templates/`: contratos-base, exemplos e registries.
- `factory/agents/`: workers, perfis, bindings Hermes, capability packs e readiness.
- `factory/tests/`: regressão do comportamento da fábrica.
- `factory/legacy-docs/`: docs antigas preservadas para referência técnica; não são o manual público canônico.
- `factory/legacy-docs/generated/`: referência gerada do kernel para maintainers.

## Caminho mental curto

```text
fonte
-> entendimento
-> Product SOT
-> método
-> packs e gates
-> work units
-> Hermes
-> worker results
-> verificação e review
-> Receipt Five
-> release, bloqueio ou learnback
```

Se uma execução parece pronta, mas não consegue apontar para esse caminho, provavelmente está faltando prova.

## Classes de rota

As quatorze classes de rota existem para impedir que todo pedido seja tratado do mesmo jeito.

- `product_creation`: criação de produto; precisa de Product SOT, cobertura de escopo e ready gate.
- `feature_delivery`: feature ou slice; precisa de método, critérios de aceite e prova proporcional ao risco.
- `bug_repair`: bug; precisa de reprodução ou justificativa clara, correção e regressão.
- `incident_response`: incidente; precisa de severidade, mitigação, comunicação e learnback.
- `brownfield_discovery` / `migration_execution`: brownfield, refactor, integração ou migração; precisa de baseline, contrato, regressão e rollback.
- `release_promotion`: release; precisa de prontidão de produção, rollback, owner e autoridade.
- `research_validation`: research; precisa virar decisão operacional, não só comentário inteligente.
- `docs_onboarding`: docs/onboarding; precisa provar utilidade para o leitor ou primeiro sucesso.
- `security_remediation`: segurança; precisa de arquitetura, scans, review e tratamento de risco residual.
- `ux_product_experience`: UX/Product Experience; precisa de Product Face, estados, jornadas, design e review.
- `analytics_data`: analytics/data; precisa de contrato de métrica, privacidade e prova de qualidade.
- `agent_quality_change`: agent/skill/model; precisa de eval, prontidão de perfil e learnback.

## Métodos principais

O método muda a forma de provar o trabalho.

- Spec-first: bom quando o risco é construir a coisa errada.
- Test-first: bom quando comportamento precisa ficar travado por regressão.
- Behavior-first: bom quando jornada e aceite importam mais que detalhe interno.
- Discovery-first: bom quando a pergunta ainda não está madura.
- Security-first: obrigatório quando ameaça, segredo, chave, produção, onchain ou abuso importam.
- Design-first: obrigatório quando a experiência visível é parte do produto.
- Legacy-diagnosis: necessário quando existe sistema antigo, comportamento desconhecido ou migração.
- Incident-first: necessário quando o produto está quebrado, em risco ou exigindo resposta operacional.

## Capability packs

Capability pack é a resposta para: “temos cobertura especialista para este tipo de produto?”.

Packs core atualmente incluem web/SaaS, CLI/TUI, cloud-native, agent-runtime, Solana AI Kit, onboarding e public-docs. Eles ainda precisam dos gates normais, mas a fábrica reconhece cobertura básica.

Packs template incluem mobile nativo, desktop, game, AI/ML, fintech, regulated domain, data analytics, browser extension e hardware/IoT. Esses não devem executar materialmente só porque o card pediu. Precisam de ativação, especialistas, bindings, smoke, eval e evidência.

## Product Face

Product Face é a prova da face do produto. Ele muda conforme a superfície:

- web visual: screenshots, viewports, estados, console, acessibilidade básica e overflow;
- CLI/TUI: transcript, help, instalação, erro e comportamento no terminal;
- docs/onboarding: replay do primeiro sucesso, links e critério do leitor;
- interface agentic: controle do usuário, permissões, memória/dados, recuperação e limites;
- wallet/onchain UI: prova visual mais fronteira de assinatura, transação e chave.

Product Face Packet é planejamento. Product Face Result é prova.

## Workers e autoridade

Worker não é personagem de prompt. Para ser operável, precisa de quatro camadas:

1. papel no registry público;
2. perfil de agente;
3. binding Hermes;
4. worker packet específico do card.

O worker executa dentro da autoridade recebida. Ele não aprova gate, não inventa evidência, não toca produção, não mexe em chaves e não muda escopo fora do contrato.

Accountability de worker é separada da identidade do worker. Saídas ruins repetidas, falhas, rework, artefatos rasos, reprovação em review ou loops de reparo entram em um `worker_accountability_ledger`. Esse ledger é public-safe e guarda apenas referências sanitizadas de evidência. As consequências de rota são determinísticas: observação, review independente obrigatório, rebaixamento para fila de review ou escalonamento para revisão de perfil. Ele não muta Hermes Kanban diretamente; o reducer da fábrica consome a consequência e Hermes continua sendo a autoridade de estado em runtime.

## Termos centrais

Product SOT é a fonte de verdade do produto.

Full Product SOT Scope Coverage mostra que cada promessa importante do SOT está planejada, bloqueada, fora de escopo, delegada ao humano ou provada.

Method Contract liga rota, método, gates, workers e evidência.

Worker Packet é a tarefa limitada entregue a um worker.

Worker Result é o retorno estruturado do worker com evidência.

Gate Report explica se algo pode avançar, por que está bloqueado e o que destrava.

Receipt Five é o recibo de conclusão: pedido, mudança, evidência, revisão e próximo estado.

Human Gate é uma decisão material do operador com pacote legível.

Readback é a leitura real do artefato produzido.

No-idle é o guard contra parada silenciosa, não um segundo despachante.

Learnback é aprendizado promovido com prova, não memória solta de chat.

## Comandos úteis

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
python3 scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md
python3 scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python3 scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
python3 scripts/factoryctl.py build-worker-accountability-ledger .tmp/worker-accountability-events.json --out .tmp/worker-accountability-ledger.json
python3 scripts/factoryctl.py validate-worker-accountability-ledger .tmp/worker-accountability-ledger.json
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
```

## Fronteira das claims públicas

O repositório público prova coerência local do kernel. Ele não prova que um produto privado foi entregue. Entrega real precisa de Hermes vivo, estado de runtime, worker results atuais, evidência específica do produto, review consumido e aprovação humana quando o risco pedir.
