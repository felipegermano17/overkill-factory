# Overkill Factory 10 Runtime Closure

Date: 2026-06-05

Scope: close Factory 10 as an operational method with Hermes Kanban gates,
without exposing private runtime paths, board ids, task ids, or operator
details in the public repository.

## Verdict

Factory 10 is strong enough as a dry-pilot proof of methodology, contracts and
Hermes gate enforcement.

This does not claim that a real product has shipped to production. It means the
factory now has objective blockers for the failures that usually damage
autonomous execution:

- weak cards;
- Product Face missing from product-facing work;
- onchain work without Auditor;
- R4 work without human gate;
- executor self-review;
- security reduced to prose;
- completion without Receipt Five;
- CLI failure hidden behind a success exit code.

## What Changed

### 1. Factory V3.5 Opt-In Gate

Cards with `factory_method_version` set to `OVERKILL_V3_5_AGENT_WORKFORCE` or
`OVERKILL_V3_5_FACTORY_10` must satisfy a stronger contract before `ready` and
before `done`.

Why better than narrative methodology: agents execute contracts more reliably
than prose. The gate turns the method into state enforcement.

### 2. Product Face Contract

Visible product surfaces require `product_face_packet` with screens, states,
mobile breakpoints, accessibility, performance budget and visual evidence plan.

Why better than backend-only planning: a product also has a face. Without states,
screens and evidence, the factory can deliver an incomplete system while still
claiming progress.

### 3. Onchain/Solana/Quasar Package

Onchain surfaces require `onchain_work_package` with Quasar source references,
account map, instruction ABI, PDA derivation, CPI allowlist and compute-unit
budget. R3/R4 onchain work requires Auditor evidence or structured human waiver.

Why better than generic architecture review: Solana/Quasar work has authority,
signer, CPI and compute risks that generic review misses.

### 4. Security Scan Contract

R3/R4, security, onchain and sensitive surfaces require `security_scan_packet`.
Done requires `security_scan_result` when a scan is required.

Why better than a security comment: the card records timing, scope, tool,
scanner identity and evidence refs. The done gate refuses unsupported claims.

### 5. Anti-Self-Review

`executor_identity` and `reviewer_identity` must differ.

Why better than trust: autonomous work inflates confidence when the same worker
executes and approves. Separation is a cheap and powerful control.

### 6. R4 Human Gate

R4 requires a human gate packet with approval reference, rollback plan, risk
owner and security owner.

Why better than "looks safe": R4 needs explicit authority and recovery, not
implicit confidence.

### 7. Receipt Five

Done requires `receipt_five` and `kanban_transition_event`.

Why better than marking a card done: the receipt records what changed, where the
evidence is, how it was verified, who reviewed it and what happens next.

### 8. CLI Exit-Code Propagation

Hermes command failures must return non-zero exit codes.

Why better than console prose: agents and scripts read exit codes. A rejected
transition with exit code `0` is an operational bypass.

## Evidence Shape

The private runtime proof covered:

- invalid Product Face card blocked;
- valid Product Face card allowed through ready but blocked before weak done;
- onchain R3 without Auditor blocked;
- R4 without human gate blocked;
- completion without metadata failed with exit code `1`;
- security card without scan packet blocked;
- self-review blocked;
- R1 security card required scan result before done;
- onchain Quasar card with Auditor and scan packet reached ready and was then
  parked to avoid accidental dispatch.

Specific private board ids, task ids, paths and process ids are intentionally
not included in this public artifact.

## Remaining Risks

1. The adapter patch still needs a durable Hermes compatibility strategy.
2. The gate was proven through CLI/runtime paths; UI/API paths need their own
   compatibility tests if they can mutate Kanban state.
3. The factory needs multiple real-product pilots to calibrate field volume,
   cycle time and agent confusion.
4. Security scan execution is still a required contract; automatic scanner
   dispatch is a future hardening step.
5. Product Face validates required fields; screenshots, mobile and
   accessibility proof still need an automated worker.
6. Auditor is required for onchain work, but real Quasar source must be audited
   in implementation pilots.

## Decision

Factory 10 is accepted as a dry-pilot operational proof. The next version must
focus on public hygiene, worker operability, security-specialist depth, Hermes
update compatibility, AutoReview, Handoff, Remote Proof, Product Face proof and
multi-context validation.
