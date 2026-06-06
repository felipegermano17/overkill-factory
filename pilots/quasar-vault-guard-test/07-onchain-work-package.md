# F7 Onchain Work Package

## Runtime Constraint

Quasar is required. Anchor defaults are forbidden.

## Program Scope

A public product-like Quasar target now exists at
`pilots/quasar-vault-guard-test/onchain/qvg-product-like`. It implements the
dry proof shape for the factory and is used to exercise Quasar build/test and
Auditor code-audit contracts.

This is still not production source. It does not deploy, write chain state,
move funds, use wallet signing, handle custody or approve a real product.

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
| `review_vault_instruction` | Implemented in public product-like Quasar target. |
| `record_audit_receipt` | Implemented in public product-like Quasar target. |
| `block_instruction` | Implemented in public product-like Quasar target. |

## PDA Derivation

| PDA | Seeds |
| --- | --- |
| `vault_state` | `["vault", operator]` |
| `pending_instruction` | `["pending", vault_state]` |
| `audit_receipt` | `["audit", vault_state]` |

## CPI Allowlist

None in the pilot.

Any future CPI must be explicitly added to the onchain package and reviewed by
the Auditor Runner.

## Compute Budget

The product-like target passes Quasar build/test in a clean Docker container.
It does not yet include a production compute-unit budget or SVM client flow.
Future production implementation must include compute-unit thresholds before
ready.

## Auditor Path

Mandatory: `solanabr/Auditor`.

The public product-like target has a bounded Auditor `code_audit` result with
real corpus coverage, instruction matrix, state model and Quasar build/test
proof:

- `validation/quasar-product-like-proof/qvg-quasar-runtime-proof.json`
- `validation/quasar-product-like-proof/qvg-product-like-auditor-result.json`
- `validation/quasar-product-like-proof/qvg-product-like-auditor-report.md`

Boundary: this closes the public pilot gap between "preflight only" and
"code-audit contract exercised". It is not reusable as production approval.
