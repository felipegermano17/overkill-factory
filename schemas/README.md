# Schemas

Schemas are the machine contracts for public factory cards, packets, receipts,
gates and worker outputs.

## What Belongs Here

- JSON Schema files for canonical factory contracts.
- Public-safe schema versions paired with templates, tests or validation
  scripts.
- Contracts that scripts and adapters can enforce without relying on chat
  memory.

## What Does Not Belong Here

- Narrative explanations that should live in `docs/`.
- Generated examples, one-off outputs or partial mirrors of private schemas.
- Unused contract drafts without tests, templates or a clear owner.

## Source Of Truth

For machine validation, JSON Schema files are authoritative. Templates and docs
must follow the schema, not the other way around.

## Product Design System Contract

`project-design-system.schema.json` is the machine contract behind a project's
AI-readable `DESIGN.md`. It sits between Product Experience planning and
frontend implementation:

```text
product_experience_plan -> product_face_packet -> project_design_system / DESIGN.md
-> frontend_builder -> product_face_result
```

For vFinal product-facing work, `factoryctl validate-card` requires
`project_design_system` before implementation can be treated as ready.

## How It Is Validated

Run schema and public artifact checks:

```bash
python scripts/validate_public_json_artifacts.py
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
```
