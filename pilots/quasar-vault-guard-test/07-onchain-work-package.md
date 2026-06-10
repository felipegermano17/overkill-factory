# F7 Onchain Work Package

## Runtime Constraint

Quasar is required. Anchor defaults are forbidden.

## Program Scope

No program code is implemented in this pilot. This package defines the minimum
shape that a later Quasar program card must satisfy.

## Accounts

| Account | Purpose | Authority |
| --- | --- | --- |
| `vault_state` | Holds vault status and policy hash. | example vault authority. |
| `operator_identity` | Links operator wallet to allowed action review. | Human-approved operator. |
| `pending_instruction` | Represents instruction candidate being reviewed. | Read-only in pilot. |
| `audit_receipt` | Stores hash/reference of Auditor evidence when real program exists. | Security owner. |

## Instruction ABI

| Instruction | Pilot Status |
| --- | --- |
| `review_vault_instruction` | Defined only. Not implemented. |
| `record_audit_receipt` | Defined only. Not implemented. |
| `block_instruction` | Defined only. Not implemented. |

## PDA Derivation

| PDA | Seeds |
| --- | --- |
| `vault_state` | `["vault", vault_id]` |
| `pending_instruction` | `["pending", vault_id, instruction_hash]` |
| `audit_receipt` | `["audit", vault_id, receipt_hash]` |

## CPI Allowlist

None in the pilot.

Any future CPI must be explicitly added to the onchain package and reviewed by
the Auditor Runner.

## Compute Budget

Not measured in pilot. Future implementation must include compute-unit budget
and failure thresholds before ready.

## Auditor Path

Mandatory: `solanabr/Auditor`.

Current limitation: there is no Quasar source code to audit yet. Therefore the
Auditor result is a preflight readiness report, not a code-audit pass.
