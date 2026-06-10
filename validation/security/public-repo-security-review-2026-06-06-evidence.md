# Public Repository Security Review Evidence - 2026-06-06

This evidence log is public-safe and contains only repo-relative references.

## Review Type

Bounded single-agent public repository review. This was not a full Codex
Security repository scan.

## Commands Run

```bash
python -m unittest discover -s tests -p "test_*.py" -q
```

Result: pass. The test suite ran 30 tests.

```bash
python adapters/hermes/compatibility-check.py
```

Result: pass.

```bash
python scripts/public_safety_scan.py
```

Result: pass.

```bash
python -m compileall -q scripts adapters/hermes tests
```

Result: pass.

```bash
python scripts/factoryctl.py validate-card validation/cards/public-repo-release-r2.md
```

Result: pass.

```bash
python scripts/factoryctl.py gate-report --card validation/cards/public-repo-release-r2.md
```

Result: generated a blocked gate report, with missing inputs for security,
cloud, release, supply-chain and monitoring workers. This is expected for the
validation card and confirms the routing model blocks incomplete public-release
evidence.

```bash
python scripts/factoryctl.py validate-card validation/cards/solana-quasar-r3.md
```

Result: pass.

```bash
python scripts/factoryctl.py validate-completion --card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md --receipt pilots/quasar-vault-guard-test/evidence/receipt-five-first-slice.json
```

Result: pass.

## Main Evidence Points

- CI currently runs unit tests, adapter marker compatibility, and public-safety
  scan.
- `docs/security/factory-11-security-review.md` already states that prior
  security review was not a full Codex Security repository scan.
- `scripts/factoryctl.py` routes public, code, CI and supply-chain cards toward
  security and supply-chain workers.
- `scripts/public_safety_scan.py` is a denylist scanner, not a general secret or
  privacy scanner.
- `adapters/hermes/compatibility-check.py` is marker-based, not a disposable
  patch-apply runtime proof.

## Bounded Findings

- `scripts/factoryctl.py::source_card_ref` can preserve angle-bracketed source
  references as raw text. This should be fixed outside this review's write
  scope.
- Public CI needs supply-chain, schema, workflow-permission and secret-scan
  coverage before the repo can claim a 10/10 public security posture.
