# Production-like Product Face proof summary

## Scope

This summary covers the production-like Product Face lane for the QVG public validation product only.

The historical proof was limited to:

- product_id: `qvg-public-validation-product`
- environment_class: `production-like-static-artifact`
- approval_scope: `Product Face lane for the QVG public validation product only`
- target artifact: `pilots/quasar-vault-guard-test/product-face/prototype.html`

## Result

The Product Face proof is `PASS` and `evidence_kind=real` for browser/render evidence, but it is no longer reusable as product approval until packet comparison, source-promise coverage and design-fit review are recorded as `pass`.

Evidence:

- `validation/production/product-face/product-face-result.json`
- `validation/production/product-face/product-face-report.md`
- `validation/production/product-face/state.json`
- `validation/production/product-face/console.json`
- `validation/production/product-face/screenshots/desktop.png`
- `validation/production/product-face/screenshots/mobile.png`

The result records `product_target.product_id=qvg-public-validation-product`, `product_target.environment_class=production-like-static-artifact`, and a `product_target.target_sha256` for the target artifact. Its current `reusable_for_product=false` is intentional.

## Completion audit boundary

The completion audit now treats `production_product_face` as bounded until the alignment fields above pass.

This section captured the state immediately after the Product Face lane closed.
The later final Factory 10 run also closed Quasar Auditor, CU/SVM/economic,
remote proof, release-control and production graph lanes. Current final status
is recorded in:

- `validation/completion/factory-10-completion-audit.md`
- `validation/production/full-product-worker-graph.md`
- `validation/hermes-live/practical-10-final-hermes-run.md`

At that moment, Product Face did not clear the then-remaining product blockers:

- `production_quasar_auditor`
- `production_cu_svm_economic`
- `managed_remote_proof`
- `production_release_human_gate`
- `full_product_specific_worker_graph`

The full practical-completion claim remained blocked until those lanes later
received product-specific or provider-backed evidence.

Audit evidence:

- `validation/completion/factory-10-completion-audit.json`
- `validation/completion/factory-10-completion-audit.md`

## Validation commands

Passed:

- `python -m unittest tests.test_product_face_proof -q`
- `python scripts/product_face_proof.py --target pilots/quasar-vault-guard-test/product-face/prototype.html --out validation/production/product-face/product-face-result.json --viewport desktop=1440x900 --viewport mobile=390x844 --state initial-render --state product-specific-production-like-static-artifact --journey "open QVG production-like static target" --journey "inspect status, gate copy and evidence affordances" --card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md`
- `python scripts/validate_public_json_artifacts.py`
- `python scripts/public_safety_scan.py`
- `python scripts/secret_safety_scan.py`
- `python scripts/factory_completion_audit.py --no-write`
- `git diff --check`

Expected blocking result at the time:

- `python scripts/factory_completion_audit.py --no-write --require-complete`
  returned `NOT_COMPLETE` because the five blockers above remained.

Current verifier probe must also confirm `--reusable-for-product` rejects missing packet comparison, source-promise coverage and design-fit review before it can set `reusable_for_product=true`.
