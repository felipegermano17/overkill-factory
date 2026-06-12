# Factory 11 Security Review

> Document status: HISTORICAL EVIDENCE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This is not the current factory rule; it records a dated Factory 11 security review snapshot.

Scope: Factory 11 public-methodology hardening, worker expansion, public-safety
scan, Hermes update safety, and documentation changes.

## Result

No reportable secret or private-context leak was found after sanitization.

Validation run:

```bash
python scripts/public_safety_scan.py
python adapters/hermes/compatibility-check.py
python -m unittest discover -s tests -p "test_*.py" -q
```

All passed.

## Sensitive-Term Review

The repository intentionally contains words such as `wallet`, `signing`,
`mainnet`, `devnet`, `deploy`, `secret`, `funds` and `custody` because the
factory records forbidden actions and security boundaries.

These are not secret leaks by themselves. They are acceptable only when they
appear as:

- forbidden actions;
- scope-out terms;
- security controls;
- test fixtures;
- dry-pilot boundaries;
- worker trigger surfaces.

They are not acceptable when they contain:

- real credentials;
- private keys;
- real wallet seed material;
- production hostnames;
- private runtime paths;
- private board or task links;
- raw source extraction.

## Later Security Closure

This review predates the later full Codex Security repository-wide scan. Current
full-scan evidence is recorded in:

- `validation/security/codex-security-full-scan-2026-06-06.md`
- `validation/security/codex-security-full-scan-2026-06-06.html`
- `validation/security/bandit-scripts-adapters.json`

The heavy validation pass improved security routing but still did not complete
a full scan. It did fix public path leakage in worker packets, worker-registry
drift, and under-routing of Codex Security for public/code/CI/supply-chain
cards.

The remaining security posture is repeat-per-product rather than missing
factory evidence:

- product-specific Codex Security scan for future product source;
- product-specific dependency and provenance review;
- environment-specific release, monitoring and incident-response validation;
- Solana/Quasar Auditor rerun whenever future product source changes.
