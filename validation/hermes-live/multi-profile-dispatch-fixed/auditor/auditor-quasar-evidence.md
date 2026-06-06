# Auditor / Quasar evidence — fixed multi-profile dispatch

Created: 2026-06-06T11:45:24Z
Worker: solana-quasar-auditor
Card: pilots/quasar-vault-guard-test/cards/qvg-first-slice.md
Result boundary: real Hermes worker operational preflight, not a product code audit, not reusable as product approval.

## 1. Product Quasar source availability

Observed public repo HEAD: 9659e17a07d2a5c3b9d6d605bad28c81eed80a44.

I checked the assigned public Overkill Factory clone for real product Quasar/Solana program source. The repo currently contains factory cards, validation artifacts, Product Face/static pilot assets, Quasar runtime proof receipts, and generated-minimal Quasar proof records, but no product Quasar program source.

Source-like file count observed in the repo scan:

- Rust source files (`*.rs`): 0
- Cargo manifests (`*.toml`): 0
- TypeScript source files (`*.ts`, `*.tsx`): 0
- Move/Solidity files (`*.move`, `*.sol`): 0
- HTML prototype files (`*.html`): 3
- JSON factory/validation files (`*.json`): 304
- Markdown factory/docs files (`*.md`): 117

Quasar/QVG-named material exists, but it is documentation, worker packets, validation receipts, screenshots, schemas, and pilot cards. The static pilot and generated minimal Quasar proof are useful factory/runtime evidence, but they are not product-specific Quasar source and are not enough for product safety.

Relevant existing proof boundary already stated by the repo:

- `docs/validation/quasar-runtime-proof-2026-06-06.md` says the source-pinned Quasar toolchain built/tested a generated minimal program, but does not prove a real product program was implemented or audited.
- `docs/validation/auditor-quasar-source-resolution-2026-06-06.md` says Auditor evidence must remain preflight/WAIVED until real Quasar source and a real Auditor code audit report exist.

Conclusion: real product Quasar source is absent in this public repo at the observed head.

## 2. Auditor source inspected

Auditor source inspected from: https://github.com/solanabr/Auditor
Observed Auditor HEAD from fresh clone: 38ceb3fabc811d62e1d6172bd23e110af502d8e6

No secrets, deploys, signing, devnet/mainnet writes, custody actions, or funds movement were performed.

## 3. Auditor corpus counts available

Fresh Auditor corpus clone counts:

- Total files: 131
- Markdown corpus files: 131
- `known-vectors/*.md` files: 101
- `checklists/*.md` files: 18
- Program checklist files 01-07 available: yes
  - `checklists/01-program-account-validation.md`
  - `checklists/02-program-access-control.md`
  - `checklists/03-program-arithmetic-safety.md`
  - `checklists/04-program-cpi-pda.md`
  - `checklists/05-program-state-machine.md`
  - `checklists/06-program-economic-logic.md`
  - `checklists/07-program-opsec-governance.md`

These counts prove the Auditor corpus path was operationally inspectable in the real Hermes worker dispatch. They do not prove product-specific checklist application because there is no product Quasar source to audit.

## 4. Coverage possible now

Coverage possible now:

- Auditor corpus availability preflight: yes.
- Product-specific Quasar code audit: no.
- Instruction matrix: blocked; no product instructions exist in source.
- State model: blocked; no product accounts/state structs exist in source.
- Known-vector coverage against target code: blocked; no product target code exists.
- Quasar product build/test/profile evidence: blocked; only generated-minimal runtime proof exists.

Because real product Quasar source is absent, any claim of Auditor PASS or `audit_mode=code_audit` would be misleading. This worker result must remain WAIVED/preflight and not reusable for product work.

## 5. Commands executed for this evidence

```bash
pwd && git rev-parse --show-toplevel && git rev-parse HEAD && git status --short
python3 scripts/factoryctl.py --help
python3 scripts/factoryctl.py evidence-record --help
# repo source scan with Python pathlib
# fresh clone and count of https://github.com/solanabr/Auditor
```

The bounded worker-result command is recorded in `validation/hermes-live/multi-profile-dispatch-fixed/auditor/auditor_result.json`.

## 6. Next action

Provide or scaffold real product Quasar source. Then run Quasar build/test/profile against that product program and run Auditor over the real source with corpus files, checklists 01-07, known-vector coverage, instruction matrix, state model, findings/waivers, and Quasar toolchain proof attached before any product code-audit claim.
