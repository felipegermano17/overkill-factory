# Auditor + Quasar Source Resolution - 2026-06-06

> Document status: HISTORICAL EVIDENCE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This is not the current factory rule; it records a source-resolution decision about Quasar/Auditor scope.

Purpose: decide what the factory can honestly claim about Solana/Quasar
Auditor evidence.

## Source Resolution

Quasar is a real Solana/SVM program framework, not the Vue UI framework. The
official Quasar docs describe it as a Solana program development framework for
SVM programs, with `#![no_std]` programs, `#[program]`, `#[account]`,
`#[derive(Accounts)]`, account constraints, PDA support, build/test/deploy
commands and CU profiling.

Primary public references:

- https://quasar-lang.com/docs
- https://quasar-lang.com/docs/getting-started/quickstart
- https://quasar-lang.com/docs/guides/build-a-vault
- https://quasar-lang.com/docs/references/cli
- https://quasar-lang.com/docs/getting-started/installation

The Quasar docs also show that a real build path needs a Rust/Solana/Quasar
toolchain. The host runtime did not expose `cargo`, `rustc` or `quasar`, so the
factory used a clean container proof instead of pretending the host was ready.
That proof found an important source conflict: the crates.io CLI path generated
a project that did not build, while the source-pinned `blueshift-gg/quasar`
path passed `quasar init`, `quasar build` and `quasar test`.

Auditor is not an executable CLI. It is a security-audit skill/corpus: a
structured set of markdown instructions, checklists, discovery commands,
templates and known attack vectors. Correct use requires loading the Auditor
corpus, walking target files, applying item-level checklist verdicts and
recording known-vector coverage. A summary-only "Auditor passed" statement is
not valid evidence.

Primary public reference:

- https://github.com/solanabr/Auditor

## Factory Decision

The factory must keep the current dry-pilot Auditor record as `preflight` or
`WAIVED`, not `PASS`, until there is real Quasar source and a real Auditor code
audit report.

This is better than accepting a shallow preflight because onchain work can look
complete while the riskiest part, the program itself, has never been read. It is
also better than requiring a generic "security review" because Auditor has
Solana-specific account, signer, PDA, CPI, arithmetic, economic-logic,
governance and known-vector coverage.

## Contract Change

`auditor_result` with `audit_mode=code_audit` now requires:

- at least 120 Auditor corpus files loaded;
- program checklist coverage for checklists 01-07;
- at least 100 known vectors covered;
- non-empty instruction matrix;
- non-empty state model;
- explicit `findings` array, which may be empty for a clean audit;
- explicit `waivers` array, which may be empty when no waiver exists.
- explicit `quasar_toolchain_proof` with source pin, versions, init/build/test
  commands, build PASS, test PASS and evidence refs.

Synthetic smoke remains allowed only as `evidence_kind=synthetic` and
`reusable_for_product=false`. It cannot be reused as product approval.

Public Quasar runtime receipts are recorded in:

- `docs/validation/quasar-runtime-proof-2026-06-06.md`
- `validation/quasar-real-proof/quasar-crates-proof-result.json`
- `validation/quasar-real-proof/quasar-source-proof-result.json`

Later hardening added a public product-like QVG Quasar target:

- `pilots/quasar-vault-guard-test/onchain/qvg-product-like/src/lib.rs`
- `pilots/quasar-vault-guard-test/onchain/qvg-product-like/src/tests.rs`

Hermes then ran a real `solana-quasar-auditor` worker against a clean public
clone. That worker produced:

- `validation/quasar-product-like-proof/qvg-quasar-runtime-proof.json`
- `validation/quasar-product-like-proof/qvg-product-like-auditor-result.json`
- `validation/quasar-product-like-proof/qvg-product-like-auditor-report.md`
- `validation/quasar-product-like-proof/hermes-qvg-code-audit-summary.md`

This is no longer preflight-only for the public pilot. It is a bounded
`code_audit` PASS over product-like public source. It is still not reusable as
production product approval.

## Remaining Gate To Reach Real Nota 10

1. Replace the public product-like target with real production Quasar source
   when a production product exists.
2. Add production compute-unit profiling and SVM/client flow coverage.
3. Rerun Auditor over production source with corpus coverage, checklist
   coverage, instruction matrix, state model, known-vector results and
   findings.
4. Attach the production Auditor report as `auditor_result audit_mode=code_audit`.
5. Keep promotion blocked if production Auditor is preflight, synthetic or
   waived without explicit human risk ownership.
