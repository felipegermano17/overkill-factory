# Document Governance

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py`, schemas, tests and `README.md`.
> Runtime boundary: This guide controls document classification; executable gates still decide factory runtime behavior.

This page defines which documents can guide an external user and which ones are
allowed only outside the public repository.

## Authority Order

Use this order when documents disagree:

1. Executable gates: `scripts/factoryctl.py`, schemas, adapter hooks and tests.
2. Current user path: `README.md`, `docs/getting-started/quickstart-hermes.md`,
   `docs/concepts/factory-flow.md` and `docs/operations/validation-and-release.md`.
3. Supporting guides: agent, worker, capability, security and Product Face docs.
4. Machine-readable fixtures under `.tmp/factory-runs/` when a test or script directly
   needs them.

When prose and runtime disagree, runtime wins. Fix the prose or the runtime, but
do not let a document silently override a gate.

## Required Status Banner

Every high-risk narrative document must start with:

```text
> Document status: <status>.
> Current authority: <current executable or current guide>.
> Runtime boundary: <what this document can and cannot prove>.
```

High-risk narrative documents include methodology drafts, roadmaps, reviews,
risk registers, planning notes, pilot writeups, research notes, validation
reports, screenshots and past-test evidence. Those artifacts should stay in a
private workspace, issue, release note or local `.tmp` output unless they are
rewritten as current user documentation.

Any other `docs/` file that uses ambiguous planning or status language such as
`future`, `remaining`, `still open`, `not yet`, `TBD`, `TODO` or `does not
prove` also needs a status banner. A supporting guide may discuss limits, but it
must not look like an unowned live task list.

## Status Labels

| Status | Meaning |
| --- | --- |
| `CURRENT SUPPORTING GUIDE` | Current external-user guidance, but still subordinate to executable gates. |
| `ACTIVE BACKLOG` | Candidate work. Track it in GitHub issues, not in public docs. |
| `ACTIVE RISK REGISTER` | Known risks and candidate mitigations. Track as issues or security advisories, not completion authority. |
| `ACTIVE PILOT GUIDE` | Guidance for a current pilot class. Keep raw results out of the repo. |
| `HISTORICAL EVIDENCE` | Prior validation or review evidence. Keep it outside the public repository. |
| `LEGACY METHOD` | Older methodology retained outside the public repo for migration only. |

## External User Rule

A user arriving from the public repo should be able to answer three questions
without reading historical files:

1. What do I run first?
2. What blocks work?
3. Which command or contract blocks the next move?

If a new document makes those answers less clear, move it to a GitHub issue,
release note, private evidence store or local `.tmp` output before publishing.

## Validation

Run this check before claiming the docs are clean:

```bash
python scripts/validate_document_governance.py
```
