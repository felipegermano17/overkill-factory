# Fixtures

Fixtures are public-safe regression inputs.

They are not historical evidence, runtime exports, generated proof archives or private product source trees.

## Current fixture families

| Path | Purpose |
| --- | --- |
| `v2/` | Regression inputs for V2/factory control-plane behavior. |
| `incidents/` | Small incident-shaped edge cases for blocked, ready and missing-capability behavior. |
| `status-snapshot-v0/` | StatusSnapshot v0 fail-closed/read-only operator console cases. |
| `product-validation/` | Product-shaped validation fixtures for advanced production/onchain lanes. These are regression targets, not the default public product path. |

## Keep rule

A fixture stays only if it supports a test or validator.

Good fixture:

- minimal;
- public-safe;
- focused on one contract behavior when possible;
- required by automated validation;
- free of local paths, secrets, private chat IDs and private evidence.

Bad fixture:

- generated worker packets;
- generated gate reports;
- run summaries;
- screenshots;
- raw logs;
- old pilot proof;
- product material that belongs to a private operator.

## Validation

From `factory/`:

```bash
python scripts/status_snapshot/validate_status_snapshot_fixtures.py fixtures/status-snapshot-v0 --schema schemas/factory-status-snapshot.schema.json --require-cases FX01,FX02,FX03,FX04,FX05,FX06,FX07,FX08,FX09,FX10,FX11,FX12,FX13,FX14,FX15,FX16,FX17,FX18 --fail-closed
python scripts/status_snapshot/validate_evidence_refs.py fixtures/status-snapshot-v0 --allow-public-urls --allow-relative-artifacts --deny-raw-private --deny-local-paths --deny-chat-ids --deny-secrets --json
python scripts/status_snapshot/assert_fail_closed.py fixtures/status-snapshot-v0 --cases stale,missing,contradictory,private_unavailable,missing-gate
```
