# Factory Learning And Skill Evolution OS

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `schemas/factory-learning-proposal.schema.json`,
> `scripts/factory_self_improvement.py`, `skill-eval-distiller`, tests.
> Runtime boundary: this OS creates inactive proposals and public-safe issue
> candidates. It does not auto-activate rules, skills, workers, hooks, MCPs,
> install profiles or gates.

## Purpose

The factory should improve from execution evidence without becoming a pile of
agent-written notes. Learnback, plan-review findings, repeated corrections and
reusable workflow patterns must become typed proposals that can be validated,
reviewed, activated or rejected.

The source of a learning proposal can be:

- `execution_learnback_record`;
- independent plan review;
- recurring Receipt Five reconciliation finding;
- governance audit;
- issue intake from an owner-controlled factory instance;
- public research summarized through a read-only source pass.

Raw private evidence is not a learning artifact. Public proposals use redacted
evidence refs such as `external:run-summary`, `.tmp` outputs during validation,
or public-safe issue links.

## Proposal Contract

Use `templates/factory-learning-proposal.json` as the starting point. Each
proposal must name:

- source evidence refs;
- source trust level;
- classification;
- proposed artifact type;
- risk;
- owner;
- validation plan;
- activation policy;
- untrusted input handling;
- tool governance;
- rejection rationale.

Supported classifications are:

`rule`, `skill`, `worker`, `gate`, `schema`, `test`, `doc`, `reference`,
`issue`, `hook`, `mcp_or_tool`, `install_profile`, and `reject`.

Every non-rejected proposal needs independent review before activation. Worker,
gate, hook, MCP/tool and install-profile proposals land as inactive candidates
and require explicit review. Sensitive domains such as production, secrets,
credentials, custody, mainnet, legal, privacy, billing or hardware require a
human gate before mutation.

## Skill Promotion

A workflow can become a factory skill only after this lifecycle:

1. repeated workflow, correction or failure is observed;
2. `factory_learning_proposal` is created as `inactive_candidate`;
3. trigger conditions and source evidence refs are recorded;
4. focused tests or eval fixtures prove the skill helps;
5. independent review checks scope, safety and maintainability;
6. public-safety, secret-safety and supply-chain checks pass;
7. activation policy names scope, budget, tools and stop condition;
8. learnback after real use confirms the skill remains useful.

Skills should carry scripts or fixtures when that prevents agents from
recreating boilerplate from memory. Large references stay on demand; they should
not bloat always-loaded context.

## Plan Review

Material work should not move from plan to implementation only because the
generating agent likes its own plan. Require independent critical review for:

- security-sensitive work;
- architecture or registry/binding changes;
- product-facing surfaces;
- release or production operations;
- reusable skills, hooks, MCPs, gates, schemas or worker profiles.

The reviewer looks for missing security decisions, weak auth assumptions,
architecture drift, convenience implementations, missing tests, unclear owners,
missing rollback/release gates and invented details. Repeated review corrections
become learning proposals.

## Scheduled Learning

Scheduled or dream passes are allowed only as public-safe proposal generation.
They may read structured execution evidence, issue snapshots and governance
reports, then produce `factory_learning_proposal` or
`factory_improvement_issue_candidate` records. They must not dispatch workers,
approve gates, post public comments or mutate runtime state without a separate
owner-approved scope, cadence, budget and stop condition.

## Untrusted Sources

External posts, articles, repositories and docs are inputs, not authority. Use a
reader/actor split:

- a read-only source pass summarizes raw external content;
- privileged factory actors consume only structured summaries and source refs;
- copied code/assets require license or terms evidence;
- rejected ideas keep rejection rationale instead of disappearing.

This protects the factory from prompt injection, vendor lock-in and accidental
adoption of patterns that do not fit the factory spine.

## Parallel Workflows

Parallelism is a tool, not a default. Use fan-out, adversarial verification,
tournament, generate-and-filter or loop-until-done patterns when the task
benefits from independent evidence, review pressure or scale. Detailed
lane/worktree boundaries, write scopes and reconciliation stay in
`operations/parallel-execution-and-status.md`.

## Completion Bar

A learning proposal is complete only when it has:

- public-safe source evidence refs;
- validation commands or evals;
- independent review provenance;
- explicit activation policy;
- budget, max agents, timeout and stop condition;
- tool/MCP/hook trust and supply-chain posture;
- rejection rationale when not adopted.

Narrative alone is not learning. Unvalidated learning is only a candidate.
