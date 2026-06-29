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

## Factory V2 Control Contracts

The V2 line is enforced by schemas, not agent memory. The core control-plane
schemas are:

- `factory-phase-graph.schema.json`: canonical product phases plus non-product
  event/view aliases.
- `v2-study-traceability.schema.json`: raw-study claim to bounded truth level,
  evidence, known gaps and next action.
- `v2-doc-implementation-obligations.schema.json`: doc-vs-code parity ledger
  that prevents documented V2 obligations from being overclaimed as
  implemented.
- `worker-authority-contract.schema.json`: worker profiles cannot own route,
  gate, waiver or promotion decisions.
- `product-experience-control-plane.schema.json`: design, brand, frontend,
  operator UX and Product Face as governed product surfaces.
- `capability-acquisition-contract.schema.json`: search/create/install/evaluate
  capability before missing specialists can block.
- `hermes-reducer-mutation-proof.schema.json`: Hermes Kanban remains the
  mutation authority.
- `factory-v2-readiness-claim.schema.json`: readiness claims are scoped and
  cannot jump from kernel proof to production proof.
- `runtime-contract.schema.json` and `security-contract.schema.json`: embedded
  card contracts for execution authority, runtime boundary, security owner,
  secret policy and evidence refs.
- `onchain-work-package.schema.json` and
  `solana-ai-kit-usage-receipt.schema.json`: Solana work must carry signer,
  auditor and Solana AI Kit evidence instead of prose-only mentions.

## How It Is Validated

Run schema and public artifact checks:

```bash
python scripts/factoryctl.py validate-v2-study-traceability templates/v2-study-traceability.json
python scripts/factoryctl.py validate-v2-doc-implementation-obligations templates/v2-doc-implementation-obligations.json --traceability templates/v2-study-traceability.json
python scripts/factoryctl.py validate-worker-authority-contract templates/worker-authority-contract.json
python scripts/factoryctl.py validate-product-experience-control-plane templates/product-experience-control-plane.json
python scripts/validate_public_json_artifacts.py
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
```
