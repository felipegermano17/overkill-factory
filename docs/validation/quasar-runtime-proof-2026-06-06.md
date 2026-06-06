# Quasar Runtime Proof - 2026-06-06

Purpose: turn Quasar from a documentation assumption into a verified factory
runtime path.

## What Was Tested

Two containerized paths were tested in a clean Rust environment with the Solana
CLI installed:

1. `cargo install quasar-cli` from crates.io.
2. `cargo install --path cli` from `github:blueshift-gg/quasar` at
   `a89a9329f05740a20520607608b2b3b78c74f7c4`.

## Result

The crates.io path installed and generated a minimal project, but the generated
project failed `quasar build`. The factory must treat that path as weak
evidence until the public crate and docs are aligned.

The source-pinned path passed:

- `quasar init` with `--yes --toolchain solana --test-language rust
  --rust-framework quasar-svm --template minimal --no-git`;
- `quasar build`;
- `quasar test`.

Public receipts:

- `validation/quasar-real-proof/quasar-crates-proof-result.json`
- `validation/quasar-real-proof/quasar-source-proof-result.json`

## Factory Decision

For real Solana/Quasar `code_audit` claims, the factory now requires
`quasar_toolchain_proof` inside `auditor_result`.

That proof must include a source pin, versions, init/build/test commands,
build/test PASS and public evidence refs. This is stricter than accepting
`quasar --version` because a CLI can exist while its generated program path is
broken. It is also better than generic Rust compilation because Quasar has its
own scaffold, IDL and Solana build wrapper behavior.

## Boundary

This proves the Quasar source toolchain path can build and test a generated
minimal program. It still does not prove:

- a real product program was implemented;
- the real program's instructions, account model, PDAs or CPIs are safe;
- compute-unit profile, fuzz/property tests or economic attack analysis passed;
- Auditor completed a full product-specific code audit.

Those remain blocking gates for a real onchain product.
