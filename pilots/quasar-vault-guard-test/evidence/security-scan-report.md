# Codex Security Scoped Scan Report

## Verdict

`PASS_WITH_BOUNDARIES`

No blocking finding was identified in the dry-pilot artifacts. The pilot remains
blocked for any production, signing, funds, custody, deploy, devnet, or mainnet
authority.

## Scope

- `pilots/quasar-vault-guard-test`
- `scripts/factoryctl.py`
- schemas used by the pilot

## Phase 1: Threat Model

Threat model written to:

```text
pilots/quasar-vault-guard-test/evidence/security-threat-model.md
```

Primary risks:

- authority expansion from test approval to production approval;
- fake security/Auditor/human evidence;
- Product Face skipped by backend-only completion;
- wallet signing accidentally exposed;
- Quasar/Anchor confusion;
- Receipt Five missing evidence refs.

## Phase 2: Finding Discovery

Commands/checks run:

```bash
rg -n "secret|token|private|password|api[_-]?key|BEGIN|wallet|sign|mainnet|devnet|deploy|eval\\(|<script|http://|https://" pilots/quasar-vault-guard-test README.md scripts schemas docs/automation
python scripts/factoryctl.py validate-card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md
python scripts/factoryctl.py gate-report --card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md
```

Discovery result:

- Sensitive terms found are policy boundaries and forbidden actions, not leaked secrets.
- No `<script>` tag exists in the prototype.
- No external runtime dependency exists in the prototype.
- Factory card validation passed.
- Gate report requires all five critical workers.

## Phase 3: Validation

| Candidate | Validation |
| --- | --- |
| Secret leak | Suppressed: no secret material found; matches are policy terms and schema IDs. |
| Wallet signing path | Suppressed: sign button exists only as disabled UI and forbidden action. |
| Devnet/mainnet authority | Suppressed: all occurrences are explicit prohibitions. |
| Fake human approval | Suppressed with boundary: human gate cites current user authorization and is dry-pilot only. |
| Fake Auditor pass | Suppressed with boundary: Auditor report states preflight only, no code audit pass. |
| Product Face missing | Suppressed: prototype and screenshots exist. |

## Phase 4: Attack Path Analysis

No reportable attack path exists inside the dry-pilot artifacts.

The main theoretical attack path is process-level:

```text
test authorization -> broad interpretation -> production authority
```

Mitigation:

- card `scope_out` forbids sensitive actions;
- `forbidden_actions` blocks deploy, signing, keys, funds, custody, devnet and mainnet;
- human gate record is dry-pilot only;
- Receipt Five must preserve boundaries.

## Final Decision

The dry pilot can complete.

It must not be reused as evidence for:

- production deployment;
- live Quasar program safety;
- wallet signing readiness;
- custody/funds safety;
- mainnet/devnet operation.
