# Hermes Full Product Worker Graph Review Summary

Review status: historical bounded PASS.

This summary records the earlier product-specific graph review before the final
production graph, remote proof and release-control lanes were completed. The
current final state is recorded in:

- `validation/production/full-product-worker-graph.md`
- `validation/completion/factory-10-completion-audit.md`
- `validation/hermes-live/practical-10-final-hermes-run.md`

This review inspected the staged QVG full product worker graph implementation and output:

- `scripts/full_product_worker_graph.py`
- `schemas/full-product-worker-graph.schema.json`
- `tests/test_full_product_worker_graph.py`
- `validation/product-specific/qvg-full-product-worker-graph.json`

## Findings

- The full product worker graph is stronger than isolated prooflets because it reconciles ten lanes into one product-specific public validation graph: Product Face, security scan, Auditor, CU/SVM/economic proof, remote proof, independent review, human gate, release ops, supply chain, and Receipt Five.
- At that stage, the graph remained bounded and did not claim production readiness: `reusable_for_product=false`, `completion_claim_allowed=false`, `reusable_for_product_lanes=2`, and the completion audit remained `NOT_COMPLETE`.
- At that stage, the graph kept four explicit production blockers: production CU/SVM/economic proof, managed Crabbox/Testbox remote proof, production release/R4 human gate, and a production product run with every remaining critical lane marked `reusable_for_product=true`.
- Stale Receipt Five references are preserved only as `stale_evidence_refs` on the `receipt_five` lane. They are visible for historical traceability and do not replace current lane evidence in the graph-level `evidence_refs` list.
- No managed Testbox, release, human approval, CU/SVM/economic, or production worker-graph evidence was inferred or invented.

## Validation commands run

- `python3 scripts/full_product_worker_graph.py --require-pass` -> exit 0, `PASS`
- `python3 scripts/factory_completion_audit.py` -> exit 0, `NOT_COMPLETE` at that stage
- `python3 scripts/factory_completion_audit.py --no-write --require-complete` -> exit 1, expected at that stage because completion remained blocked
- `python3 scripts/validate_public_json_artifacts.py` -> exit 0, `OK`
- `python3 scripts/public_safety_scan.py` -> exit 0, `OK`
- `python3 scripts/secret_safety_scan.py` -> exit 0, `OK`
- `python3 -m unittest discover -s tests -p "test_*.py" -q` -> exit 0, reported `OK`
- `git diff --check` -> exit 0

## Historical review decision

The staged graph was acceptable as a public, bounded, product-specific validation graph for QVG. It was not suitable for promotion as production readiness or practical 10/10 completion until the listed production blockers had current product-specific or provider-backed evidence and the completion audit changed from `NOT_COMPLETE` through the proper gate.

Those later completion conditions have since been closed by the production
graph and final Hermes V2 run listed above.
