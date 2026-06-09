# Factory 13 Worker Scorecard

Date: 2026-06-06

## Scope

This scorecard validates public-safe worker configuration and operability:
registry, profile, Hermes binding, worker packet route, result field, evidence
contract, refusal boundary and tests.

This is not product execution proof. A worker keeps this score only when a real
product card later produces the required receipt evidence.

## Scoring Rule

Each worker is scored against ten checks:

1. clear identity;
2. precise activation surface;
3. bounded authority;
4. refusal conditions;
5. required inputs;
6. receipt/result field;
7. evidence contract;
8. independent review or gate boundary;
9. Hermes binding and skill refs;
10. failure/handoff behavior.

## Result

All 37 routable operators score `10/10` for configuration/operability after the
Factory 13 builder-layer patch.

| Worker | Score | Why it is 10/10 for configuration |
|---|---:|---|
| `factory-orchestrator` | 10/10 | Routes phase/risk/workers and blocks transitions without gaining approval authority. |
| `source-ledger-worker` | 10/10 | Separates source, inference, conflicts and gaps before Product SOT promotion. |
| `product-sot-planner` | 10/10 | Produces SOT candidates with scope, acceptance and open decisions without approval drift. |
| `product-architect` | 10/10 | Owns architecture candidate and specialist routing while keeping human gate mandatory. |
| `product-face` | 10/10 | Owns visible-product proof, screenshots, states, mobile, a11y and overlap evidence. |
| `solana-quasar-auditor` | 10/10 | Owns Auditor/Quasar audit evidence and explicitly forbids Anchor assumptions, keys and deploy authority. |
| `codex-security` | 10/10 | Owns scoped Codex Security/Cybersecurity scans and cannot waive blocking findings. |
| `appsec-owasp-specialist` | 10/10 | Covers OWASP Web/API/AppSec controls with machine-checkable domain and waiver contracts. |
| `agentic-ai-security-specialist` | 10/10 | Covers prompt injection, tools, memory, browser and autonomy boundaries. |
| `autoreview-gate` | 10/10 | Provides report-only pre-landing review and cannot replace independent review. |
| `remote-proof-runner` | 10/10 | Runs clean/heavy proof with TTL, cost, cleanup and artifact boundaries. |
| `handoff-packer` | 10/10 | Produces replayable handoff packets instead of chat-only summaries. |
| `independent-reviewer` | 10/10 | Enforces separate reviewer identity and report-only review boundaries. |
| `human-gate-clerk` | 10/10 | Records real human decisions and explicitly cannot invent approval. |
| `docs-os-worker` | 10/10 | Converts approved architecture into durable docs, ADRs and contracts before decomposition. |
| `decomposition-planner` | 10/10 | Produces card graph with risk, runtime, reviewer and gate contracts. |
| `implementation-worker` | 10/10 | Demoted to fallback-only implementation, preventing one generic builder from owning all work. |
| `frontend-builder` | 10/10 | Builds UI/product surfaces and hands visible proof to Product Face. |
| `backend-api-builder` | 10/10 | Builds API/service/auth behavior with contract tests and security handoff. |
| `data-persistence-builder` | 10/10 | Builds schema/storage/migration changes with rollback and data-risk evidence. |
| `solana-quasar-builder` | 10/10 | Builds scoped Solana program work using Quasar and routes QA/Auditor separately. |
| `solana-quasar-qa-engineer` | 10/10 | Verifies onchain behavior with Quasar/devnet/local proof and negative tests. |
| `wallet-transaction-builder` | 10/10 | Builds wallet/signing transaction states without key or funds authority. |
| `integration-builder` | 10/10 | Connects approved surfaces and refuses to hide missing upstream evidence. |
| `test-automation-builder` | 10/10 | Turns acceptance criteria into repeatable tests/evals without redefining criteria. |
| `infra-devops-builder` | 10/10 | Builds CI/CD/runtime/deploy wiring with smoke, rollback and release handoff. |
| `agent-runtime-builder` | 10/10 | Builds Hermes/factory/agent runtime changes with profile/binding/security boundaries. |
| `qa-verification-worker` | 10/10 | Verifies objective evidence before done/promotion. |
| `security-orchestrator` | 10/10 | Routes security surfaces to concrete specialists instead of generic security review. |
| `cloud-infra-security-specialist` | 10/10 | Covers IAM, KMS, CI/CD, system/runtime and cloud boundaries. |
| `crypto-key-management-specialist` | 10/10 | Covers custody, signing, key lifecycle and separation of duties without touching keys. |
| `release-ops-worker` | 10/10 | Owns release packet, smoke, rollback and monitoring readiness without release approval authority. |
| `memory-steward` | 10/10 | Treats memory as a trust-tiered risk surface and blocks memory-as-truth drift. |
| `skill-eval-distiller` | 10/10 | Promotes repeated work into skills only with evals and held-out cases. |
| `public-safety-gate` | 10/10 | Blocks public leaks with deterministic scan and independent rerun expectations. |
| `supply-chain-gate` | 10/10 | Covers dependencies, CI permissions, provenance, secrets, SBOM and workflow risk. |
| `detection-monitoring-worker` | 10/10 | Requires telemetry, alert owner, runbook, incident drill and rollback signal. |

## Main Change From Factory 12

Factory 12 had good planners, reviewers and gates but still depended on a
generic implementation worker for too much product creation. Factory 13 fixes
that by adding surface-specific builders and demoting the generic worker to a
fallback.

That is better because execution ownership is now testable. A Solana card can
require `solana_quasar_build_result` and `solana_quasar_qa_result`; a frontend
card can require `frontend_build_result`; an agent-runtime card can require
`agent_runtime_result`. The receipt field proves which operator actually owned
the work.

## Remaining Boundary

The score reaches 10/10 for configuration because all workers have contracts,
bindings, route logic and passing tests. It becomes practical 10/10 only after
the full pilot proves that the right workers execute real cards and produce
usable product evidence.
