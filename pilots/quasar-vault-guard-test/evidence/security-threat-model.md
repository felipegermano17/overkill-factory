# Security Threat Model

## Assets

- Future KAXIS vault authority.
- Future Quasar program.
- Operator wallet identity.
- Human approval trail.
- Factory evidence chain.
- Hermes Kanban state.

## Trust Boundaries

- Raw product paper to Product SOT.
- Product SOT to architecture.
- Architecture to decomposition.
- Codex artifacts to Hermes Kanban.
- Worker packet to worker result.
- Human authorization to human gate record.

## Attacker-Controlled Or Risky Inputs

- Messy raw paper.
- Prompted agent interpretation.
- Future wallet/account input.
- Future instruction hash.
- Future PDA/account map.
- Future security or Auditor reports.

## Invariants

- Dry pilot must not become production authority.
- No wallet signing.
- No secret access.
- No devnet/mainnet write.
- Auditor preflight must not be represented as code-audit pass.
- Human gate must cite real authorization and remain scoped.
- Receipt Five must include evidence refs.
