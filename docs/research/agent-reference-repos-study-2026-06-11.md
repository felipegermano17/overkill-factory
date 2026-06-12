# Agent Reference Repositories Study

> Document status: HISTORICAL EVIDENCE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This is not the current factory rule; implemented decisions must appear in current registries, schemas, tests or gates.

Date: 2026-06-11

Purpose: study external agent/skill repositories, compare their agent and skill
patterns against the existing Overkill Factory agent layer and product-type
coverage, then execute the useful changes. This is not a plan to copy another
project's SOULs, prompts or private assumptions.

## Sources Checked

| Repository | Commit checked | What was studied |
|---|---:|---|
| `VirtusLab/orca` | `43c266e4ec4e687838dfcae0bbdcad478dfc9a6b` | programmatic workflow, persistent plan, task loop, reviewer selection |
| `garrytan/gstack` | `a5833c4d37c84b89670d2993bc9c79436f5d598d` | skill routing, review army, plan review pipeline, QA/review/shipping skills |
| `SynkraAI/aiox-core` | `77265d53966193958c0d370475bc2df041760d99` | agent role map, UX/QA/PM/DevOps agents, quality gates and workflow mapping |
| `mattpocock/skills` | `694fa30311e02c2639942308513555e61ee84a6f` | small composable skills, alignment, shared language, feedback loops |
| `solanabr/solana-claude` | `d653daceb005fc7568bfe0f33e4195afbfb2f7c1` | Solana domain packs, agent teams, progressive skill loading |
| `LerianStudio/ring` | `80d56e8c049707df0f90948e4b1b54a0212cb33a` | specialist reviewers, review slicing, docs writers, QA modes, production readiness |

## Agent/Skill Comparison Matrix

| Area observed in references | Reference source | Existing Overkill agent/skill | Concrete gap found | Executed decision |
|---|---|---|---|---|
| Reviewer selector and review slicing | `orca` reviewer selector; `ring/default/agents/review-slicer.md` | `independent-reviewer`, `autoreview-gate`, `security-orchestrator` | Review identity existed, but reviewer selection was too implicit. | Added `reviewer-selection-plan` schema/template and required it in `independent-reviewer`. |
| Work-unit compiler | `orca` persistent plan/workflow; GStack plan review | `decomposition-planner`, `software-development-plan`, `loop-plan` | Work units were named but not contract-shaped enough for resume, rollback and review. | Added `work-unit-contract` schema/template; strengthened software and loop plan schemas; required them in `decomposition-planner`. |
| Agent/skill eval and promotion | GStack review/ship flows; `mattpocock/skills`; Ring writing-skills | `skill-eval-distiller`, `agent-runtime-builder` | Promotion rules existed, but eval result/promotion evidence was not explicit enough. | Strengthened `agent-eval-plan`; added `agent-eval-result`; required eval plan for agent runtime and skill promotion. |
| UI/UX/product quality | AIOX UX expert; Ring product designer and frontend QA | `product-face`, `frontend-builder` | Product Face covered screenshots/states, but not enough journey/game-like/desktop coverage. | Patched `product-face` profile to require journey coverage across app, desktop and game-like surfaces. |
| QA modes | AIOX QA and quality gates; Ring QA modes; GStack QA | `qa-verification-worker`, `test-automation-builder` | QA was evidence-focused but did not name mode taxonomy. | Added QA mode contract and patched `qa-verification-worker` to require mode coverage. |
| Docs/API writers | Ring API writer/docs reviewer/guide writer | `docs-os-worker`, `backend-api-builder` | Docs OS was broad and did not route doc shape explicitly. | Patched `docs-os-worker` to route API docs, operator guides and onboarding separately. |
| Production readiness and observability | Ring production-readiness and observability skills | `release-ops-worker`, `detection-monitoring-worker`, `infra-devops-builder` | Existing workers cover release and monitoring; no new worker needed before pilot. | Kept existing agents; current production-readiness schemas/tests remain the enforcement path. |
| Security, prompt and agentic review | GStack security review; Ring prompt/security reviewers | `agentic-ai-security-specialist`, `security-orchestrator`, `codex-security` | Core coverage exists; prompt/tool/memory risk should stay in specialist contracts. | Kept existing agents; agent runtime now requires eval plan and security handoff before promotion. |
| Solana domain packs | `solana-claude` agents/skills/commands | `solana-quasar-builder`, `solana-quasar-qa-engineer`, `solana-quasar-auditor` | Solana reference is useful, but Anchor/Pinocchio should not become Factory default. | Rejected new Anchor/Pinocchio workers for core; keep Quasar-first workers and domain-pack backlog. |
| Human review focus | AIOX human-review tests and gates | `human-gate-clerk`, `independent-reviewer` | Human gate exists, but reviewer selection should focus the human on uncovered surfaces. | Reviewer-selection plan now becomes the carrier for human-review focus. |
| Product-type specialist packs | Ring specialist teams; Solana Claude domain teams; GStack iOS/design/QA skills; AIOX UX/QA/Data/DevOps agents | Existing builders plus security, QA, Product Face and release workers | Horizontal factory coverage was not enough to prove coverage for every product type. Native mobile, desktop, game, AI/ML, fintech, regulated, analytics, browser extension and hardware products need explicit capability decisions before execution. | Added a capability pack registry, capability pack contract, card validation gate and tests. Core packs can execute; template packs block until activated. |

## Executed Changes

Implemented in this repository:

- Added `schemas/work-unit-contract.schema.json`.
- Added `templates/work-unit-contract.json`.
- Added `schemas/reviewer-selection-plan.schema.json`.
- Added `templates/reviewer-selection-plan.json`.
- Strengthened `schemas/software-development-plan.schema.json` with work-unit
  contracts and reviewer-selection plan.
- Strengthened `schemas/loop-plan.schema.json` with work-unit and reviewer
  selection refs.
- Strengthened `schemas/agent-eval-plan.schema.json` with target agent,
  negative cases, over-authority cases, blocked cases, reviewer separation and
  promotion decision.
- Added `schemas/agent-eval-result.schema.json`.
- Added `templates/agent-eval-result.json`.
- Added `schemas/qa-verification-plan.schema.json`.
- Added `templates/qa-verification-plan.json`.
- Patched `decomposition-planner` to require `loop_plan` and
  `software_development_plan`, and to deliver work-unit contracts plus reviewer
  selection.
- Patched `independent-reviewer` to require `reviewer_selection_plan`.
- Patched `skill-eval-distiller` to require `agent_eval_plan` before promoting
  skills, agents or domain packs.
- Patched `agent-runtime-builder` to require `agent_eval_plan` before profile,
  adapter or skill-runtime promotion.
- Patched `product-face` to include journey, desktop and game-like product
  experience coverage.
- Patched `qa-verification-worker` to include QA mode coverage.
- Patched `docs-os-worker` to route API, guide, onboarding and operator docs by
  shape instead of treating documentation as one generic artifact.
- Patched validation cards with reviewer-selection plans where independent
  review is required.
- Added `agents/capability-packs.public.json` to describe which product
  categories are ready now and which ones require a specialist pack before
  execution.
- Added `schemas/capability-pack-registry.schema.json` and
  `schemas/capability-pack-contract.schema.json`.
- Added `templates/capability-pack-contract.json`.
- Patched `scripts/factoryctl.py` so a card with
  `capability_coverage_required=true` blocks when a surface is not covered by a
  ready pack or an activated pack contract.
- Patched factory card templates to carry capability coverage by default.
- Added `tests/test_agent_reference_study_execution.py`.
- Added `tests/test_capability_packs.py`.

## Capability Coverage Decision

The corrected decision is not "the current agents can build absolutely any
product." That would be false.

The decision is:

```text
paper surface -> capability pack coverage -> ready pack or activated pack
-> worker packets -> execution
```

If a paper asks for a product type outside ready coverage, the Factory must
block before material execution and create or activate the right pack.

Ready now:

- `web-saas-core`: ordinary web apps, SaaS, APIs, persistence, auth,
  integration, tests, docs, release and monitoring.
- `cloud-native-core`: CI/CD, runtime, cloud wiring, observability, rollback
  and production readiness boundaries.
- `agent-runtime-core`: Hermes, Factory adapter, agents, skills, profiles, MCP,
  tools, memory and agentic workflow changes.
- `solana-quasar-core`: Quasar-first Solana/onchain program work, wallet
  transactions, signer boundaries, Auditor path and onchain QA.

Template packs that must block until activated:

- `mobile-app-pack`;
- `desktop-app-pack`;
- `game-product-pack`;
- `ai-ml-product-pack`;
- `fintech-payments-pack`;
- `regulated-domain-pack`;
- `data-analytics-pack`;
- `browser-extension-pack`;
- `hardware-iot-pack`.

These template packs are not fake agents. They are explicit coverage gaps with
worker templates, activation rules and evidence requirements.

## What Was Not Promoted

No new public executable worker was promoted from the reference repositories in
this pass. That is intentional.

A new worker becomes executable only after a repeatable input, verifiable
output, permission class, Hermes binding, smoke evidence and eval result exist.
Until then, the capability pack registry records the gap and blocks execution
when the product surface needs that specialist.

Rejected for core now:

- broad auto-spawn based only on context;
- copying reference SOULs/prompts/personas;
- broad tool allowlists because another repository uses them;
- Anchor/Pinocchio-specific core workers before a Quasar-first pilot proves the
  need;
- native mobile, desktop, game, AI/ML, fintech, regulated, analytics, browser
  extension or hardware workers without pack activation evidence.

## Backlog Candidates

These remain useful, but should not block the pre-pilot battery unless a pilot
card explicitly needs them:

- closed reviewer selector worker after repeated reviewer-selection plans pass;
- optional Anchor/Pinocchio pack if a future Solana paper requires it;
- API-docs writer skill if docs-shape routing repeats;
- observability sweep contract for production products;
- finding dedup/fingerprint model across AutoReview, independent review and
  security specialists;
- agent manifest drift auditor comparing registry, bindings, Hermes profiles,
  SOUL files, permission classes and smoke evidence.

## Final Rule

Use reference repositories as operational evidence:

```text
reference agent/skill -> matching Overkill agent/skill -> concrete gap
-> contract/profile/schema/test patch -> validation -> optional promotion later
```

No reference agent becomes an Overkill worker without a contract, permission
class, eval, reviewer separation and Kanban routing reason.
