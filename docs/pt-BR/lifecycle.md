# Ciclo da fábrica

O workflow compilado é a fonte factual desta página. Hoje ele contém `26` fases em `docs/factory-workflow.catalog.json`.

Esta página não deve ser lida como uma cachoeira rígida. Ela é um mapa do que a fábrica protege. Hermes, dependências, bloqueios, risco e evidência ainda decidem o que pode andar numa execução viva.

A leitura prática é simples: cada fase responde uma pergunta, exige alguns artefatos, bloqueia atalhos perigosos e entrega ao operador uma visão mais clara do próximo passo.

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

## F0 — Pre-Start / Sealed Source Envelope

A fábrica separa conversa de execução. O material entra num envelope de fonte antes de virar card, para o primeiro resumo não destruir a intenção original.

O que precisa existir: `factory_bridge_source_envelope`, `factory_bridge_start_request`.

Gates que seguram o avanço: `Start Boundary`.

Workers normalmente envolvidos: `overkill-factory-gerente`, `factory-orchestrator`.

Atalhos que esta fase impede:

- summarize or reinterpret source material in the bridge.
- create Hermes board/card directly from bridge.
- start without explicit runtime target policy.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F1 — Intake

Aqui o pedido vira sinal classificado. A interface do operador, a conversa inicial e a resolução da fonte impedem que a fábrica comece com um chute bonito.

O que precisa existir: `operator_interface_profile`, `factory_start_conversation`, `universal_signal_intake`, `source_refs`, `source_resolution_packet`.

Gates que seguram o avanço: `Source Gate`.

Workers normalmente envolvidos: `factory-orchestrator`.

Atalhos que esta fase impede:

- route implementation before source resolution.
- create Product SOT from raw input.
- require the operator to poll for status.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F2 — Source Ledger

O source ledger diz de onde veio cada afirmação. Fato, inferência, decisão, conflito e lacuna não podem virar uma massa só.

O que precisa existir: `source_refs`, `product_source_ledger`, `operator_understanding_confirmation`.

Gates que seguram o avanço: `Source Gate`.

Workers normalmente envolvidos: `source-ledger-worker`.

Atalhos que esta fase impede:

- ask user to reconcile internal source bookkeeping.
- create outcome contract or Product SOT before understanding is confirmed.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F3 — Source Resolution

A fábrica transforma fonte em entendimento operacional. Se ainda falta descoberta, ela segura o avanço em vez de deixar o worker preencher buraco com imaginação.

O que precisa existir: `discovery_brief`.

Gates que seguram o avanço: `Discovery Gate`.

Workers normalmente envolvidos: `source-ledger-worker`, `product-sot-planner`.

Atalhos que esta fase impede:

- turn unresolved gaps into execution scope.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F4 — Product Outcome And Discovery

O resultado esperado, o usuário, o problema e as hipóteses ficam explícitos. O operador precisa conseguir corrigir a direção antes de virar plano.

O que precisa existir: `operator_understanding_confirmation`, `operator_briefing_package`, `outcome_contract`, `discovery_brief`.

Gates que seguram o avanço: `Outcome Gate`, `Discovery Gate`.

Workers normalmente envolvidos: `product-sot-planner`.

Atalhos que esta fase impede:

- treat outcome candidate as approved Product SOT.
- draft Product SOT before operator understanding confirmation.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F5 — Product SOT

O Product SOT vira a verdade do produto. Ele protege escopo, não-escopo, critérios de aceitação e cobertura completa antes de execução material.

O que precisa existir: `product_sot`, `operator_briefing_package`, `full_product_sot_scope_coverage`, `factory_phase_lock`.

Gates que seguram o avanço: `Product SOT Gate`.

Workers normalmente envolvidos: `product-sot-planner`.

Atalhos que esta fase impede:

- execute from paper instead of Product SOT.
- ask operator to approve Product SOT from a short chat summary only.
- start architecture, repo cleanup, human gate or worker packet while Product SOT owner package is missing.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F6 — Agentic Method Router

A rota escolhe o tipo de caminho: produto, bug, release, incidente, segurança, UX, analytics, integração ou agente. A fábrica para de tratar tudo como tarefa genérica.

O que precisa existir: `factory_phase_lock`, `method_contract`.

Gates que seguram o avanço: `Method Gate`.

Workers normalmente envolvidos: `factory-orchestrator`.

Atalhos que esta fase impede:

- ask user to choose internal method machinery.
- start architecture or repo cleanup before Method Contract.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F7 — Method Contract

O método registra como o trabalho será feito e provado. Não basta dizer TDD, security-first ou design-first; o contrato precisa mudar artefatos, gates e evidência.

O que precisa existir: `factory_phase_lock`, `method_contract`.

Gates que seguram o avanço: `Method Gate`.

Workers normalmente envolvidos: `factory-orchestrator`.

Atalhos que esta fase impede:

- start implementation with undocumented process choices.
- materialize future-phase cards while active frontier is still product_sot or method_contract.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F8 — Pack And Product Experience Selection

A fábrica confere se tem pacote de capacidade e prova de superfície para o tipo de produto. Web, CLI, docs, agente, Solana, mobile ou fintech não pedem a mesma prova.

O que precisa existir: `capability_pack_contract`, `product_experience_plan`, `product_face_packet`, `project_design_system`, `professional_design_process`, `surface_evidence_profile`, `product_delivery_quality_profile`.

Gates que seguram o avanço: `Pack Gate`, `Product Experience Gate`, `Surface Pack Gate`.

Workers normalmente envolvidos: `product-face`, `factory-orchestrator`.

Atalhos que esta fase impede:

- activate a pack without proof or coverage.
- start product-facing implementation before surface state coverage.
- treat generic UI proof as Product Experience proof.
- move to implementation with unnamed surface pack or proof profile.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F9 — Risk And Authority Gates

Autoridade, acesso, orçamento e risco entram antes da execução sensível. Se a decisão pertence ao operador, a fábrica prepara pacote de decisão; se é reparo interno, não joga no humano.

O que precisa existir: `access_capability`, `budget_contract`.

Gates que seguram o avanço: `Access Gate`, `Budget Gate`, `Human Gate when required`.

Workers normalmente envolvidos: `human-gate-clerk`.

Atalhos que esta fase impede:

- infer approval from silence.
- ask for planning-only continuation approval.
- ask for architecture or repo cleanup approval while downstream is frozen.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F10 — Security Architecture

Segurança entra como arquitetura, não como scan no fim. Trust boundary, segredo, chave, supply chain, privacidade, onchain e rollback precisam aparecer cedo quando importam.

O que precisa existir: `factory_phase_lock`, `security_architecture_plan`.

Gates que seguram o avanço: `Security Architecture Gate`.

Workers normalmente envolvidos: `security-orchestrator`.

Atalhos que esta fase impede:

- build material risk before architecture.
- start security architecture while Product SOT or Method Contract is still missing.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F11 — Executable Plans

A arquitetura e os riscos viram plano de desenvolvimento. O objetivo é sair da ideia para unidades executáveis sem perder dependências e critérios de parada.

O que precisa existir: `software_development_plan`, `spec_graph`, `loop_plan`, `product_creation_plan`.

Gates que seguram o avanço: `Ready Gate`.

Workers normalmente envolvidos: `decomposition-planner`.

Atalhos que esta fase impede:

- execute before plans, coverage review and stop criteria exist.
- mark decomposition review as passed from the planner that created the decomposition.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F12 — Autonomy Readiness

O produto é quebrado em work units. Cada pedaço precisa de dono, reviewer, prova, dependência e regra de pronto; do contrário vira fila de agente solta.

O que precisa existir: `decomposition_coverage_review`, `product_implementation_readiness`, `autonomy_readiness_packet`.

Gates que seguram o avanço: `Decomposition Coverage Gate`, `Access & Capability Gate`.

Workers normalmente envolvidos: `independent-reviewer`, `factory-orchestrator`.

Atalhos que esta fase impede:

- start autonomous work with missing review, access or limits.
- let a single reviewer approve the complete decomposition alone.
- create Product Implementation Readiness from a failed or missing decomposition coverage review.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F13 — Ready Gate

Antes de rodar, a fábrica checa prontidão de implementação: SOT, método, research, arquitetura, packs, acesso, workers e provas necessárias.

O que precisa existir: `gate_report`.

Gates que seguram o avanço: `Ready Gate`.

Workers normalmente envolvidos: `factory-orchestrator`.

Atalhos que esta fase impede:

- dispatch blocked workers.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F15 — Runtime Execution

Workers executam escopos pequenos e devolvem resultado estruturado. O resultado precisa trazer evidência, limite de autoridade e próximo estado.

O que precisa existir: `worker_packets`.

Gates que seguram o avanço: `Runtime Gate`.

Workers normalmente envolvidos: `implementation-worker`, `qa-verification-worker`.

Atalhos que esta fase impede:

- spawn without route readiness.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F16 — Worker Results

A fábrica roda verificação objetiva: testes, scans, screenshots, jornadas, logs, contratos ou provas remotas, conforme o tipo de trabalho.

O que precisa existir: `worker_results`.

Gates que seguram o avanço: `Done Gate`.

Workers normalmente envolvidos: `evidence-reconciler`.

Atalhos que esta fase impede:

- treat packet existence as proof.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F17 — Verification

Revisão independente consome o artefato real. Pass sem leitura, reviewer igual executor ou achado sem reparo são progresso falso.

O que precisa existir: `verification_plan`, `verification_result`.

Gates que seguram o avanço: `Verification Gate`.

Workers normalmente envolvidos: `qa-verification-worker`.

Atalhos que esta fase impede:

- claim done without command evidence.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F18 — Independent Review

Receipt Five reconcilia pedido, mudança, evidência, revisão e pendências. É a passagem entre “mexeu” e “provou”.

O que precisa existir: `review_result`.

Gates que seguram o avanço: `Review Gate`.

Workers normalmente envolvidos: `independent-reviewer`.

Atalhos que esta fase impede:

- allow executor to self-approve.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F20 — Closure Summary

Handoff guarda estado reproduzível para pausa, troca de operador ou retomada. Não é aprovação; é transferência honesta de contexto e evidência.

O que precisa existir: `closure_summary`.

Gates que seguram o avanço: `Closure Gate`.

Workers normalmente envolvidos: `handoff-packer`.

Atalhos que esta fase impede:

- hide unresolved blockers in prose.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F21 — Receipt Five

A auditoria de conclusão compara obrigações com provas entregues. Ela fecha quando bate e bloqueia quando falta algo.

O que precisa existir: `receipt_five`.

Gates que seguram o avanço: `Done Gate`.

Workers normalmente envolvidos: `evidence-reconciler`.

Atalhos que esta fase impede:

- mark done without Receipt Five.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F22 — Completion Audit

Operações de produção verificam dono, ambiente, monitoramento, rollback, incidentes e canal de release. Produto vivo precisa chão operacional.

O que precisa existir: `completion_audit`.

Gates que seguram o avanço: `Completion Audit`.

Workers normalmente envolvidos: `evidence-reconciler`.

Atalhos que esta fase impede:

- close skipped method or evidence requirements.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F23 — Production Operations

Release só acontece com promoção, evidência e autoridade. Se a prova não sustenta, a decisão correta é bloquear.

O que precisa existir: `production_readiness_plan`.

Gates que seguram o avanço: `Release Gate`.

Workers normalmente envolvidos: `release-ops-worker`.

Atalhos que esta fase impede:

- release without owner, rollback or approval.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F24 — Release Or Block

Depois da entrega, monitoramento e suporte mantêm o produto observável. Incidente não vira improviso; vira rota.

O que precisa existir: `release_decision`.

Gates que seguram o avanço: `Release Gate`, `Human Gate when required`.

Workers normalmente envolvidos: `release-ops-worker`, `human-gate-clerk`.

Atalhos que esta fase impede:

- promote without production-strict evidence.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F25 — Monitoring Support

Learnback transforma falhas repetidas em docs, testes, skills, gates ou issues. A fábrica aprende, mas não se altera em silêncio.

O que precisa existir: `incident_support_plan`.

Gates que seguram o avanço: `Support Gate`.

Workers normalmente envolvidos: `release-ops-worker`.

Atalhos que esta fase impede:

- ship without support owner when support is material.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F26 — Learnback

A auditoria de maturidade pergunta se o método escolhido foi bom o bastante. É a defesa contra uma fábrica que segue processo e mesmo assim escolhe processo fraco.

O que precisa existir: `factory_learning_proposal`.

Gates que seguram o avanço: `Learning Gate`.

Workers normalmente envolvidos: `skill-eval-distiller`.

Atalhos que esta fase impede:

- auto-activate critical factory changes.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.

## F27 — Factory Maturity Audit

A auditoria final olha a própria fábrica: cobertura, gaps, confiabilidade, operadores, workers e regras que precisam evoluir.

O que precisa existir: `factory_maturity_scorecard`.

Gates que seguram o avanço: `Maturity Gate`.

Workers normalmente envolvidos: `skill-eval-distiller`.

Atalhos que esta fase impede:

- commit raw study or private evidence.

O operador não deveria precisar ler o JSON dessa fase para entender a situação. A projeção humana precisa dizer o que já está claro, o que falta, quem é dono do próximo passo e qual prova destrava o avanço.
