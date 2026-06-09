# Security Review: Overkill Factory

Date: 2026-06-06

## Scope

This scan reviewed the public Overkill Factory repository at commit `664edd2`
plus the current hardening diff. The highest-risk surfaces were the factory
gate reconciler, Hermes transition hook, live Kanban adapter, Product Face
proof runner, remote proof runner, public JSON validator, public safety scanner,
secret scanner, worker-result schemas and published validation artifacts.

### Scan Summary

| Field | Value |
|---|---|
| Mode | Codex Security repository/scoped critical-surface scan |
| Threat model | Generated for this repository and used for discovery |
| Discovery | Parent review plus three parallel specialist reviews |
| Validation | Local proof probes, unit tests, public scanners, Bandit and remote proof |
| Reportable open findings | 0 |
| Fixed during scan | 9 |
| Remaining follow-up | Real Quasar Auditor execution, provider-backed remote proof and shared Hermes dashboard/API hook wiring |

## Threat Model

Overkill Factory is a public, open-source product-production line for autonomous
agents. The assets that matter most are gate integrity, evidence integrity,
public-safety hygiene, Hermes runtime safety, specialist separation, waiver
quality and honest boundaries around Product Face, Security, Auditor and Remote
Proof evidence.

The main trust boundaries are public repository publication, raw project-paper
input, worker-result JSON, Hermes transition requests, filesystem evidence refs,
browser/Product Face proof and Solana/Quasar/onchain evidence.

The highest-risk failure modes are gate bypass, stale or spoofed evidence,
synthetic evidence reused as real proof, weak waivers, transition fail-open,
task spoofing in Hermes completion, command execution in proof tooling, public
leaks and false claims of production/onchain/security proof.

## Findings

| Finding | Severity | Status |
|---|---:|---|
| Inline worker results could satisfy done with nonexistent evidence | High | Fixed |
| Product Face PASS could accept warning/blocking UI evidence | High | Fixed |
| Remote proof claimed no secrets while inheriting host environment | High | Fixed |
| Hermes live complete-main could target an arbitrary task id | Medium | Fixed |
| Public JSON validator ignored additionalProperties=false | Medium | Fixed |
| Worker-result schemas allowed weak worker/card/waiver shape | Medium | Fixed |
| Auditor waiver was semantically marked as real evidence | Medium | Fixed |
| Secret scanner let fixture words suppress concrete secret patterns | Medium | Fixed |
| Product Face external-file redaction missed normal Windows paths | Low | Fixed |

No reportable open finding remains after the applied fixes and verification.

## Reviewed Surfaces

| Surface | Risk Area | Outcome | Notes |
|---|---|---|---|
| `scripts/factoryctl.py` | Gate bypass / evidence spoofing | Fixed | Duplicate records block; inline evidence refs now require existing repo evidence; transition event fields and status match are enforced. |
| `adapters/hermes/transition_hook.py` | Fail-open transition | No issue found | Default remains fail-closed; `--report-only` is explicit observation mode. |
| `adapters/hermes/live_kanban_adapter.py` | Task spoofing | Fixed | `--complete-main` now requires a live binding created during materialization and sends real receipt metadata. |
| `scripts/product_face_proof.py` | False Product Face PASS / path leak | Fixed | A11y/overlap warnings now block; default states/journeys no longer claim unexercised flows; Windows path redaction hardened. |
| `scripts/remote_proof_smoke.py` | Secret exposure / weak isolation | Fixed | Commands run with sanitized env; receipt output is redacted and checked; no shell invocation. |
| `scripts/secret_safety_scan.py` | Secret false negative | Fixed | Concrete secret patterns are no longer skipped just because the line says example/fake/placeholder. |
| `scripts/validate_public_json_artifacts.py` | Public schema bypass | Fixed | `additionalProperties=false`, `minProperties` and strong waiver domain rules are enforced. |
| `schemas/*.json` | Weak public contract | Fixed | Worker result, Product Face and Auditor schemas now require stronger nested evidence shape. |
| Public artifacts | Internal leak | No issue found | Secret scan, public safety scan and JSON artifact validation pass. |
| Python scripts/adapters | Static code scan | No issue found | Bandit reviewed `scripts` and `adapters` with zero findings after explicit no-shell controls. |

## Validation Evidence

Commands run:

```text
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/remote_proof_smoke.py --out validation/remote-proof/local-clean-smoke.json --timeout-seconds 180
python -m bandit -r scripts adapters -f json -o validation/security/bandit-scripts-adapters.json
python scripts/validate_public_json_artifacts.py
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
```

Observed result:

- Unit tests: 43 tests passed.
- Remote proof: PASS in a clean temporary copy with sanitized environment.
- Bandit: 0 findings across `scripts` and `adapters`.
- Public JSON validation: OK.
- Secret safety scan: OK.
- Public safety scan: OK.

## Remaining Risk

This scan raises the factory-process confidence, but it does not replace:

- real `solanabr/Auditor` execution against real Quasar source;
- provider-backed Crabbox/Testbox remote proof;
- full Hermes dashboard/API/CLI hook wiring with bypass tests;
- production Product Face proof on a real deployed UI;
- multi-profile product-specific specialist dispatch. One public-safety profile
  dispatch is now smoke-proven separately.
