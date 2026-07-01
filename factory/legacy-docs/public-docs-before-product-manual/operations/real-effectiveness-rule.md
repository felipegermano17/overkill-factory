# Real effectiveness rule

A Kanban comment, Receipt Five entry, `done` transition, or phase advancement is process evidence only. It does not count as real progress unless a `real_effectiveness_proof` ties that ritual to at least one material effect:

- `product_progress`: a product/SOT/acceptance delta exists and is traced.
- `blocker_resolution`: a named blocker is resolved with evidence.
- `usable_artifact`: an operator/product artifact exists and has validation evidence.
- `human_delivery`: the right human/operator received a usable delivery artifact.
- `executable_repair`: executable code/runtime/config was repaired and validated.

Use `factory/templates/real-effectiveness-proof.json` as the starting packet and validate it with:

```sh
python factory/scripts/factoryctl.py validate-real-effectiveness factory/templates/real-effectiveness-proof.json
python factory/scripts/work_product_quality_firewall.py real_effectiveness factory/templates/real-effectiveness-proof.json
```

For cards that must enforce this boundary at done promotion, set `real_effectiveness_required: true` on the card or completion metadata and attach `real_effectiveness_proof` beside `receipt_five` and `kanban_transition_event`.

Process-only evidence belongs in `ritual_refs`; material evidence belongs in `evidence_refs` plus the effect-specific refs. If every evidence ref is just a comment, receipt, status/done transition, or phase move, validation fails closed.
