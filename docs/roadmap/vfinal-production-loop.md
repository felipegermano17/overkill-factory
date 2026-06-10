# Overkill Factory vFinal Production Loop

This is the public-safe operating loop for making Overkill Factory vFinal fully
usable in production.

It is intentionally separate from the canonical architecture document. The
canonical document describes the final factory model. This file tracks the
remaining production loop.

## Current Decision

The real Hermes runtime update remains blocked.

The current preflight is:

```text
validation/hermes-production-update-preflight/real-runtime-update-blocked.json
```

Current blockers:

1. `operator_control_tower`
2. `complete_update_receipt`

Already proven:

- non-stub worker execution;
- real local terminal tool auth;
- scanner-backed specialist output quality;
- parent `done` reconciliation with a real worker result;
- production gateway rollback and monitoring recovery.

## Loop Rule

Every loop iteration must do one of these:

1. close a real blocker with evidence;
2. narrow a blocker into a more exact machine-checkable blocker;
3. improve harnesses, validation, cleanup, worktree readiness, docs or maps;
4. stop because the next step needs a private external input.

Do not repeat a solved blocker. Do not invent a `PASS` for missing Discord,
runtime registration, bridge health, human approval, secrets, cloud access or
external tool access.

## Next Production Path

### 1. Operator Control Tower

The Control Tower local contracts already pass:

```text
validation/control-tower/control-tower-readonly-smoke.json
validation/control-tower/control-tower-approval-registration-smoke.json
```

The production readiness harness is:

```bash
python scripts/operator_control_tower_proof.py \
  --mapping /private/path/to/discord-control-tower-mapping.json \
  --runtime-registration-event /private/path/to/runtime-approval-event.json \
  --bridge-health /private/path/to/bridge-health.json
```

Private evidence preparation is documented in:

```text
docs/control-tower/operator-control-tower-private-evidence-kit.md
```

The public bridge-health template is:

```text
templates/operator-control-tower-bridge-health.json
```

Current blocked receipt:

```text
validation/control-tower/operator-control-tower-production-readiness.json
```

To pass, the harness needs private evidence for:

- real Discord or equivalent owner cockpit mapping;
- runtime-registerable approval event;
- bridge or bot health checks following
  `schemas/operator-control-tower-bridge-health.schema.json`;
- proof that Discord is not the source of truth.

If it passes, it writes:

```text
validation/hermes-production-proof/operator-control-tower.json
```

### 2. Complete Update Receipt

The current blocked receipt is:

```text
validation/hermes-production-update-preflight/current-update-receipt-blocked.json
```

It becomes a passing update receipt only after `operator_control_tower` passes.

Then rerun:

```bash
python adapters/hermes/production_update_preflight.py \
  --non-stub-worker-execution validation/hermes-production-proof/non-stub-worker-execution.json \
  --real-tool-auth validation/hermes-production-proof/real-tool-auth.json \
  --specialist-output-quality validation/hermes-production-proof/specialist-output-quality.json \
  --real-worker-done-reconciliation validation/hermes-production-proof/real-worker-done-reconciliation.json \
  --production-rollback-monitoring validation/hermes-production-proof/production-rollback-monitoring.json \
  --operator-control-tower validation/hermes-production-proof/operator-control-tower.json \
  --complete-update-receipt validation/hermes-production-update-preflight/current-update-receipt-blocked.json \
  --out validation/hermes-production-update-preflight/real-runtime-update-blocked.json
```

The receipt file name may stay the same until the preflight result becomes
`PASS`; the content decides the state.

## Parallel Agent Use

Use parallel agents when work is independent.

Good parallel tracks:

- production blocker audit;
- cleanup and public-safety hygiene;
- worktree and branch readiness;
- document and mind-map review;
- test or validation review;
- Hermes runtime source review.

Do not delegate the immediate blocking action if the main agent needs that
result before it can continue.

Parallel agents must:

- get a narrow scope;
- avoid overlapping write sets;
- avoid raw private ids, paths, URLs, logs or secrets;
- return changed paths and evidence;
- never revert unrelated work.

Every write lane must produce a machine-checkable lane contract and pass:

```bash
python scripts/factoryctl.py validate-lane path/to/parallel-lane-contract.json
```

## Worktree And Cleanup Loop

Before a large implementation wave:

1. Record `git status --short`.
2. Separate intentional product changes, generated validation artifacts,
   obsolete artifacts and unrelated user changes.
3. Never delete or revert unrelated changes without explicit approval.
4. Prefer public-safe receipts over raw logs.
5. Run scans before publishing or creating a PR.
6. Check the exact release tree or target commit, not only the dirty local
   worktree.

Cleanup should happen in phases:

1. inventory;
2. classify;
3. validate what is safe to remove;
4. remove only scoped generated/obsolete artifacts;
5. rerun tests and public-safety scans.

Do not run a broad clean command on this repository until untracked vFinal
schemas, scripts, docs, tests, templates, patches and validation receipts have
been classified. Cache folders are safe cleanup candidates; evidence folders
need explicit review.

## Release Candidate Integration

The current release integration receipt is:

```text
validation/release/release-integration-preflight.json
```

It now carries a `release_candidate_plan` object. This is intentionally not a
production approval. It answers a narrower question:

```text
Can the current public-safe dirty worktree be prepared as a release candidate
branch?
```

If `safe_to_prepare_candidate_branch` is true, the recommended path is:

1. create or switch to `codex/vfinal-release-candidate`;
2. stage only the public-safe release-candidate worktree;
3. commit the candidate with validation evidence;
4. rerun public-safety and secret-safety scans on committed `HEAD`;
5. push or merge only after the production gate owner accepts the release path.

Do not publish `origin/main` while exact `HEAD` and `origin/main` scans fail.
Do not treat a release candidate branch as production readiness.

Generated validation receipts are tracked separately from product/release
changes. In the inventory they appear as `generated_receipt`, not as cleanup
trash and not as product work. A dirty worktree that contains only refreshed
receipts is not evidence that the factory product files are still unintegrated.
The final hygiene proof is still a clean `git status` after the receipts are
committed.
The preflight detects generated receipt paths directly from `git status`, so the
release result stays stable even when validation scripts refresh receipts in a
different order.

## Required Validation Before Claiming Progress

Run the narrowest useful set first, then the full set before a production claim:

```bash
python adapters/hermes/compatibility-check.py
python scripts/factoryctl.py validate-lane templates/parallel-lane-contract.json
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest discover -s tests -p "test_*.py" -q
```

Before publishing, scan the exact committed tree as well:

```bash
python scripts/public_safety_scan.py --git-ref HEAD
python scripts/public_safety_scan.py --git-ref origin/main
```

Track failures of the committed or remote tree here:

```text
docs/roadmap/release-public-safety-tree-gap.md
```

For Control Tower work, also run:

```bash
python scripts/control_tower_readonly_smoke.py
python scripts/control_tower_approval_registration_smoke.py
python scripts/operator_control_tower_proof.py
python -m unittest tests.test_operator_control_tower_proof -q
```

## Stop Conditions

Stop and report a real blocker when:

- the real owner cockpit does not exist yet;
- the private mapping evidence is missing;
- bridge health cannot be proven;
- runtime registration cannot be proven;
- a receipt would need private ids, URLs, paths, logs or secrets;
- a cleanup action would touch unrelated user work;
- Hermes real would be mutated without a receipt, rollback path or cleanup path.
