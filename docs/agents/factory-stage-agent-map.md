# Factory Stage Agent Map

This map connects the canonical factory journey to the actual public workers.
It prevents two common failures:

- treating a conceptual role as if it were an executable worker;
- leaving a stage with no named owner, proof, or blocker.

Hermes remains the runtime source of truth. Discord, when configured, is only
the operator cockpit.

## Reading Rule

- Primary worker: owns the stage outcome.
- Support workers: enter only when the card surface, risk, or method contract
  requires them.
- Proof: the minimum evidence that must exist before the next stage can trust
  the result.
- Blocker: the condition that must stop the line.

## Stage Map

| Stage | Primary worker | Support workers | What they own | Proof | Blocker |
| --- | --- | --- | --- | --- | --- |
| 1. Intake | `factory-orchestrator` | `source-ledger-worker`, `memory-steward`, `control-tower-projection-worker` | Classify request type, phase, risk surface and first route. | Intake classification, source refs, initial risk. | Request cannot be classified or source is missing. |
| 2. Source Ledger | `source-ledger-worker` | `memory-steward`, `public-safety-gate` | Register sources and separate source material from memory or chat claims. | Source map, freshness/trust notes. | Critical claim has no source ref. |
| 3. Source Resolution | `source-ledger-worker` | `product-sot-planner`, `memory-steward` | Mark facts, inference, decision, conflict, stale material and gaps. | Promoted/rejected claims and conflict list. | Stale or conflicting source is promoted as fact. |
| 4. Product Outcome & Discovery | `product-sot-planner` | `source-ledger-worker`, `product-face`, `detection-monitoring-worker` | Define expected outcome, user, problem, success metric, risk metric and assumptions. | Outcome contract, discovery notes, assumption ledger. | Product moves forward without outcome or critical assumption handling. |
| 5. Product SOT | `product-sot-planner` | `product-architect`, `human-gate-clerk`, `docs-os-worker` | Produce the product or slice source of truth candidate. | SOT candidate with scope in/out, acceptance and open decisions. | SOT candidate is treated as approval. |
| 6. Agentic Method Router | `factory-orchestrator` | `product-architect`, `security-orchestrator`, `skill-eval-distiller` | Choose method weight, required artifacts, workers, gates and reviews. | Method route and rationale. | Execution starts from habit instead of method. |
| 7. Method Contract | `factory-orchestrator` | `decomposition-planner`, `independent-reviewer`, `human-gate-clerk` | Record selected methods, skipped methods, authority limits and done criteria. | Method contract status and skipped-method rationale. | Method is skipped without reason. |
| 8. Product Pack & Surface Pack | `factory-orchestrator` | `product-face`, `security-orchestrator`, `agent-runtime-builder` | Select product/surface capability coverage and block unsupported product types. | Capability pack contract and coverage report. | Product type lacks ready pack or activated specialist pack. |
| 9. Risk, Authority, Dependencies, Access, Budget | `factory-orchestrator` | `human-gate-clerk`, `supply-chain-gate`, `cloud-infra-security-specialist`, `crypto-key-management-specialist`, `public-safety-gate` | Decide what can be planned, executed, tested, released and operated. | Readiness blockers, access capability, budget/dependency refs. | Material execution starts without required access or authority. |
| 10. Security Architecture Plan | `security-orchestrator` | `product-architect`, `appsec-owasp-specialist`, `agentic-ai-security-specialist`, `cloud-infra-security-specialist`, `crypto-key-management-specialist`, `solana-quasar-auditor` | Define trust boundaries, controls, specialist owners and required security gates. | Security Architecture Plan and specialist routing rationale. | Security is postponed as a final scan. |
| 11. Software Development Plan | `decomposition-planner` | `product-architect`, `docs-os-worker`, builders by surface | Convert SOT and architecture into buildable contracts. | PRD/TRD/story/card plan when required. | Worker cards are created without buildable context. |
| 12. Product Experience Plan | `product-face` | `frontend-builder`, `docs-os-worker`, `qa-verification-worker`, `wallet-transaction-builder` | Define surface behavior, states, journeys, accessibility and proof per product surface. | Product Face packet and proof needs. | Interface work begins without surface state coverage. |
| 13. Data, Metrics & Analytics Plan | `detection-monitoring-worker` | `data-persistence-builder`, `backend-api-builder`, `product-sot-planner`, `public-safety-gate` | Define success metrics, risk metrics, events, dashboards, visibility and privacy limits. | Data metrics plan, event contract, dashboard/health proof. | Product success is claimed without measurable signal. |
| 14. Agent Quality & Evals Plan | `skill-eval-distiller` | `agent-runtime-builder`, `agentic-ai-security-specialist`, `test-automation-builder`, `independent-reviewer` | Define evals for agents, skills, prompts, models and authority behavior. | Agent eval plan, held-out cases, authority/evidence tests. | Important agent/prompt/skill is trusted without eval or waiver. |
| 15. Spec Graph | `decomposition-planner` | `docs-os-worker`, `factory-orchestrator`, `product-architect` | Connect requirements, risks, dependencies, gates, workers and evidence. | Spec Graph with gate and worker mapping. | Requirements become disconnected tasks. |
| 16. Loop Plan | `decomposition-planner` | `test-automation-builder`, `remote-proof-runner`, `independent-reviewer`, `handoff-packer` | Define lanes, order, timeouts, evidence, stop criteria and isolation. | Loop Plan, work-unit contracts, reviewer selection. | Parallel work starts without lane/worktree boundaries. |
| 17. Autonomy Readiness Packet | `factory-orchestrator` | `infra-devops-builder`, `human-gate-clerk`, `supply-chain-gate`, `cloud-infra-security-specialist`, `release-ops-worker` | List required repo, cloud, billing, APIs, secrets refs, runtime, owners and approvals. | Autonomy readiness packet. | Material execution requires access that is not granted. |
| 18. Ready Gate | `factory-orchestrator` | `supply-chain-gate`, `security-orchestrator`, `human-gate-clerk`, `public-safety-gate` | Decide if the line is allowed to start execution. | Ready gate verdict and blocked reason list. | Any required artifact, access, gate or worker is missing. |
| 19. Control Tower Projection | `control-tower-projection-worker` | `discord-control-tower-bridge`, `factory-orchestrator`, `human-gate-clerk` | Show phase, blockers, next steps, approvals and evidence in simple operator language. | Project Projection with source state and staleness note. | Cockpit hides blocked work or becomes source of truth. |
| 20. Execution | surface builder selected by `factory-orchestrator` | `implementation-worker`, `frontend-builder`, `backend-api-builder`, `data-persistence-builder`, `solana-quasar-builder`, `wallet-transaction-builder`, `integration-builder`, `infra-devops-builder`, `agent-runtime-builder` | Build the scoped work only inside worker authority. | Diffs, command output, artifacts and bounded handoff. | Generic builder replaces a more specific specialist. |
| 21. Worker Result | each assigned worker | `evidence-reconciler`, `handoff-packer` | Return PASS/FAIL/WAIVED/PENDING/BLOCKED with evidence. | Worker result artifact matching the receipt field. | Result has no evidence or mismatched receipt field. |
| 22. Verification | `qa-verification-worker` | `test-automation-builder`, `remote-proof-runner`, `product-face`, security workers by surface | Prove behavior with tests, screenshots, scans, logs, evals or release smoke. | QA result and mode coverage matrix. | Done is claimed from implementation output alone. |
| 23. Review | `independent-reviewer` | `autoreview-gate`, `codex-security`, security specialists by risk | Review executor output independently. | Review report, findings, residual risk. | Executor reviews its own work. |
| 24. Human Gate | `human-gate-clerk` | `factory-orchestrator`, `release-ops-worker`, `security-orchestrator` | Prepare and record real human decisions with scope and actor role. | Durable decision record. | Approval is inferred from chat or missing scope. |
| 25. Closure Summary | `evidence-reconciler` | `handoff-packer`, `docs-os-worker`, `factory-orchestrator` | Summarize request, delivery, proof, risks, waivers and next step. | Closure summary tied to current evidence. | Summary invents or omits required proof. |
| 26. Receipt Five | `evidence-reconciler` | `qa-verification-worker`, `independent-reviewer`, `human-gate-clerk` | Answer what changed, where, how verified, who reviewed and next step. | Receipt Five readiness verdict. | Current worker result, review, proof or approval is missing. |
| 27. Completion Audit | `evidence-reconciler` | `factory-orchestrator`, `independent-reviewer`, `public-safety-gate` | Compare required vs delivered and detect skipped methods/gates. | Completion audit verdict. | Required method, gate or evidence was skipped without recorded reason. |
| 28. Production Operations | `release-ops-worker` | `infra-devops-builder`, `detection-monitoring-worker`, `cloud-infra-security-specialist`, `supply-chain-gate` | Prepare live ownership, health checks, rollback, support and deploy evidence. | Production operations packet and smoke. | Product is treated as live without owner or rollback path. |
| 29. Release or Block | `release-ops-worker` | `human-gate-clerk`, `public-safety-gate`, `detection-monitoring-worker`, `factory-orchestrator` | Decide released, release candidate, done, blocked, superseded or archived. | Release decision with evidence and rollback refs. | Release decision lacks authority or monitoring evidence. |
| 30. Monitoring, Incident & Support | `detection-monitoring-worker` | `release-ops-worker`, `infra-devops-builder`, `memory-steward`, `skill-eval-distiller` | Track health, alerts, incidents, rollback, postmortem and support path. | Monitoring evidence, incident runbook, owner path. | Failure has no signal, owner or response path. |
| 31. Learnback | `skill-eval-distiller` | `memory-steward`, `docs-os-worker`, `test-automation-builder`, `agent-runtime-builder` | Turn repeated learning into test, eval, skill, policy, template, doc, gate, worker or pack update. | Learnback record and before/after evidence. | Learning remains only in chat memory. |
| 32. Factory Maturity Audit | `skill-eval-distiller` | `independent-reviewer`, `factory-orchestrator`, `security-orchestrator`, `product-face` | Attack the factory for blind spots, weak agents, weak packs and missing proof. | Factory maturity scorecard and missing coverage register. | Factory is strong in one area and blind in another. |

## Conceptual Roles To Real Workers

The canonical document may use simple role names. In the public runtime, those
roles are implemented by these registered workers:

| Conceptual role | Real worker |
| --- | --- |
| Method Router | `factory-orchestrator` |
| Product Outcome & Discovery Worker | `product-sot-planner` |
| Product Experience Router / Worker | `product-face` |
| Security Architect Worker | `security-orchestrator` plus the routed security specialist |
| Data/Metrics Worker | `detection-monitoring-worker` with `data-persistence-builder` or `backend-api-builder` when implementation is needed |
| Agent Eval Worker | `skill-eval-distiller` |
| Dependency/Integration Worker | `integration-builder` plus `supply-chain-gate` when dependency risk exists |
| Access/Capability Worker | `factory-orchestrator` plus `human-gate-clerk` for real authority |
| Privacy/Compliance Worker | `security-orchestrator` routes the right specialist or blocks until a pack exists |
| Release Channel Worker / Production Readiness Worker | `release-ops-worker` |
| Incident Triage Worker | `detection-monitoring-worker` |
| Support/Handoff Worker | `handoff-packer` |
| Factory Concierge | operator interface role; not a builder worker |
| Approval Inbox Clerk | `human-gate-clerk` |
| Bot Health Monitor | `discord-control-tower-bridge` and bridge-health validation |
| Factory Maturity Auditor | `skill-eval-distiller` with `independent-reviewer` for adversarial review |

## Promotion Rule

A new executable worker is created only when all of this is true:

- the existing worker map cannot own the stage cleanly;
- the work repeats across projects;
- input, output, authority and evidence are clear;
- permission class and Hermes binding can be created;
- eval or smoke proof exists before production use.

Until then, the right move is usually to strengthen the current worker contract
or activate a capability pack instead of adding a new loose agent.
