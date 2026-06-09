# Verification Summary

Commands run in this Factory 13 validation pass:

- `node products/devnet-receipt-pass/offchain/receipt-service.mjs products/devnet-receipt-pass/offchain/devnet-read-proof.json`: PASS.
- `node products/devnet-receipt-pass/offchain/receipt-service.mjs pilots/devnet-receipt-pass-factory13-test/devnet/devnet-read-proof.json`: PASS.
- `python scripts/product_face_proof.py --target local HTTP dashboard`: PASS.
- `python scripts/factoryctl.py validate-card pilots/devnet-receipt-pass-factory13-test/cards/drp-factory13-builder-pilot.md`: PASS.
- `python scripts/factoryctl.py gate-report --card ...`: PASS.
- `python scripts/factoryctl.py worker-packet --worker all --required-only --card ...`: PASS.
- `python scripts/factoryctl.py validate-receipt ...`: PASS.
- `python scripts/factoryctl.py validate-completion --card ... --receipt ...`: PASS.
- `python scripts/factoryctl.py transition-plan --enforce ...`: PASS.
