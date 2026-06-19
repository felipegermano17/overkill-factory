# Fixtures

Fixtures are minimal public-safe regression inputs. They are not historical
evidence, runtime exports or proof archives.

## What Belongs Here

- Small JSON or text fixtures required by automated tests.
- Domain-neutral cases that prove one contract behavior without private data.
- Public-safe negative fixtures that keep scanners and fail-closed behavior
  honest.

## What Does Not Belong Here

- Generated worker packets, gate reports, receipts or run summaries.
- Screenshots, private board exports, raw logs, local paths or old pilot proof.
- Large fixture archives when a small case can prove the same rule.

## Source Of Truth

Fixtures are supporting inputs. Schemas, scripts and tests decide whether the
behavior is valid.

Current fixture family:

| Path | Purpose |
| --- | --- |
| `fixtures/status-snapshot-v0/` | Public-safe StatusSnapshot v0 cases for the local operator console fail-closed/read-only contract. |

## How It Is Validated

```bash
python scripts/status_snapshot/validate_status_snapshot_fixtures.py fixtures/status-snapshot-v0 --schema schemas/factory-status-snapshot.schema.json --require-cases FX01,FX02,FX03,FX04,FX05,FX06,FX07,FX08,FX09,FX10,FX11,FX12,FX13,FX14,FX15,FX16,FX17,FX18 --fail-closed
python scripts/status_snapshot/validate_evidence_refs.py fixtures/status-snapshot-v0 --allow-public-urls --allow-relative-artifacts --deny-raw-private --deny-local-paths --deny-chat-ids --deny-secrets --json
python scripts/status_snapshot/assert_fail_closed.py fixtures/status-snapshot-v0 --cases stale,missing,contradictory,private_unavailable,missing-gate
python -m unittest tests.test_status_snapshot_v0 tests.test_status_snapshot_readonly_adapter tests.test_public_safety_scan -q
```
