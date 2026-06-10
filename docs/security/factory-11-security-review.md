# Factory 11 Security Review

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

## Remaining Security Work

This review is not a full Codex Security repository-wide scan. A full scan
requires its own threat-model, discovery, validation, attack-path analysis and
final report artifacts.

The heavy validation pass improved security routing but still did not complete
a full scan. It did fix public path leakage in worker packets, worker-registry
drift, and under-routing of Codex Security for public/code/CI/supply-chain
cards.

The next validation goal should run:

- full Codex Security scan for the public repo;
- supply-chain/dependency scan;
- public-safety scan in CI;
- Hermes adapter patch compatibility tests;
- remote proof smoke;
- Product Face browser proof;
- Solana/Quasar Auditor against real implementation source when available.
