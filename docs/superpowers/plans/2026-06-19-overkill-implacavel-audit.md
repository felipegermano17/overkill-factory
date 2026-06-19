# Overkill Implacavel Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten Overkill Factory around proportional process, executable evidence, and gated self-improvement without creating infinite execution loops.

**Architecture:** Keep enforcement in existing public contracts and validators instead of adding a new process layer. Use `factoryctl.py` and `factory_self_improvement.py` as executable authorities, with tests proving fail-closed behavior before local docs claim the invariant.

**Tech Stack:** Python stdlib, `unittest`, JSON schemas/templates, existing `factoryctl.py` validators, `gh` issue inspection.

---

### Task 1: Audit Current State And Issues

**Files:**
- Read: `README.md`
- Read: `docs/maintenance/self-improvement-loop.md`
- Read: `docs/agents/capability-packs.md`
- Read: `docs/factory-workflow.catalog.json`
- Read: GitHub issues `#382`, `#385`, `#386`, `#387`, `#389`
- Create: `docs/maintenance/implacability-audit-2026-06-19.md`

- [x] **Step 1: Capture branch and issue state**

Run:

```powershell
git status --short --branch
gh issue list --state open --limit 100 --json number,title,updatedAt,url
```

Expected: current local branch plus open issues relevant to Product Face, runtime projection and artifact evidence.

- [x] **Step 2: Write audit artifact**

Create a public-safe audit summarizing proportionality-by-risk findings, executable-evidence findings, self-improvement loop findings, issue mapping, local changes and open risk.

### Task 2: Bound Remediation Loops

**Files:**
- Modify: `schemas/factory-readiness-scorecard.schema.json`
- Modify: `templates/factory-readiness-scorecard.json`
- Modify: `scripts/factoryctl.py`
- Modify: `tests/test_factory_readiness_scorecard.py`
- Modify: `docs/maintenance/self-improvement-loop.md`

- [x] **Step 1: Write failing test**

Added a test proving a scorecard with remediation required but no finite `max_remediation_attempts`, `timeout_minutes`, and `stop_condition` fails validation.

- [x] **Step 2: Run the focused test and confirm RED**

Run:

```powershell
python -m unittest tests.test_factory_readiness_scorecard.FactoryReadinessScorecardTest.test_remediation_loop_requires_finite_budget_when_required -q
```

Observed: FAIL because current validation did not enforce finite remediation budget.

- [x] **Step 3: Implement schema/template/validator**

Added finite remediation budget fields to `remediation_loop` and validation for required bounded remediation.

- [x] **Step 4: Run focused readiness tests**

Run:

```powershell
python -m unittest tests.test_factory_readiness_scorecard -q
```

Expected: PASS.

Observed: PASS.

### Task 3: Block Product Face Residuals From Final Completion

**Files:**
- Modify: `schemas/product-face-result.schema.json`
- Modify: `scripts/factoryctl.py`
- Modify: `tests/test_factoryctl.py`
- Modify: `docs/product-face/proof-runner.md`

- [x] **Step 1: Write failing test**

Added a test proving `validate_product_face_result_against_card()` rejects `PASS_WITH_RESIDUALS` unless each residual has a final completion disposition.

- [x] **Step 2: Confirm RED**

Run:

```powershell
python -m unittest tests.test_factoryctl.FactoryCtlTest.test_product_face_residual_requires_completion_disposition_for_final_acceptance -q
```

Observed: FAIL because current final completion validator accepted bounded residuals without final disposition.

- [x] **Step 3: Implement final-completion disposition validation**

Kept `validate_product_face_result()` able to accept bounded narrow-scope residuals, but made `validate_product_face_result_against_card()` fail closed for final product completion when residual disposition is missing or unresolved.

- [x] **Step 4: Add positive final-completion test**

Added a test proving a residual with explicit human gate disposition can pass final completion when all other evidence is valid.

### Task 3b: Require Active SOT Scope Coverage For Product Face Completion

**Files:**
- Modify: `schemas/product-face-result.schema.json`
- Modify: `scripts/factoryctl.py`
- Modify: `tests/test_factoryctl.py`
- Modify: `docs/product-face/proof-runner.md`

- [x] **Step 1: Write failing scope-coverage test**

Added a test proving a current-bound Product Face result that covers only part of the active Product SOT scope fails final product completion.

- [x] **Step 2: Confirm RED**

Run:

```powershell
python -m unittest tests.test_factoryctl.FactoryCtlTest.test_product_face_completion_requires_active_sot_scope_coverage -q
```

Observed: FAIL because current validation did not enforce active SOT scope coverage.

- [x] **Step 3: Implement Product Face scope coverage validation**

Added `scope_coverage_matrix` schema support and final-completion validation when active Product SOT scope exists. `partial` and `blocked` fail closed; `deferred_by_sot` and `out_of_scope_by_sot` require public-safe SOT or human-gate authority.

- [x] **Step 4: Add positive authorized-deferral test**

Added a test proving final completion can pass when all active Product SOT scope items are covered or explicitly deferred by SOT.

### Task 4: Verify And Report

**Files:**
- Read/modify: affected docs/tests/scripts/schemas above

- [x] **Step 1: Run focused checks**

Run:

```powershell
python -m unittest tests.test_factory_readiness_scorecard tests.test_factoryctl -q
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```

Observed final: PASS for focused suites, full `python -m unittest discover -s tests -q` ran 841 tests and passed, and public JSON/public safety/secret safety checks passed.

- [x] **Step 2: Inspect diff**

Run:

```powershell
git diff --check
git diff --stat
```

- [x] **Step 3: Finalize audit note**

Update the audit document with evidence, failures if any, and open issue coverage.

Observed: `git diff --check` passed, and the audit note records both local hardening and still-open issue coverage.
