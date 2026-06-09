# Hermes CU/Fuzz/Property Summary

Worker profile: solana-quasar-auditor
Result: PASS

## Evidence refs

- validation/quasar-product-like-proof/qvg-quasar-runtime-proof.json
- validation/quasar-product-like-proof/qvg-quasar-cu-fuzz-property-proof.json
- validation/quasar-product-like-proof/qvg-product-like-auditor-result.json
- validation/quasar-product-like-proof/qvg-product-like-auditor-report.md
- validation/quasar-product-like-proof/hermes-cu-fuzz-property-summary.md

## Runtime proof source hash match

Status: PASS / matched

- runtime_source_sha256: d01eaf425d01e02480620cf1d18a27cc0833ff4246e14462794556ec117d67ed
- current_source_sha256: d01eaf425d01e02480620cf1d18a27cc0833ff4246e14462794556ec117d67ed
- matches: true

## Property/fuzz coverage

Total deterministic property/fuzz cases: 513

- hash_cases: 256 total, 255 accepted, 1 expected rejected, verdict PASS
- reason_code_cases: 256 total, 255 accepted, 1 expected rejected, verdict PASS
- client_flow_cases: 1 total, verdict PASS

## Compute profile boundary

The compute profile is static/symbolic only. It is not real production Solana CU measurement. The proof records profile_kind `static_symbolic_upper_bound`, real_solana_cu_measured `false`, and max_symbolic_upper_bound_units `40`; production source still needs real CU profiling and SVM/client transaction-flow measurement.

## Production boundary

This proof is not reusable for product approval, deploy, devnet/mainnet writes, signing, funds, or custody. It is bounded evidence for a public product-like QVG Quasar target only and does not claim production approval.

## Validation commands

1. `python3 scripts/quasar_product_like_container_proof.py --timeout-seconds 1200` -> PASS, wrote validation/quasar-product-like-proof/qvg-quasar-runtime-proof.json
2. `python3 scripts/qvg_quasar_cu_fuzz_property_proof.py` -> PASS, total_cases 513, wrote validation/quasar-product-like-proof/qvg-quasar-cu-fuzz-property-proof.json
3. `AUDITOR_DIR=$(mktemp -d); git clone --depth 1 https://github.com/solanabr/Auditor.git "$AUDITOR_DIR"; python3 scripts/qvg_product_like_auditor_result.py --auditor-dir "$AUDITOR_DIR"` -> PASS, wrote validation/quasar-product-like-proof/qvg-product-like-auditor-result.json and validation/quasar-product-like-proof/qvg-product-like-auditor-report.md
4. `python3 scripts/validate_public_json_artifacts.py` -> OK
5. `python3 scripts/public_safety_scan.py` -> OK
6. `python3 scripts/secret_safety_scan.py` -> OK
7. `python3 -m unittest discover -s tests -p "test_*.py" -q` -> OK, 59 tests run
