# Worker Roster

This roster names factory workers at process level. It does not define prompts,
personalities, or provider configuration.

## Source Cartographer

Enters at F0-F1. Builds the source ledger, separates source from inference, and
marks conflicts.

## Product SOT Architect

Enters at F2-F3. Converts source and answers into the Product Source of Truth.

## Product Architect

Enters at F4. Creates the architecture candidate from the SOT.

## Product Face Designer

Enters at F5. Defines screens, states, wallet flows, breakpoints,
accessibility, performance budget, and visual evidence plan.

## Solana/Quasar Architect

Enters at F7. Defines accounts, instruction ABI, PDA derivation, CPI allowlist,
compute-unit budget, signer/authority boundaries, and Auditor route.

## Codex Security Runner

Enters at F8 and F13. Runs Codex Security/Cybersecurity scans when the card's
security scan packet requires it.

## Auditor Runner

Enters at F7 and F13 for onchain work. Runs or prepares `solanabr/Auditor`
evidence for Solana/Quasar work.

## Documentation Operator

Enters at F10. Turns approved architecture into durable specs, decisions,
diagrams, contracts, and evidence paths.

## Decomposition Planner

Enters at F11. Produces the gated Hermes card graph.

## Implementation Worker

Enters at F12. Executes bounded cards only.

## Verification Worker

Enters at F13. Runs tests, screenshots, scans, and domain checks.

## Independent Reviewer

Enters at F14. Reviews work produced by another worker. Cannot be the executor.

## Human Gate Clerk

Enters at F9 and F15. Prepares approval packets and records human decisions.

## Release Operator

Enters at F16-F17. Handles promotion, rollback readiness, monitoring, and
post-release evidence.

## Factory Critic

Enters at F18. Looks for weak points, excessive complexity, ambiguity, and
agent misinterpretations before the next factory version.
