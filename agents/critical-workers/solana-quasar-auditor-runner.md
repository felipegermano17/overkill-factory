# Solana/Quasar Auditor Runner

## Purpose

Prepare or run the Auditor path for Solana/Quasar work.

## Enters

- F7 Onchain Package
- F13 Verification
- Before any real onchain promotion

## Input

- `onchain_work_package`
- Quasar source references
- account map
- instruction ABI
- PDA derivation
- CPI allowlist
- compute-unit budget
- authority/signing boundaries

## Output

- Auditor evidence refs
- onchain risk notes
- blocking findings
- waiver request when a human exception is needed

## Hermes Gate

R3/R4 onchain cards must require Auditor or a human waiver before `ready`.

## Hard Rule

Do not assume Anchor defaults. Factory onchain work uses Quasar.
