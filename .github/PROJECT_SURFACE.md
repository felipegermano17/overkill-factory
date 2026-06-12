# GitHub Project Surface

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: README.md, pyproject.toml, .github/workflows/, tests/
> Runtime boundary: GitHub automation protects the public repository. Hermes
> remains the runtime source of truth for real factory cards.
> Naming note: this guide is intentionally not named README.md so GitHub keeps
> the repository overview anchored to the product README at the repository root.

## What Belongs Here

This folder contains the GitHub project surface: issue templates, pull request
templates, Dependabot configuration and CI/security workflows that keep the
public repository installable, reviewable and safe for external operators.

## What Does Not Belong Here

Do not add generated worker packets, historical proof, screenshots, private
runtime exports, local workspace paths, secrets or internal validation logs.
Those belong in a local `.tmp/` directory, a private evidence store or a
sanitized release artifact.

## Source Of Truth

- `.github/workflows/ci.yml` proves the public quickstart and test path.
- `.github/workflows/security.yml` runs public-boundary and secret checks.
- `.github/workflows/codeql.yml` runs CodeQL analysis.
- `.github/workflows/dependency-review.yml` blocks risky dependency changes.
- `.github/dependabot.yml` keeps package and GitHub Actions updates visible.

The product entrypoint remains `README.md`; this folder only owns repository
automation and contribution hygiene.

## How It Is Validated

Run the local checks before changing workflows or templates:

```bash
python scripts/supply_chain_proof.py --check --no-write
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest discover -s tests -p "test_*.py" -q
```

After publication, the GitHub `ci`, `security`, `dependency-review` and
`codeql` checks must pass on the pull request and on `main`.
