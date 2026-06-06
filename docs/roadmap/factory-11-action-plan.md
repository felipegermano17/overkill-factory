# Factory 11 Action Plan

Factory 11 is the next Overkill Factory version bump.

The goal is to turn the current methodology, contracts and pilot evidence into
a public-safe, durable, agent-operable production system.

## Implementation Status

Materialized in this Factory 11 pass:

- public hygiene scan: `scripts/public_safety_scan.py`
- CI gate: `.github/workflows/ci.yml`
- source policy: `docs/research/source-capture-policy.md`
- source resolution: `docs/research/factory-11-source-resolution.md`
- Hermes compatibility manifest: `adapters/hermes/compatibility-manifest.md`
- Hermes update runbook: `adapters/hermes/update-runbook.md`
- Hermes update receipt template: `adapters/hermes/update-receipt.template.json`
- Hermes compatibility check: `adapters/hermes/compatibility-check.py`
- worker roster: `agents/worker-roster.md`
- worker schema: `agents/worker-contract.schema.json`
- public worker registry: `agents/worker-registry.public.json`
- expanded worker routing in `scripts/factoryctl.py`
- security control matrix: `docs/security/security-control-matrix.md`
- Product Face proof: `docs/product-face/proof-runner.md`
- supply-chain CI/SBOM proof: `scripts/supply_chain_proof.py` and
  `validation/supply-chain/`
- context spine: `docs/memory/context-spine.md`
- risk register: `docs/risks/future-risk-register.md`
- map source refresh: `docs/maps/factory-10-flow.mmd`
- illustration brief: `docs/illustrations/factory-11-production-line-illustration.md`
- methodology hardening: `docs/methodology/factory-11-operational-hardening.md`

Still reserved for the next goal:

- multi-context heavy validation battery;
- real product pilots;
- disposable Hermes update smoke;
- live dashboard/API bypass testing;
- managed remote proof run;
- product-specific release/human R4 gate;
- full production worker graph with every critical lane reusable.
- product-specific dependency audit/provenance once real runtime dependencies
  exist.

## Rules For This Version

1. The repository must remain public-safe.
2. No private workspace names, local machine paths, private board ids, personal
   approval identities, or internal runtime details belong in public artifacts.
3. Study material does not belong in this public repo. Raw social-post
   extraction, screenshots, private ledgers and internal source work must stay
   outside the repo.
4. Public methodology claims must be traceable without exposing private
   material: use public source URLs, generic source-note formats, or
   reproducible local artifacts.
5. Agent work must be judged by evidence, not by self-report.
6. Small tasks should stay lightweight. High-risk tasks need full gates.
7. Security is not one generic review. It is a matrix of controls and specialist
   responsibilities.
8. Hermes integration must be protected by compatibility tests and an update
   runbook.

## P0 - Public Hygiene

The repo needs a full public-safety pass.

Remove or generalize:

- private product names
- private runtime identifiers
- local filesystem paths
- private board/task ids
- private human names
- private workspace URLs
- internal profile names that do not make sense for open-source users

Replace with reusable public terms:

- `product-owner`
- `factory-security`
- `factory-reviewer`
- `security-runner`
- `onchain-auditor`
- `product-face-validator`
- `real Hermes runtime`
- `example pilot`

Done means:

- `README.md` is public-safe.
- All docs are public-safe.
- All examples and fixtures are public-safe.
- Public docs still explain how to reproduce the factory without private context.

## P0 - Source Capture Policy

External source study must be explicit.

Raw study artifacts must not be stored in the public repo. Keep source ledgers,
screenshots and extraction snapshots in a private research workspace. The public
repo may keep only a generic policy and distilled decisions.

Before recapturing any source, check existing local artifacts first.

For each source:

- capture URL
- capture date
- source type
- author/title when visible
- main claim
- factory implication
- confidence
- whether it becomes a rule, worker, gate, checklist, or rejected input

For social posts and long articles, do not copy long text into the repo. Convert
them into source notes and operational decisions.

## P0 - Hermes Update Safety

Hermes is a required runtime integration, so updates cannot rely on memory or
manual caution.

Add:

- `adapters/hermes/compatibility-manifest.md`
- `adapters/hermes/update-runbook.md`
- adapter regression fixtures
- a compatibility check script

The update process must be:

```text
fetch upstream
-> inspect release and changed surfaces
-> apply or port adapter
-> run adapter tests
-> run disposable Hermes smoke
-> produce update receipt
-> update real runtime only after pass
```

Done means a contributor can decide whether a Hermes update is safe without
reading old chat context.

## P0 - Agent Workforce Redesign

The factory needs a stronger worker model.

Each worker must define:

- worker id
- purpose
- open or closed mode
- trigger
- inputs
- tools
- output contract
- authority limit
- veto conditions
- required evidence
- separation-of-duty rule

Worker classes to add or harden:

- Orchestrator
- Source/SOT Planner
- Product Architect
- Product Face Validator
- Documentation OS Worker
- Decomposition Planner
- Implementation Worker
- QA/Verification Worker
- Independent Reviewer
- AutoReview Gate
- Handoff Packer
- Remote Proof Runner
- Security Orchestrator
- AppSec/OWASP Specialist
- Agentic AI Security Specialist
- Cloud/Infrastructure Security Specialist
- Detection/Monitoring Specialist
- Crypto/Key Management Specialist
- Onchain/Solana/Quasar Auditor
- Release/Operations Worker
- Skill Eval Worker
- Memory Steward
- Human Gate Clerk

## P0 - Security Control Matrix

Create a security matrix that covers at minimum:

- networking basics
- Linux and systems
- web security
- ethical hacking workflow
- security tools
- cloud security
- detection and monitoring
- cryptography
- security operations
- future security
- OWASP web/API/application controls
- OWASP LLM and agentic AI risks
- secrets and key management
- software supply chain
- dependency and SBOM checks
- CI/CD security
- infrastructure-as-code checks
- runtime monitoring and incident response
- onchain/Solana/Quasar-specific risks

Done means high-risk cards cannot proceed with a generic security paragraph.
They need the right specialist coverage and evidence.

## P1 - AutoReview Gate

Add AutoReview as a named gate before commit, ship, or promotion for non-trivial
code work.

Why it is better than a generic reviewer:

- it is repeatable
- it runs against a defined diff/branch/commit
- findings must be verified against real code
- fixes trigger focused tests and another review pass
- the process stops only when no accepted/actionable findings remain

## P1 - Handoff Packer

Add a worker that creates portable handoff prompts for another agent.

Why it is better than a normal summary:

- no private path leakage
- starts with independent review
- includes constraints and non-goals
- tells the receiving agent not to push/merge/publish unless authorized
- preserves enough context without turning into a transcript dump

## P1 - Remote Proof Runner

Add a worker for heavy validation using remote proof environments such as
crabbox/testbox or a local-container fallback.

Why it is better than only local tests:

- cleaner environment
- closer to CI
- better for long or broad gates
- clearer provider-backed receipts

Use local targeted tests for tight loops. Use remote proof for broad gates.

## P1 - Product Face Proof

Product Face must move beyond packet presence.

Add proof for:

- screenshots
- mobile viewport
- accessibility basics
- important UI states
- visual overlap checks
- user-facing copy sanity
- browser/runtime evidence

## P1 - Memory Spine

Create a memory model for the factory only after separating source evidence from
architecture hypotheses. This is not derived from the open-vs-closed specialist
source by itself.

Potential memory categories:

- source memory
- decision memory
- artifact memory
- worker memory
- risk memory
- production learning memory

Every memory write needs:

- source
- trust tier
- author/worker
- timestamp
- expiration or review condition
- poisoning risk note when relevant

Memory is useful, but it is also a control surface. Treat it accordingly.

## P1 - Map And Illustration

Refresh the visual assets.

Mind map:

- stronger color system
- linear factory path remains clear
- dedicated worker lane
- each worker gets a short config summary

Illustration:

- use the installed hand-drawn illustration skill
- create a 16:9 visual explanation of the factory
- keep it simple, white background, black line art, sparse color annotations
- show raw paper entering a controlled factory and verified product leaving

## P2 - Hermes Capability Adoption

Study and adopt useful Hermes improvements only after the compatibility process.

Likely candidates:

- desktop/remote gateway improvements
- admin dashboard improvements
- model picker improvements
- `/goal` and subgoal operating model
- Kanban refinements
- memory/admin controls
- skill management improvements
- security fixes

Done means each adopted capability has a factory use case, not just a release
note mention.

## P2 - Hermes Transition-Plan Integration

The adapter should graduate from static gate checks to a runtime transition
planner.

At `ready`, the planner should create Hermes subtasks for every required worker
and put them into the right queue. At `done`, the planner should reconcile
worker results against Receipt Five and block closure when evidence is missing
or only preflight-level.

Required runtime work:

- Kanban event hook before `ready`;
- Kanban event hook before `done`;
- idempotent worker subtask persistence;
- queue mapping for before-ready, before-done and advisory review work;
- worker result ingestion with artifact refs;
- Receipt Five reconciliation;
- shared enforcement for CLI, dashboard, API and worker routes;
- disposable Hermes smoke proving no route can bypass the gate.

Done means public fixtures are backed by live Hermes behavior, not only by
generated JSON examples.

## Factory 11 Done Definition

Factory 11 is done when:

- public repo hygiene is complete
- source capture policy exists
- Hermes update runbook and compatibility tests exist
- Hermes transition-plan integration has either landed or is explicitly listed
  as the next runtime gap
- worker roster is redesigned
- security matrix exists
- AutoReview, Handoff and Remote Proof are represented as gates/workers
- Product Face proof is defined
- memory spine is defined
- map and illustration plan are ready
- every new claim has source status and factory implication
