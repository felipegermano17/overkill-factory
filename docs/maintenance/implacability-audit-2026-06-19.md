# Overkill Factory Implacability Audit - 2026-06-19

> Document status: LOCAL AUDIT ARTIFACT.
> Scope: proportional process, executable evidence, and gated self-improvement.
> Public/private boundary: no private dogfooding logs, board ids, local paths or screenshots are included.

## Executive Verdict

Overkill Factory is plausible as a control system, but only while it fails
closed on weak evidence and keeps process weight proportional to risk. The
current public repo already has strong foundations: capability packs, worker
permissions, Product Face validation, readiness scorecards, learnback records,
inactive learning proposals and public-safety scans.

The audit found five immediate hardening gaps that could make the factory feel
implacable in prose but weaker in execution:

1. Bounded remediation could be declared without a finite attempt/time/stop
   budget.
2. Product Face residuals could be accepted for a narrow review boundary and
   still be consumed as final product completion without a final disposition.
3. Repair-required Product Face residuals could lack a materialized repair
   loop.
4. Kanban artifact evidence could remain comment/path-level instead of proving
   durable attachment readback.
5. Product progress could be shown as manual or board-count optimism instead of
   runtime-gate projection.

These gaps are now covered by failing-then-passing tests and local code changes.

## Issue Inventory Reviewed

| Issue | Audit Mapping | Status In This Branch |
| --- | --- | --- |
| #382 Route Product Face residuals back to repair before product completion | Directly addresses executable evidence and avoiding permanent caveats. | Hardened: final completion now requires residual disposition and a materialized Hermes Kanban repair loop for `repair_required` residuals. |
| #385 Add native Kanban attachment producer/readback contract | Evidence transport gap: files must become durable runtime evidence, not local-only artifacts. | Hardened: native `kanban-attachment:` refs require durable readback proof, blob/size/hash checks, parse status, safety scans and held-card hydration when applicable. |
| #386 Add runtime-backed product process projection with completion percent | Operator projection gap: progress must come from runtime/gates, not manual estimates. | Hardened: projection completion percent is derived from runtime gates and rejects board-count/manual completion claims for release, production and closed states. |
| #387 Fail closed when Product Face selects stale or legacy surfaces | Source-authority gap: name similarity is not authority. | Hardened: final Product Face completion requires source-authority binding to the active SOT/source-resolution packet and rejects stale/reference/unrelated surfaces unless SOT-promoted. |
| #389 Require Product Face scope coverage before product completion | Scope-coverage gap: current-bound surface can still under-cover active SOT. | Hardened: final Product Face completion requires active Product SOT scope coverage, with partial/blocked items failing closed and deferrals requiring authority refs. |

## Audit Findings

### 1. Proportional Process By Risk

The design is directionally sound: `factory-workflow.catalog.json`,
capability packs and risk tiers let small work avoid the full heavy path while
material product, security, infra, release and onchain work get stronger gates.

The main operational risk is not lack of phases; it is overusing the full path
for low-risk work. The repo should continue treating Method Router output and
`gate-report` as the authority for process weight. Manual operator pressure or
copy-pasted templates must not turn every card into a maximum-rigor card.

Current evidence:

- `docs/factory-workflow.catalog.json` has phase-specific entry conditions,
  blocked actions and allowed next actions.
- `agents/capability-packs.public.json` distinguishes `core_ready`,
  `pack_template` and `blocked_until_installed`.
- `schemas/factory-readiness-scorecard.schema.json` and
  `validate_factory_readiness_scorecard()` prevent material autonomy when
  remediation is still required.

Local hardening:

- Remediation loops now require finite bounds before the scorecard validates:
  `max_remediation_attempts`, `timeout_minutes` and `stop_condition`.

### 2. Executable Evidence Over Pretty Documents

The strongest evidence surfaces are executable: `factoryctl validate-card`,
`gate-report`, `validate-completion`, Product Face result validation, public
JSON validation, public-safety scan and secret scan.

The weak spot is where a bounded review caveat can become final-product
acceptance. That is exactly the risk behind issue #382.

Local hardening:

- `validate_product_face_result()` still allows bounded
  `PASS_WITH_RESIDUALS` for a narrow Product Face result.
- `validate_product_face_result_against_card()` now fails final product
  completion unless each residual has a final `completion_disposition`.
- `repair_required` and `blocked_with_owner` block final product completion.
- `accepted_by_human_gate` requires a public-safe `human_gate_ref`.
- `out_of_scope_with_rationale` requires a public-safe rationale.
- When active Product SOT scope exists, `scope_coverage_matrix` must account for
  each approved SOT requirement before final Product Face completion.
- `partial` and `blocked` Product Face scope items fail closed; SOT or
  human-gate authorized deferrals must carry a public-safe authority ref.

This keeps residuals useful as review evidence without letting them become
quiet permanent caveats.

### 3. Gated Self-Improvement Without Infinite Loops

The self-improvement model is mostly conservative: learnback produces records,
issue candidates and inactive learning proposals. It does not dispatch Hermes,
activate workers, post GitHub comments, approve gates or mutate critical
factory behavior by itself.

The missing executable invariant was loop finiteness. A remediation loop must
state when it stops, not only that it is bounded.

Local hardening:

- Readiness scorecards now fail closed when remediation is required but finite
  loop controls are missing.
- The public template sets `max_remediation_attempts=2`,
  `timeout_minutes=90` and a concrete stop condition.
- `docs/maintenance/self-improvement-loop.md` now states that loop bounds are
  required to avoid unreviewed execution loops.

## Remaining Risks

These changes make the public contracts fail closed, but they do not claim that
every private runtime adapter has been exercised against a live Hermes board in
this branch. The remaining risk is integration drift: an operator can still
write an adapter badly, skip the validator, or fail to publish the required
worker result artifact. The mitigation is to keep Hermes transition hooks wired
to the validators and to treat Control Tower output as read-only unless Receipt
Five and worker-result reconciliation pass.

## Local Evidence Added

- `tests.test_factory_readiness_scorecard` now covers finite remediation loop
  budget requirements.
- `tests.test_factoryctl` now covers Product Face residual disposition for
  final completion, a human-gated positive path, repair-loop materialization,
  source-authority binding, native Kanban attachment readback and runtime-gate
  projection.
- `tests.test_evidence_reconciler` now blocks native Kanban attachment refs
  without durable readback proof.
- `scripts/factoryctl.py` now enforces the local invariants.
- `schemas/factory-readiness-scorecard.schema.json` and
  `schemas/product-face-result.schema.json` now expose the new contract fields.
- `schemas/worker-result.schema.json` exposes native attachment readback proof.
- `schemas/project-projection.schema.json` and
  `templates/project-projection.json` expose runtime-gate projection semantics.
- `templates/factory-readiness-scorecard.json` now carries bounded remediation
  limits.
- `product_face_result.scope_coverage_matrix` now exposes active SOT scope
  coverage for Product Face completion.

Verification run locally:

- `python -m unittest discover -s tests -q`: 841 tests passed.
- `python scripts/validate_document_governance.py`: passed.
- `python scripts/validate_public_json_artifacts.py`: passed.
- `python scripts/public_safety_scan.py`: passed.
- `python scripts/secret_safety_scan.py`: passed.
- `git diff --check`: passed.

## Next Priority

Keep closing the loop at runtime: run the Hermes transition hook against a live
board fixture, publish the worker result artifacts, and prove that a Control
Tower projection cannot override Receipt Five or worker-result reconciliation.
