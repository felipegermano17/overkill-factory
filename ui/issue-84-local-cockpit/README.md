# Local-First Factory Web Cockpit

A local, read-only cockpit for inspecting Overkill Factory work from public-safe StatusSnapshot data. It does not mutate Hermes, approve gates, close issues, deploy, or claim production readiness.

Build the bundled fixture-only dataset:

```bash
python3 scripts/issue84/build_local_cockpit_data.py --root . --out ui/issue-84-local-cockpit/data/status-cockpit.json
```

Serve on loopback only:

```bash
python3 scripts/issue84/serve_local_cockpit.py --directory ui/issue-84-local-cockpit --host 127.0.0.1 --port 8784
```

Open `http://127.0.0.1:8784/`.

The committed dataset is generated from public fixtures only. Private execution reports are intentionally excluded from the repository.
