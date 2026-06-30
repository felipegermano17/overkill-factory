# Ciclo da fábrica

O workflow compilado é a fonte factual desta página. Hoje ele contém `26` fases compiladas em `docs/factory-workflow.catalog.json`.

Você pode regenerar ou inspecionar o plano pelo lado da implementação:

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

Leia o ciclo como um caminho de produção, não como uma cachoeira rígida. Estado vivo no Hermes, dependências, bloqueios, risco e evidência decidem o que pode andar. A lista de fases mostra o que a fábrica está protegendo em cada passo.

### F0 — Pre-Start / Sealed Source Envelope

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Pre-Start / Sealed Source Envelope`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `factory_bridge_source_envelope`, `factory_bridge_start_request`. O portão que segura a passagem é: Start Boundary. Os workers normalmente envolvidos são: `overkill-factory-gerente`, `factory-orchestrator`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F1 — Intake

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Intake`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `operator_interface_profile`, `factory_start_conversation`, `universal_signal_intake`, `source_refs`, `source_resolution_packet`. O portão que segura a passagem é: Source Gate. Os workers normalmente envolvidos são: `factory-orchestrator`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F2 — Source Ledger

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Source Ledger`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `source_refs`, `product_source_ledger`, `operator_understanding_confirmation`. O portão que segura a passagem é: Source Gate. Os workers normalmente envolvidos são: `source-ledger-worker`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F3 — Source Resolution

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Source Resolution`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `discovery_brief`. O portão que segura a passagem é: Discovery Gate. Os workers normalmente envolvidos são: `source-ledger-worker`, `product-sot-planner`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F4 — Product Outcome And Discovery

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Product Outcome And Discovery`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `operator_understanding_confirmation`, `operator_briefing_package`, `outcome_contract`, `discovery_brief`. O portão que segura a passagem é: Outcome Gate, Discovery Gate. Os workers normalmente envolvidos são: `product-sot-planner`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F5 — Product SOT

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Product SOT`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `product_sot`, `operator_briefing_package`, `full_product_sot_scope_coverage`, `factory_phase_lock`. O portão que segura a passagem é: Product SOT Gate. Os workers normalmente envolvidos são: `product-sot-planner`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F6 — Agentic Method Router

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Agentic Method Router`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `factory_phase_lock`, `method_contract`. O portão que segura a passagem é: Method Gate. Os workers normalmente envolvidos são: `factory-orchestrator`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F7 — Method Contract

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Method Contract`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `factory_phase_lock`, `method_contract`. O portão que segura a passagem é: Method Gate. Os workers normalmente envolvidos são: `factory-orchestrator`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F8 — Pack And Product Experience Selection

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Pack And Product Experience Selection`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `capability_pack_contract`, `product_experience_plan`, `product_face_packet`, `project_design_system`, `professional_design_process`, `surface_evidence_profile`, `product_delivery_quality_profile`. O portão que segura a passagem é: Pack Gate, Product Experience Gate, Surface Pack Gate. Os workers normalmente envolvidos são: `product-face`, `factory-orchestrator`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F9 — Risk And Authority Gates

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Risk And Authority Gates`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `access_capability`, `budget_contract`. O portão que segura a passagem é: Access Gate, Budget Gate, Human Gate when required. Os workers normalmente envolvidos são: `human-gate-clerk`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F10 — Security Architecture

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Security Architecture`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `factory_phase_lock`, `security_architecture_plan`. O portão que segura a passagem é: Security Architecture Gate. Os workers normalmente envolvidos são: `security-orchestrator`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F11 — Executable Plans

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Executable Plans`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `software_development_plan`, `spec_graph`, `loop_plan`, `product_creation_plan`. O portão que segura a passagem é: Ready Gate. Os workers normalmente envolvidos são: `decomposition-planner`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F12 — Autonomy Readiness

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Autonomy Readiness`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `decomposition_coverage_review`, `product_implementation_readiness`, `autonomy_readiness_packet`. O portão que segura a passagem é: Decomposition Coverage Gate, Access & Capability Gate. Os workers normalmente envolvidos são: `independent-reviewer`, `factory-orchestrator`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F13 — Ready Gate

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Ready Gate`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `gate_report`. O portão que segura a passagem é: Ready Gate. Os workers normalmente envolvidos são: `factory-orchestrator`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F15 — Runtime Execution

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Runtime Execution`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `worker_packets`. O portão que segura a passagem é: Runtime Gate. Os workers normalmente envolvidos são: `implementation-worker`, `qa-verification-worker`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F16 — Worker Results

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Worker Results`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `worker_results`. O portão que segura a passagem é: Done Gate. Os workers normalmente envolvidos são: `evidence-reconciler`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F17 — Verification

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Verification`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `verification_plan`, `verification_result`. O portão que segura a passagem é: Verification Gate. Os workers normalmente envolvidos são: `qa-verification-worker`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F18 — Independent Review

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Independent Review`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `review_result`. O portão que segura a passagem é: Review Gate. Os workers normalmente envolvidos são: `independent-reviewer`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F20 — Closure Summary

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Closure Summary`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `closure_summary`. O portão que segura a passagem é: Closure Gate. Os workers normalmente envolvidos são: `handoff-packer`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F21 — Receipt Five

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Receipt Five`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `receipt_five`. O portão que segura a passagem é: Done Gate. Os workers normalmente envolvidos são: `evidence-reconciler`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F22 — Completion Audit

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Completion Audit`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `completion_audit`. O portão que segura a passagem é: Completion Audit. Os workers normalmente envolvidos são: `evidence-reconciler`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F23 — Production Operations

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Production Operations`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `production_readiness_plan`. O portão que segura a passagem é: Release Gate. Os workers normalmente envolvidos são: `release-ops-worker`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F24 — Release Or Block

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Release Or Block`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `release_decision`. O portão que segura a passagem é: Release Gate, Human Gate when required. Os workers normalmente envolvidos são: `release-ops-worker`, `human-gate-clerk`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F25 — Monitoring Support

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Monitoring Support`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `incident_support_plan`. O portão que segura a passagem é: Support Gate. Os workers normalmente envolvidos são: `release-ops-worker`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F26 — Learnback

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Learnback`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `factory_learning_proposal`. O portão que segura a passagem é: Learning Gate. Os workers normalmente envolvidos são: `skill-eval-distiller`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.

### F27 — Factory Maturity Audit

Nesta fase, a fábrica tenta responder uma pergunta simples: "já temos base suficiente para avançar sem inventar?" O nome interno é `Factory Maturity Audit`, mas o papel prático é proteger o próximo passo. Se a fase pula evidência, todo o resto fica bonito no papel e fraco na execução.

O que precisa existir antes de avançar: `factory_maturity_scorecard`. O portão que segura a passagem é: Maturity Gate. Os workers normalmente envolvidos são: `skill-eval-distiller`.

O erro comum aqui é acelerar demais. A fábrica bloqueia atalhos como: none listed. Isso não é burocracia. É a diferença entre trabalho autônomo e teatro autônomo.

O operador não deveria precisar entender cada campo JSON desta fase. Ele deveria enxergar o estado em linguagem clara: o que já foi entendido, o que ainda falta, quem é dono do próximo passo e qual evidência vai destravar a fase. Se a resposta for "não sabemos", a fábrica deve dizer isso cedo, abrir o bloqueio certo e propor o menor próximo passo seguro.
