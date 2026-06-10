# Worktrees And Parallel Agents

This document defines how Overkill Factory uses parallel work without losing
control of evidence, safety or ownership.

## Principle

Parallelism is useful only when the work remains auditable.

The factory may use multiple agents, worktrees or runtime workers at the same
time, but each lane needs a clear scope, owner, write boundary, evidence and
merge rule.

## When Parallel Work Is Allowed

Parallel work is allowed when tasks are independent:

- different documents;
- different schemas;
- different test files;
- separate proof harnesses;
- read-only audits;
- independent worker packets;
- independent validation reviews.

Parallel work is not allowed when two agents need to edit the same contract,
same schema, same canonical section, same receipt, same migration, same runtime
board or same release decision unless one agent is explicitly the integrator.

## Lane Contract

Every parallel lane needs:

- lane name;
- owner agent or worker;
- input refs;
- write scope;
- forbidden files or surfaces;
- expected output;
- validation command;
- evidence refs;
- cleanup rule;
- integration owner.

If a lane cannot name its write scope, it should be read-only.

Machine-checkable lane contracts use:

```text
schemas/parallel-lane-contract.schema.json
templates/parallel-lane-contract.json
```

Validate one with:

```bash
python scripts/factoryctl.py validate-lane path/to/parallel-lane-contract.json
```

A write lane cannot be ready for integration unless it lists changed files,
keeps those files inside the declared write scope, avoids forbidden paths,
passes validation, includes evidence refs and has cleanup resolved.

A read-only lane can finish with no changed files, but it still needs inputs,
expected output, validation result, evidence refs and cleanup status.

## Worktree Rules

Use a worktree when a lane needs code or doc edits that could conflict with the
main rollout.

Before creating or using a worktree:

1. record the base branch or commit;
2. record the intended write scope;
3. check whether the main worktree is dirty;
4. avoid copying private runtime artifacts into the worktree;
5. define how changes will be reviewed and integrated.

After worktree work:

1. list changed files;
2. run scoped tests;
3. run public-safety and secret scans when public artifacts changed;
4. integrate only reviewed changes;
5. remove temporary worktrees only after integration or explicit abandonment.

## Subagent Rules

Subagents are best for sidecar work:

- audit one subsystem;
- inspect docs for contradictions;
- review validation coverage;
- propose a map outline;
- implement a bounded patch in a disjoint file set.

Subagents should not:

- touch Hermes real without explicit runtime instructions;
- invent production proof;
- edit broad overlapping areas;
- clean unrelated files;
- publish, merge, delete or reset history.

## Integration Rule

The main agent remains responsible for integration.

Subagent output is evidence, not truth by itself. The main agent must check for:

- conflict with current worktree state;
- public/private boundary;
- validation coverage;
- consistency with the canonical vFinal model;
- whether the change belongs in canonical docs, roadmap, validation, or private
  context.

## Public-Safe Boundary

Parallel work must not put these into public artifacts:

- private product names;
- local absolute paths;
- private board ids;
- raw Hermes task ids or run ids;
- private URLs;
- secrets, tokens, webhooks or credentials;
- raw logs that may contain any of the above.

Use redacted refs or `external:<name>` for private evidence.

## Done For A Parallel Lane

A lane is done only when it provides:

- changed paths or explicit read-only result;
- evidence refs;
- validation result;
- residual risks;
- cleanup status;
- integration recommendation.
