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

After material execution, write an `execution_learnback_record` and generate
issue candidates:

```bash
python scripts/factory_self_improvement.py learnback-issues \
  --record .tmp/execution-learnback-record.json \
  --out .tmp/factory-improvement-issue-candidates.json
```

Public issue candidates must be generalized and redacted. Raw private logs,
local paths, private board ids, Discord ids and screenshots do not belong in
public issue bodies.

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
