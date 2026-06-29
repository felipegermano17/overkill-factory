# Product Validation Fixtures

These are advanced product-shaped fixtures used by strict validators and
production-lane tests. They are not public products, not onboarding examples and
not source-of-truth product pipelines.

## What Belongs Here

- Small, public-safe targets needed to exercise production-scoped validators.
- Domain-specific fixtures, including Quasar/Solana, only when tests or scripts
  require realistic structure.
- Stable fixture ids kept for regression compatibility.

## What Does Not Belong Here

- Private product material, generated evidence, old pilot output or runtime
  archives.
- A public product catalog or examples intended as the first user path.
- Claims that a fixture proves readiness for another product.

## Source Of Truth

Schemas, scripts and tests decide whether these fixtures are valid. The public
first-run path remains `examples/minimal-hermes-project/`, and real execution
state remains in Hermes plus Receipt Five.

## How It Is Validated

```bash
python scripts/validate_public_json_artifacts.py
python -m unittest tests.test_qvg_public_defaults tests.test_factory_completion_audit tests.test_production_full_product_worker_graph -q
```
