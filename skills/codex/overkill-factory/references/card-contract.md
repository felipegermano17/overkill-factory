# Card Contract

## Factory Card Required Fields

Factory 10 cards must include:

- `factory_method_version`
- `phase`
- `surfaces`
- `risk_initial`
- `risk_effective`
- `authority_max`
- `owner_worker`
- `executor_identity`
- `reviewer_identity`
- `runtime_decision`
- `runtime_contract`
- `security_contract`
- `forbidden_actions`
- `done_definition`
- `transition_event_required`
- `kanban_transition_event_ref`

## Conditional Packets

Product Face Packet is required for:

- `ux`
- `frontend`
- `mobile`
- `wallet-ui`

Onchain Work Package is required for Solana/Quasar/account/PDA/CPI/CU/funds
surfaces.

Security Scan Packet is required for:

- R3
- R4
- onchain
- security/cybersecurity/prompt-injection/agent-runtime/supply-chain/secrets/IAM/DNS/KMS

R4 Gate is required for R4 production-critical work.

## Receipt Five

Done requires:

1. `changed`
2. `artifact_paths`
3. `verification_commands`
4. `verification_result`
5. `next_action`

If review is required, include `reviewer_result`.

Also include `kanban_transition_event` with:

- `from_status`
- `to_status`
- `actor`
- `worker`
- `receipt_refs`
- `artifact_refs`
