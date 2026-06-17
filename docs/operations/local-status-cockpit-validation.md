# Local Status Cockpit Local Cockpit Validation

Status: PASS for the local read-only cockpit package.

Scope: public-safe fixtures, StatusSnapshot v0 schema, read-only adapter, fixture-only cockpit data, static local UI, loopback server, fail-closed semantics and public-boundary tests.

Not approved by this artifact: deployment, public endpoint hosting, production release, GitHub issue closure, or human authority.

Run locally from the repository root:

```bash
python3 scripts/status_snapshot/build_local_cockpit_data.py --root . --out ui/local-status-cockpit/data/status-cockpit.json
python3 scripts/status_snapshot/serve_local_cockpit.py --directory ui/local-status-cockpit --host 127.0.0.1 --port 8784
```

Open `http://127.0.0.1:8784/`.

Validation commands:

```bash
python3 scripts/status_snapshot/validate_status_snapshot_fixtures.py fixtures/status-snapshot-v0 --schema schemas/factory-status-snapshot.schema.json --require-cases FX01,FX02,FX03,FX04,FX05,FX06,FX07,FX08,FX09,FX10,FX11,FX12,FX13,FX14,FX15,FX16,FX17,FX18 --fail-closed
python3 scripts/status_snapshot/validate_evidence_refs.py fixtures/status-snapshot-v0 --allow-public-urls --allow-relative-artifacts --deny-raw-private --deny-local-paths --deny-chat-ids --deny-secrets --json
python3 scripts/status_snapshot/assert_fail_closed.py fixtures/status-snapshot-v0 --cases stale,missing,contradictory,private_unavailable,missing-gate
python3 -m unittest tests.test_status_snapshot_v0 tests.test_status_snapshot_readonly_adapter tests.test_local_status_cockpit_ui tests.test_public_safety_scan -v
```

Public-boundary decision: the committed cockpit dataset is generated from public fixtures only. Private execution reports are intentionally excluded from the repository.
