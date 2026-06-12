# Document Governance

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This guide controls document classification; executable gates still decide factory runtime behavior.

This page defines which documents can guide an external user and which ones are
only evidence, backlog or historical context.

## Authority Order

Use this order when documents disagree:

1. Executable gates: `scripts/factoryctl.py`, schemas, adapter hooks and tests.
2. Canonical runtime evidence: `validation/canonical-runtime-enforcement/` and
   `validation/canonical-real-infra/`.
3. Current user path: `README.md`, `docs/getting-started/quickstart-hermes.md`,
   `docs/concepts/factory-flow.md` and `docs/operations/validation-and-release.md`.
4. Supporting maps: agent, worker, capability, security and Product Face docs.
5. Backlog, reviews, risk registers, planning notes and historical methodology.

When prose and runtime disagree, runtime wins. Fix the prose or the runtime, but
do not let a document silently override a gate.

## Required Status Banner

Every high-risk narrative document must start with:

```text
> Document status: <status>.
> Current authority: <current executable or current guide>.
> Runtime boundary: <what this document can and cannot prove>.
```

High-risk narrative documents include `docs/methodology/`, `docs/roadmap/`,
`docs/reviews/`, `docs/risks/`, `docs/planning/`, `docs/pilots/` and
`docs/validation/`.

Any other `docs/` file that uses ambiguous planning or status language such as
`future`, `remaining`, `still open`, `not yet`, `TBD`, `TODO` or `does not
prove` also needs a status banner. A supporting guide may discuss limits, but it
must not look like an unowned live task list.

## Status Labels

| Status | Meaning |
| --- | --- |
| `CURRENT SUPPORTING GUIDE` | Current external-user guidance, but still subordinate to executable gates. |
| `ACTIVE BACKLOG` | Candidate work. Not a runtime requirement until it becomes schema, script, test, worker, gate or receipt. |
| `ACTIVE RISK REGISTER` | Known risks and candidate mitigations. Not completion authority. |
| `ACTIVE PILOT GUIDE` | Guidance for running a specific pilot class. It does not approve a product. |
| `HISTORICAL EVIDENCE` | Prior validation or review evidence. Useful for context only. |
| `LEGACY METHOD` | Older methodology retained so existing legacy cards can be understood. Not the current vFinal rule. |

## External User Rule

A user arriving from the public repo should be able to answer three questions
without reading historical files:

1. What do I run first?
2. What blocks work?
3. Which file is evidence vs current instruction?

If a new document makes those answers less clear, classify it or move it under a
validation, research, roadmap or historical path before publishing.

## Validation

Run this check before claiming the docs are clean:

```bash
python scripts/validate_document_governance.py
```
