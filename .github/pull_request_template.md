## Summary
- What changed and why?

## Validation

```bash
python factory/scripts/quickstart_smoke.py
python -m unittest discover -s tests -p "test_*.py" -q
python factory/scripts/validate_document_governance.py
python factory/scripts/validate_public_json_artifacts.py
python factory/scripts/secret_safety_scan.py
python factory/scripts/public_safety_scan.py
```

## Public Boundary

- [ ] No secrets, private paths, private board links or raw private logs.
- [ ] No old pilot evidence, screenshots or narrative validation history added to the repo.
- [ ] New docs are about understanding or using the product.
