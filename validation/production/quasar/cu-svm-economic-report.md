# QVG Production CU/SVM/Economic Proof

Result: `PASS`
Source: `products/qvg-public-validation-product/onchain/quasar/src`
Source SHA-256: `c93325bc062bf1b0ad7ddefd114d5f3c906c34f4c7084afa9b65ed521fd4cc2b`
Real CU measured: `true`
Compute budget: `200000`

## Instruction CU

- `review_vault_instruction`: `1501` CU, within budget `true`
- `record_audit_receipt`: `1121` CU, within budget `true`
- `block_instruction`: `779` CU, within budget `true`

## Economic Boundary

This QVG validation program validates PDA/account inputs and rejects empty hashes/reason codes; it performs no CPI, token operation, lamport transfer, authority mutation or persistent write.

## Policy

This closes the QVG production-validation CU/SVM/economic lane only for the named source hash. Release, provider remote proof, human R4 gate and full production graph remain separate gates.
