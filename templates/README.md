# Templates

Templates are starter contract files paired with schemas and tests.

## What Belongs Here

- Public card, gate, receipt, plan and result templates.
- Minimal JSON or Markdown starting points that match schemas.
- Templates that help an operator create a valid factory artifact faster.

## What Does Not Belong Here

- Finished decisions, approval records or evidence from real work.
- Generated run output or private product material.
- Templates without matching schemas, tests or documentation.

## Source Of Truth

Templates are examples of valid shape. Schemas and validation scripts decide
whether an artifact is acceptable.

## Frontend And Product Surfaces

For product-facing/frontend work, start from:

- `product-experience-plan.json` for user, job, states and proof needs.
- `product-face-packet.json` for visible surface coverage.
- `project-design-system.json` for the project-level design contract.
- `DESIGN.md` as the AI-readable export that coding agents can consume.
- `professional-design-process.json` for reference research, gates and review.

`DESIGN.md` is not an approval by itself. It must match
`project_design_system`, and Product Face still has to prove the rendered
surface against the packet, design system and professional design process.

## Public Runtime Refs

Public templates and generated public artifacts must never contain raw Hermes
Kanban task IDs. Use stable issue refs such as `github-issue-example`, semantic
artifact refs, or `kanban:<redacted>` when private runtime traceability exists
only in Hermes.

## How It Is Validated

Run template and schema checks:

```bash
python scripts/validate_public_json_artifacts.py
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
```
