# Verification Summary

Commands already run in this validation pass:

- `node products/devnet-receipt-pass/offchain/receipt-service.mjs`: PASS, produced read-only devnet proof.
- `python scripts/factoryctl.py validate-card pilots/devnet-receipt-pass-test/cards/drp-full-line-pilot.md`: PASS.
- `python scripts/factoryctl.py gate-report --card pilots/devnet-receipt-pass-test/cards/drp-full-line-pilot.md --out pilots/devnet-receipt-pass-test/evidence/gate-report-full-line.json`: PASS.
- `python scripts/factoryctl.py worker-packet --worker all --card pilots/devnet-receipt-pass-test/cards/drp-full-line-pilot.md --out pilots/devnet-receipt-pass-test/worker-packets`: PASS, generated 27 worker packets.
- `python scripts/product_face_proof.py ...`: PASS, captured desktop and mobile screenshots.
- `python scripts/public_safety_scan.py`: PASS.
- `python scripts/secret_safety_scan.py`: PASS.
- `python scripts/validate_worker_profiles.py`: PASS.
- `python -m unittest discover -s tests -p "test_*.py" -q`: PASS, 105 tests.
