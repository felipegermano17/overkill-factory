# Factory V3.6 Learning Loop

> Document status: HISTORICAL EVIDENCE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This is not the current factory rule; it records V3.6 learning-loop inputs that were later superseded by runtime enforcement.

V3.6 must be generated only after pilot evidence, not opinion.

The first completed pilot is a dry pilot, not a production product:

```text
pilot: pilots/quasar-vault-guard-test
Hermes board: overkill-factory-pilot-10
Hermes task: public-methodology-card
status: done
```

This is enough to promote contract and process learnings. It is not enough to
claim production readiness or Quasar program safety.

## Questions To Answer

1. What was too heavy for agents?
2. What was too vague for agents?
3. What did agents misinterpret?
4. What did humans have to clarify?
5. Which gates blocked real risk?
6. Which gates created bureaucracy without safety?
7. Which artifacts were actually useful downstream?
8. Which artifacts were ignored or duplicated?
9. Which worker should become more automated?
10. Which worker should stay human-gated?

## Required Changes

Each V3.6 change must include:

- problem observed
- evidence from pilot
- proposed change
- why better than current behavior
- risk introduced by the change
- Hermes adapter impact
- skill update impact

## Output

- `docs/methodology/overkill-factory-v3-6.md`
- updated schemas
- updated Hermes adapter tests
- updated Codex skill
- updated Whimsical/Mermaid map

Use `templates/v3-6-learning-record.md` during the pilot so learning is
captured as evidence, not memory.

## Dry-Pilot Learnings Already Promoted

### 1. Local Validator Must Fail Before Hermes Fails

Problem observed: Hermes blocked completion twice after local validation passed.

Evidence:

- first block: `security_scan_result` lacked `scanner_agent`, `tool`, `scope`
  and Codex Security reference;
- second block: Hermes V2 completion metadata lacked evidence paths,
  verification, sandbox, rollback and scoped approval records.

Change:

- `factoryctl.py`, schemas and Codex skill validators now validate the compound
  Factory 10 + Hermes V3.5 + Hermes V2 receipt contract.

Why better: agents get a local, deterministic failure before they mutate Kanban
state.

### 2. Portable Pilot Package

Problem observed: Hermes reviewers could not re-run `factoryctl.py` inside the
context-lock pilot package.

Change:

- the pilot package now includes `tools/factoryctl.py`;
- README and Receipt Five include portable commands.

Why better: a reviewer does not need hidden repo context to verify a package.

### 3. Gate Report Is Preflight, Not Final Status

Problem observed: Hermes reviewers repeatedly flagged that
`gate-report-first-slice.json` still says workers `requires_execution` even
after worker results exist.

Change:

- the pilot now has `evidence/worker-closure-summary.json`;
- methodology now includes `preflight -> packet -> result -> closure summary ->
  Receipt Five`.

Why better: agents stop reading a preflight artifact as a final completion
state.

### 4. Dry Pilot Approval Is Not Production Approval

Problem observed: every Hermes reviewer passed the dry pilot only with hard
boundaries.

Change:

- approvals in Receipt Five are scoped to `dry pilot only`;
- forbidden authority is repeated in human gate, worker summary, receipt and
  Hermes comments.

Why better: the factory can close process tests without accidentally granting
deploy, signing, funds, devnet or mainnet authority.
