# Factory Flow Concepts

Overkill Factory is a gated production line. It is designed to prevent agents
from jumping straight from a vague request to a confident completion claim.

## Core Objects

| Object | Meaning |
| --- | --- |
| Product paper | The short project brief or source material that starts the line. |
| Source resolution | The step that separates source facts, inference, decisions, conflicts and gaps. |
| Product SOT | The source-of-truth candidate for the complete product scope, non-goals and acceptance criteria. |
| Full Product SOT scope coverage | The map that prevents a first slice from silently becoming the whole product. |
| Specialist research decision | A public-safe research result that changes SOT, architecture, method, gate, worker, proof or blocker state. |
| Product Creation Plan | The complete product decomposition into safe execution slices, proof and stop rules. |
| Product Implementation Readiness | The gate that checks SOT, method, research, architecture, work units, packs, access and proof before material execution. |
| Factory card | The machine-checkable work contract consumed by Hermes and `factoryctl.py`. |
| Worker packet | The task-specific assignment generated for one worker role. |
| Worker result | The evidence-bearing result produced after a worker actually runs. |
| Receipt Five | The closure metadata that says what changed, where evidence lives, which commands ran, review state and next action. |
| Human gate | A real human decision record for architecture, high-risk work or release promotion. |

## The Happy Path

```text
source intake
-> source resolution
-> Product SOT
-> full Product SOT scope coverage
-> specialist research decisions when needed
-> architecture and risk routing
-> method contract
-> Product Creation Plan
-> Product Implementation Readiness
-> Product Face or surface-specific plan
-> security, access and budget gates
-> decomposition into Hermes cards
-> specialist worker execution
-> QA, review and evidence reconciliation
-> human gate when required
-> Receipt Five
-> release readiness
-> learnback
```

Not every project uses every worker. The card surfaces, risk class and done
definition decide which workers are required.

## What Blocks A Card

A card should stay blocked when:

- source facts and inference are mixed;
- Product SOT or architecture is only a candidate but treated as approval;
- a first slice exists but the full Product SOT scope coverage is missing;
- research is required but no specialist research plan exists;
- Product Creation Plan or Product Implementation Readiness is missing for complete-product work;
- production or mainnet intent lacks a promotion ladder with environment-specific proof;
- a required worker packet exists but the worker result does not;
- Product Face, security, Auditor, QA or review evidence is missing;
- executor and reviewer are the same identity;
- a human gate is required but no real decision record exists;
- Receipt Five cannot point to current evidence;
- public artifacts contain secrets or private operational residue.

## Source Of Truth

Hermes Kanban state plus repo-relative evidence and receipts are the source of
truth. Chat, Discord messages and status summaries are useful operator views,
but they do not close work by themselves.

## Risk Levels

Use risk to decide how much proof and authority is required:

| Risk | Typical meaning |
| --- | --- |
| R0 | Documentation or local-only inspection with no sensitive action. |
| R1 | Low-risk local validation or small planning change. |
| R2 | Product-facing, code-facing or review-relevant work. |
| R3 | Security, wallet, onchain, infra or high-impact user behavior. |
| R4 | Release, production, irreversible action or major authority boundary. |

R3 and R4 work require stronger specialist evidence and human gates. Agents can
prepare the packet, but they cannot invent approval.

## Why This Shape Exists

Autonomous agents are good at doing scoped work. They are weak when the task
mixes source, judgment, implementation, review and approval into one prompt.
The factory separates those responsibilities so each claim can be checked.
