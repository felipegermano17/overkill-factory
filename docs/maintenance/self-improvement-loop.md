# Factory Self-Improvement Loop

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factory_self_improvement.py`, schemas, tests.
> Runtime boundary: these helpers produce dry-run plans and public-safe
> candidates. They do not dispatch Hermes, activate workers, post GitHub
> comments or approve gates.

## Purpose

The factory should learn from its own execution without leaking private run
evidence or turning every observation into a public issue. The self-improvement
loop converts blocked capability gaps, execution learnback records, owner issue
intake and governance checks into structured artifacts.

## Contracts

- `schemas/missing-capability-completion-plan.schema.json`
- `schemas/execution-learnback-record.schema.json`
- `schemas/factory-sdlc-feedback-loop.schema.json`
- `schemas/factory-readiness-scorecard.schema.json`
- `schemas/factory-learning-proposal.schema.json`
- `schemas/factory-improvement-issue-candidate.schema.json`
- `schemas/owner-issue-intake-config.schema.json`
- `schemas/owner-issue-intake-report.schema.json`
- `schemas/ai-codebase-governance-report.schema.json`
- `schemas/reasoning-policy.schema.json`
- `schemas/reference-quality-packet.schema.json`
- `schemas/reference-source-registry.schema.json`

## Missing Capability Completion

When a gate report shows blocked workers, missing profile bindings or capability
coverage gaps, use:

```bash
python scripts/factory_self_improvement.py missing-capability-plan \
  --gate-report .tmp/gate-report.json \
  --out .tmp/missing-capability-plan.json
```

The output is a candidate plan. It can propose worker/profile/schema/binding
artifacts, but material execution remains blocked until validation, independent
review and any required human gate pass.

Sensitive domains such as production, credentials, secrets, funds, custody,
mainnet, legal/regulatory, privacy or hardware must not auto-activate.

## Execution Learnback

After material execution, generate an `execution_learnback_record` from Receipt
Five and, when available, the Evidence Graph:

```bash
python scripts/factory_self_improvement.py learnback-record \
  --receipt .tmp/receipt-five.json \
  --evidence-graph .tmp/evidence-graph.json \
  --out .tmp/execution-learnback-record.json
```

Then generate issue candidates:

```bash
python scripts/factory_self_improvement.py learnback-issues \
  --record .tmp/execution-learnback-record.json \
  --out .tmp/factory-improvement-issue-candidates.json
```

Public issue candidates must be generalized and redacted. Raw private logs,
local paths, private board ids, Discord ids and screenshots do not belong in
public issue bodies.

For material vFinal execution, the learnback record must carry the same
`sdlc_feedback_loop_ref` used by the card, worker packet, worker results and
Receipt Five reconciliation. Issue candidates generated from learnback preserve
that ref so a public-safe issue can still point to the SDLC loop without
publishing private evidence.

## SDLC Feedback Loop

Use `factory_sdlc_feedback_loop` when a signal needs to stay connected across
the full factory loop:

```text
signal -> triage -> model/profile route -> evidence -> learnback
```

The loop record does not replace lifecycle state, worker results, evidence
bundles or learning proposals. It binds them so a signal cannot disappear into
chat-only state, a model/profile choice cannot become implicit, and learnback
cannot claim improvement without a target, validation path and promotion
boundary.

```bash
python scripts/factoryctl.py validate-sdlc-feedback-loop \
  templates/factory-sdlc-feedback-loop.json
```

Use this before converting external research, incidents, review findings,
runtime gaps or product quality findings into durable factory changes.

For `OVERKILL_VFINAL` cards with bounded, material or production autonomous
execution, add `sdlc_feedback_loop_ref`. Planning-only and read-only work can
stay lighter, but material work must not run without a feedback loop that keeps
signal, routing, evidence and learnback connected.

Those material cards must also declare `autonomy_mode`,
`agent_readiness_basis` and either `model_routing_decision_ref` or an inline
`model_routing_decision`. The feedback loop records the broader signal and
learning context, while the card records the executable autonomy choice that the
worker packet must preserve: how much human guidance is required, how sensitive
the information is, which autonomy scope is allowed, why the model/profile route
is acceptable, and where the work returns when validation fails.

## Factory Readiness Scorecard

Use `factory_readiness_scorecard` before long autonomous execution to decide
whether the factory can proceed, proceed with bounds, remediate, or block:

```bash
python scripts/factoryctl.py validate-readiness-scorecard \
  templates/factory-readiness-scorecard.json
```

The scorecard checks the execution environment around the work: build/install,
tests, static checks, docs/first run, task discovery, worker/profile readiness,
public/private evidence hygiene, observability/incident/rollback, security,
product success signals and autonomy risk.

It is not product acceptance, customer readiness, release approval, security
approval or a cockpit status. Non-passing dimensions require a remediation
loop, and blocking dimensions must keep autonomous execution off until the
scorecard is rerun with evidence.

## Learning Proposals

Use `factory_learning_proposal` when a finding should become a durable rule,
skill, worker, gate, schema, test, doc, reference, issue, hook, MCP/tool,
install profile or recorded rejection:

```bash
python scripts/factory_self_improvement.py learning-proposals \
  --record .tmp/execution-learnback-record.json \
  --out .tmp/factory-learning-proposals.json
```

Learning proposals land as inactive candidates. They need validation,
independent review and explicit activation policy before they can change factory
behavior. Sensitive artifacts such as workers, gates, hooks, MCPs and install
profiles must not auto-activate.

Non-rejected learning proposals must also preserve `sdlc_feedback_loop_refs`.
This keeps durable rules, gates, schemas, tests or docs tied to the execution
evidence that justified them, instead of letting learnback become chat-only
memory or an unowned mutation.

See `maintenance/factory-learning-skill-evolution-os.md` for the operating
rules.

## Owner Issue Intake

An operator-owned factory instance may review selected GitHub issues and convert
them into blocked factory work:

```bash
python scripts/factory_self_improvement.py issue-intake \
  --config templates/owner-issue-intake-config.json \
  --issues .tmp/issues.json \
  --out .tmp/owner-issue-intake-report.json
```

This is off by default for external users. The public project supports the
contract, but each owner instance decides which repos, labels and milestones it
trusts.

Critical factory changes still require human gate before implementation.

Accepted intake rows include an `owner_issue_factory_card_candidate`. This is
not an executed card. It is a bounded draft with source issue, risk, required
gates, done definition and activation policy so the owner instance can hand it
to the factory without losing auditability.

## Reasoning Policy

`reasoning_policy` makes the reasoning depth, profile class, review intensity
and durable evidence policy explicit on vFinal cards. It controls what a worker
must be able to do; it must not store or publish raw chain-of-thought.

If the active worker route cannot satisfy the policy, the card should block
instead of silently falling back to a weaker profile.

## Reference Quality Packet

For vFinal product-facing work, `reference_quality_packet` is a sub-contract of
Product Experience OS/Product Face. It establishes the quality bar before
generation. It does not approve UI and it is not a separate UX operating system.

References are benchmarks or inspiration unless a license is recorded for code
or asset reuse. Product Face remains the proof layer after implementation.

## Governance Audit

Use:

```bash
python scripts/factory_self_improvement.py governance-audit \
  --out .tmp/ai-codebase-governance-report.json
```

The report is a public-safe maintainer artifact for architecture risk, generated
artifact policy and mandatory validation checks.
