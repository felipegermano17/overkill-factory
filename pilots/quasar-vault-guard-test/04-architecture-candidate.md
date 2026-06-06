# F4 Architecture Candidate

## System Shape

```text
Raw Paper
-> Product SOT
-> Product Face Prototype
-> Quasar Onchain Work Package
-> Security Scan Packet
-> Hermes Card
-> Worker Packets
-> Evidence Records
-> Receipt Five
```

## Components

| Component | Responsibility | Risk |
| --- | --- | --- |
| Product Face Prototype | Shows vault action status, wallet state, risk summary, and evidence. | R2 visible product surface. |
| Onchain Work Package | Describes Quasar accounts, PDA, CPI, compute, and authorities. | R3 financial/onchain surface. |
| Security Scan Packet | Defines scan timing, scope, acceptance, and blocking policy. | R3 security-sensitive surface. |
| Hermes Kanban Card | Carries executable bounded work. | R2/R3 process authority. |
| Worker Packets | Route required specialists. | R2 execution-control surface. |
| Receipt Five | Closes work with evidence. | R2 process integrity surface. |

## Runtime

Hermes is the factory floor. Codex creates and validates artifacts; Hermes
records the pilot card, comments, and completion evidence.

## Security Boundary

The pilot is docs/prototype only. The architecture explicitly forbids:

- key access;
- wallet signing;
- devnet writes;
- mainnet writes;
- deploys;
- custody or funds movement;
- production release.

## Why This Architecture Is Better Than A Full Build

A full build would test implementation speed, not the factory. This pilot tests
whether the factory can convert ambiguous paper into controlled agent work with
gates, evidence, and no authority leakage.
