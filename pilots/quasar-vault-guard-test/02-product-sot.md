# F2 Product SOT

## Product Definition

Quasar Vault Guard is a safety dashboard for reviewing a Solana vault action
before execution.

It answers one operational question:

```text
Is this vault instruction safe enough to proceed, blocked, or unknown?
```

## Primary User

Overkill operator reviewing sensitive vault/account actions.

## First Slice

Create the visible Product Face prototype and the first Hermes card proving:

- source material was resolved;
- Product Face Packet exists;
- onchain package exists;
- security scan packet exists;
- worker packets exist;
- evidence records exist;
- Receipt Five can close the slice.

## Non-Goals

- No Solana program implementation.
- No Quasar compile.
- No devnet or mainnet writes.
- No wallet signing.
- No production release.
- No custody action.

## Product States

| State | Meaning |
| --- | --- |
| Loading | Vault/account data is being prepared. |
| Unknown | Inputs are incomplete or conflict. |
| Safe | No blocking issue in current evidence. |
| Blocked | Security, Auditor, or human gate blocks execution. |
| Simulation Failed | The proposed action cannot be simulated safely. |
| Wallet Rejected | User rejected wallet action. |

## Success Criteria

- A human can understand the product path from paper to first slice.
- A Hermes agent can execute a bounded card without guessing authority.
- Product Face evidence exists before completion.
- Onchain work is treated as Quasar-specific and Auditor-bound.
- Security evidence is structured and not reduced to prose.

## Authority

This SOT authorizes a dry pilot only. It does not authorize network writes,
funds, custody, signing, deploys, or production changes.
