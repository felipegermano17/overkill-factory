# Factory 11 Operational Hardening

> Document status: HISTORICAL EVIDENCE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This is not the current factory rule; hardening that survived is enforced by current schemas, scripts, tests and receipts.

Factory 11 is not a new philosophy. It is the hardening layer that makes the
factory safer for autonomous agents and public open-source operation.

## What Changed

1. Public study material boundary is explicit.
2. X/social sources are resolved from existing ledgers before recapture.
3. Memory/context spine is treated as a separate architecture hypothesis, not
   as a claim from the open-vs-closed specialist source.
4. Agent roster now separates open, closed and hybrid workers.
5. Security is a control matrix, not one generic security worker.
6. AutoReview, Handoff and Remote Proof are first-class workers/gates.
7. Hermes updates require compatibility manifest, runbook, receipt and checks.
8. Public repo safety is enforced by a scanner and CI.
9. Future risks are tracked as factory work, not left as chat memory.

## Final Factory Spine

```text
paper
-> source ledger
-> Product SOT
-> alignment questions
-> architecture candidate
-> Product Face
-> specialist reviews
-> human architecture gate
-> Documentation OS
-> decomposition
-> worker packets
-> Hermes Ready Gate
-> agent execution
-> worker results
-> AutoReview / security / Auditor / Product Face proof
-> independent review
-> closure summary
-> Receipt Five
-> Hermes Done Gate
-> release or block
-> monitoring
-> learning loop
```

## Why This Is Better Than Factory 10 Alone

Factory 10 proved that gates can block weak work. Factory 11 makes the system
less dependent on private context and more executable by agents:

- public artifacts are safe by default;
- workers have modes, triggers and authority limits;
- security has named domains;
- Hermes updates cannot silently break the floor;
- AutoReview and Handoff are explicit instead of informal;
- remote proof is available without becoming default overkill;
- risks become artifacts agents can inspect.

## Open vs Closed Specialists

Use open specialists when:

- the task is exploratory;
- ownership is unclear;
- tradeoffs matter;
- taste or judgment is required;
- the output is not easily verified.

Use closed specialists when:

- the same shape has repeated;
- inputs are predictable;
- output is verifiable;
- tools are scoped;
- the worker can produce a structured result.

Why this is better: it avoids both extremes. Open specialists do not become
endless wandering sessions, and closed specialists are not forced to make
judgment calls they cannot verify.

## Security Timing

- F0/F1: source and prompt-injection review.
- F4/F6: architecture threat model and required specialist routing.
- F8: `security_scan_packet`.
- F13: scan execution and domain checks.
- F14/F15: independent review, AutoReview and waiver scrutiny.
- F16/F17: release security, public safety, monitoring and rollback.

## Hermes Update Timing

Hermes update work is never done directly on the real runtime first. It must go:

```text
target version
-> disposable compatibility check
-> adapter patch apply
-> negative/positive smokes
-> update receipt
-> real-runtime decision
-> rollback-ready monitoring
```

## Public Repository Rule

Public Overkill artifacts can explain the factory, but cannot carry private
source extraction, private links, internal names, local paths or private runtime
details. The public repo is the productized factory, not the research notebook.

## Remaining Non-Negotiable Gap

Factory 11 is not final validation. The next goal must run a battery of heavy
pilots across different products, risks, stacks and ambiguity levels. A single
pilot can prove the line moves; it cannot prove the factory is robust.
