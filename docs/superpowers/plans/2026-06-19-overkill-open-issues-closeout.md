# Overkill Open Issues Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the current open Overkill Factory GitHub issues by turning Product Face, Kanban evidence, and product-process projection gaps into executable public-safe contracts.

**Architecture:** Keep enforcement in `scripts/factoryctl.py`, JSON schemas, templates, and focused tests. Runtime-specific behavior must be represented as public-safe contracts and smokeable adapters, not private board logs or raw local evidence.

**Tech Stack:** Python stdlib, `unittest`, JSON schemas/templates, `gh`, local `git`.

---

### Task 1: Product Face Completion Contracts

**Files:**
- Modify: `scripts/factoryctl.py`
- Modify: `schemas/product-face-result.schema.json`
- Modify: `tests/test_factoryctl.py`
- Modify: `docs/product-face/proof-runner.md`
- Modify: `docs/maintenance/implacability-audit-2026-06-19.md`

- [x] **Step 1: Verify current issue coverage**

Run:

```powershell
gh issue list --state open --limit 100 --json number,title,body,url,updatedAt
```

Expected: issues #382, #385, #386, #387, #389 are open before closeout.

- [x] **Step 2: Add failing tests for missing contracts**

Add tests proving final Product Face completion fails when:

- a stale/reference/demo surface is used without active SOT promotion;
- a repair-required residual does not materialize a deterministic repair loop;
- active SOT scope coverage is partial or missing.

- [x] **Step 3: Implement minimal validators**

Add validators that require source authority binding, repair loop routing, and active SOT scope coverage for final completion.

- [x] **Step 4: Verify focused tests**

Run:

```powershell
python -m unittest tests.test_factoryctl -q
```

Expected: PASS.

### Task 2: Native Kanban Attachment Evidence Contract

**Files:**
- Modify: `scripts/factoryctl.py`
- Modify: `schemas/worker-result.schema.json`
- Modify: `tests/test_factoryctl.py`
- Modify: `docs/automation/worker-automation-v0.md`

- [x] **Step 1: Add failing tests**

Add tests proving metadata/comment-only Kanban artifact refs fail closed and `kanban-attachment:` refs pass only with readback proof covering attachment row, blob, size, sha256, parse/schema status, scans, and held-card readback when applicable.

- [x] **Step 2: Implement validator and schema contract**

Extend worker-result artifact readback validation and `factoryctl` helper logic for native attachment refs and held-card hydration.

- [x] **Step 3: Verify focused tests**

Run:

```powershell
python -m unittest tests.test_factoryctl -q
python -m unittest tests.test_evidence_reconciler -q
```

Expected: PASS.

### Task 3: Runtime-Backed Product Process Projection

**Files:**
- Modify: `scripts/factoryctl.py`
- Modify: `schemas/project-projection.schema.json`
- Modify: `templates/project-projection.json`
- Modify: `tests/test_factoryctl.py`
- Modify: `docs/control-tower/open-source-setup.md`

- [x] **Step 1: Add failing tests**

Add tests for happy path, blocked Product Face, superseded repair route, missing release readiness, manual estimate, and stale source.

- [x] **Step 2: Implement projection validator/builder**

Ensure projection completion percent is derived from gates, not board counts or manual prose, and separates product progress from factory remediation.

- [x] **Step 3: Verify projection tests**

Run:

```powershell
python -m unittest tests.test_factoryctl -q
python -m unittest tests.test_public_json_artifact_validator -q
```

Expected: PASS.

### Task 4: Final Verification, Merge, Cleanup, Issue Closure

**Files:**
- Read/modify: all touched files above.

- [x] **Step 1: Run complete verification**

Run:

```powershell
python -m unittest discover -s tests -q
python scripts/validate_document_governance.py
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
git diff --check
```

Expected: PASS.

- [x] **Step 2: Commit and merge locally**

Commit the closeout on the feature branch, switch to `main`, merge the feature branch, and rerun complete verification on `main`.

- [x] **Step 3: Close GitHub issues**

Close issues #382, #385, #386, #387, and #389 only after the merged `main` state verifies.

- [x] **Step 4: Cleanup**

Delete the merged local feature branch if safe, prune stale worktrees if any, and report exact final state.

Cleanup note: the feature branch is still checked out by the primary worktree,
so it was preserved instead of deleting or force-switching that worktree. The
merged `main` worktree is clean and ahead of `origin/main`.
