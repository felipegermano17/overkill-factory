# Production Full Product Worker Graph

Result: `FAIL`
Reusable for product: `false`

## Lanes

- `hermes_orchestration`: `PASS` via `validation/hermes-live/multi-profile-dispatch-summary.md`
- `product_face`: `FAIL` via `validation/production/product-face/product-face-result.json`
- `security`: `PASS` via `validation/security/codex-security-full-scan-2026-06-06.md`
- `quasar_auditor`: `PASS` via `validation/production/quasar/auditor-result.json`
- `cu_svm_economic`: `PASS` via `validation/production/quasar/cu-svm-economic-proof.json`
- `remote_proof`: `PASS` via `validation/production/remote-proof/managed-testbox-result.json`
- `human_gate`: `PASS` via `validation/production/release/human-gate-record.json`
- `release_ops`: `PASS` via `validation/production/release/release-ops-result.json`
- `supply_chain`: `PASS` via `validation/supply-chain/supply-chain-proof.json`

## Blocking

- product_face: strict lane must be reusable_for_product=true; strict Product Face lane requires packet_comparison.status=pass; strict Product Face lane requires source_promise_coverage.status=pass; strict Product Face lane requires design_fit_review.status=pass; strict Product Face lane requires packet_ref
