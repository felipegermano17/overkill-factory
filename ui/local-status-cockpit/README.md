# Local-First Factory Web Cockpit

A local cockpit for operating the Overkill Factory from public-safe StatusSnapshot data. It can filter work, inspect gates/evidence, record local operator actions and download local receipts.

It does not mutate Hermes, approve gates, close issues, deploy, push to GitHub, or claim production readiness. External effects stay outside this static local surface.

Build the bundled fixture-only dataset:

```bash
python3 scripts/status_snapshot/build_local_cockpit_data.py --root . --out ui/local-status-cockpit/data/status-cockpit.json
```

Serve on loopback only:

```bash
python3 scripts/status_snapshot/serve_local_cockpit.py --directory ui/local-status-cockpit --host 127.0.0.1 --port 8784
```

Open `http://127.0.0.1:8784/`.

The committed dataset is generated from public fixtures only. Private execution reports are intentionally excluded from the repository.
