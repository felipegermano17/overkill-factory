# Security Coverage Ledger

Scope: Devnet Receipt Pass Factory 13 builder-layer validation.

| Surface | Disposition | Evidence |
| --- | --- | --- |
| Public artifact hygiene | closed-pass | `python scripts/public_safety_scan.py` |
| Secret exposure | closed-pass | `python scripts/secret_safety_scan.py` |
| Read-only devnet RPC | closed-pass | product and pilot devnet proof JSON |
| Product Face | closed-pass | desktop/mobile screenshots through local HTTP |
| Dashboard integration | closed-pass | dashboard fetches product proof JSON |
| API/backend surface | closed-pass | offchain receipt service generated deterministic proof |
| Data persistence | bounded-pass | file-based JSON proof persistence only |
| Signing/keys/custody | closed-blocked | card forbids signing, keys, custody and funds |
| Quasar/onchain build | closed-waived | no Solana/Quasar/Rust/Docker toolchain available |
| Quasar/onchain QA | closed-waived | no write-capable toolchain or SVM proof in this runtime |
| Supply chain | closed-pass | no package install or dependency lock change |

Conclusion: no blocking finding exists for the validation scope. This ledger
does not approve production, deploy, signing, write access, keys or funds.
