# Multi-Profile Hermes Dispatch Summary

Date: 2026-06-06

This run used a disposable Hermes Kanban board and a clean public repository
clone. Operational board IDs, task IDs, sessions and temp paths are intentionally
redacted from this public artifact.

## What Was Proven

| Public Alias | Hermes Profile | Result | Evidence |
|---|---|---:|---|
| `product-face-fallback-contract` | `product-face` | WAIVED | `validation/hermes-live/multi-profile-dispatch-fixed/product-face/qvg-product-face-result.json` |
| `security-focused-scan` | `codex-security` | PASS | `validation/hermes-live/multi-profile-dispatch-fixed/security/security_scan_result.json` |
| `auditor-quasar-preflight` | `solana-quasar-auditor` | WAIVED | `validation/hermes-live/multi-profile-dispatch-fixed/auditor/auditor_result.json` |
| `remote-proof-clean-fallback` | `remote-proof-runner` | PASS | `validation/hermes-live/multi-profile-dispatch-fixed/remote-proof/remote-proof-result.json` |
| `product-face-browser-proof` | `product-face` | PASS | `validation/hermes-live/multi-profile-dispatch-browser/product-face/qvg-product-face-result.json` |
| `remote-proof-after-browser` | `remote-proof-runner` | PASS | `validation/hermes-live/multi-profile-dispatch-browser/remote-proof/remote-proof-result.json` |

## Important Finding

The first real multi-profile dispatch found a Product Face fallback contract bug:
fallback evidence could be honest but still invalid for public JSON validation.
That was fixed before the clean rerun by:

- adding a static-summary schema;
- making fallback checks schema-valid while still blocking promotion;
- requiring a waiver object whenever Product Face result is `WAIVED`.

The browser-backed Product Face rerun then exposed a second runtime issue: the
Playwright package could be present while the bundled browser cache was absent.
The runner now falls back to the installed system Chrome channel, covered by a
unit test.

## Evidence Boundaries

- Product Face browser proof is real browser-local static proof with desktop and
  mobile screenshots. It is not production UI approval.
- Codex Security proof is focused public/secret safety, unit-test and factory
  battery evidence. It is not product-specific deployment or onchain approval.
- Auditor/Quasar proof is an operational preflight only. It is not a product
  Quasar code audit because no real product Quasar source exists in this public
  pilot.
- Remote Proof is real local clean-tempdir fallback evidence. It is not
  provider-backed Crabbox/Testbox proof.

## Verification

All public aliases above closed in Hermes with terminal `done` state. Commands
rerun after importing the public artifacts:

```bash
python scripts/validate_public_json_artifacts.py
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python scripts/factory_battery.py
git diff --check
```

All passed. `git diff --check` reported only line-ending normalization warnings
on existing battery files and no whitespace errors.
