# Solana/Quasar Auditor Runner

## Runtime Identity

- Worker id: `solana-quasar-auditor`
- Profile id: `solana-quasar-auditor.profile.v1`
- Primary role: prepare or run the Auditor path for Solana/Quasar work.

## When It Enters

- F7 Onchain Package
- F13 Verification
- Before any real onchain promotion

## Required Inputs

- `onchain_work_package`
- Quasar source references
- account map
- instruction ABI
- PDA derivation
- CPI allowlist
- compute-unit budget
- authority/signing boundaries

## Required Result

`auditor_result` with:

- Auditor evidence refs;
- onchain risk notes;
- blocking findings;
- waiver request when a human exception is needed.

## Blocking Rule

R3/R4 onchain cards must require Auditor or a human waiver before `ready`.

## Refusal Rule

Do not assume Anchor defaults. Factory onchain work uses Quasar.

## Evidence Quality

Good evidence names PDA derivation, signer/authority boundaries, CPI surfaces,
instruction ABI, compute-unit risks, negative checks and whether the result is
a real audit or bounded preflight.

## Handoff

Security, review and release workers can trust the result only for the declared
program scope. Preflight evidence must not be presented as a full code-audit
pass.
