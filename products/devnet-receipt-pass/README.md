# Devnet Receipt Pass

Devnet Receipt Pass is a small validation product for the factory line.

It proves that the factory can take a raw product paper, create a source of
truth, design an architecture, produce a visible product face, prepare an
onchain Quasar work package, run worker packets, collect evidence and close
with Receipt Five metadata.

The product intentionally uses read-only Solana devnet access. It does not
sign, deploy, write to devnet, write to mainnet, move funds, store keys or claim
a production onchain audit.

## Product Shape

- Offchain service: reads Solana devnet JSON-RPC and creates a deterministic
  receipt proof for one product event.
- Product Face: static dashboard showing receipt state, cluster state, disabled
  signing boundary and offline/error states.
- Onchain package: Quasar-oriented PDA receipt model for future implementation.
- Factory proof: worker packets, specialist results, human validation scope,
  transition plan and Receipt Five evidence.

## Safe Runtime Boundary

This validation can run with Node.js only. Missing Rust, Solana CLI or Quasar is
recorded as bounded evidence, not hidden. The Auditor worker remains mandatory,
but this pilot can only produce an Auditor preflight waiver until a real Quasar
toolchain and audited source are available.
