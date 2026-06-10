# Release Public-Safety Tree Gap

This note tracks a release-readiness gap that is easy to miss.

The dirty working tree can pass the public-safety scan while the currently
committed tree or remote target still fails. That means the repository can look
safe locally but still be unsafe to publish from the wrong ref.

## Current Rule

Before publishing, creating a release branch, opening a pull request, or saying
the public repository is clean, scan the exact tree that will be published:

```bash
python scripts/public_safety_scan.py
python scripts/public_safety_scan.py --git-ref HEAD
python scripts/public_safety_scan.py --git-ref origin/main
```

The first command checks the dirty working tree.

The `--git-ref` commands check committed trees.

For public-safe reporting, write summaries instead of storing raw matching
lines:

```bash
python scripts/public_safety_scan.py --summary-json validation/public-safety/worktree-summary.json
python scripts/public_safety_scan.py --git-ref HEAD --summary-json validation/public-safety/head-summary.json
python scripts/public_safety_scan.py --git-ref origin/main --summary-json validation/public-safety/origin-main-summary.json
```

The summaries intentionally store only counts by category.

## Why This Matters

The factory has been redacting and replacing old private material in the working
tree. Until those changes are integrated into the exact release ref, the target
tree can still contain old private markers.

Do not use a passing dirty-worktree scan as proof that the published tree is
safe.

## Passing Condition

The release safety gap is closed only when:

- dirty worktree scan passes;
- target commit scan passes;
- target remote scan passes when publishing from a remote branch;
- the scan result is produced after the final release tree is selected.

Current public-safe summaries:

```text
validation/public-safety/worktree-summary.json
validation/public-safety/head-summary.json
validation/public-safety/origin-main-summary.json
```

At the current checkpoint, the dirty worktree summary passes, while the committed
and remote target summaries still fail. That means publishing must wait until
the cleaned working tree is integrated into the exact release ref and rescanned.

## Safe Next Step

Inventory and classify the current worktree first. Do not use broad cleanup.
After classification, integrate only intentional public-safe product changes,
then rerun the exact-tree scans.
