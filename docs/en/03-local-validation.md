# Local validation

Local validation is required. But local validation is not live Hermes E2E proof.

It proves checkout coherence, public catalog/schema agreement, documentation build, safety scans, and local contract regressions.

## Requirements

Use Python 3.11 or newer. Run commands from `factory/` unless noted.

## Doctor

```bash
cd factory
python3 scripts/factoryctl.py doctor
```

Proves the basic kernel surface is readable. It does not prove real delivery.

## Minimal run

```bash
python3 scripts/factoryctl.py run minimal
```

Expected output includes `Wrote .tmp/quickstart-result.json` and `PASS: wrote .tmp/quickstart-result.json`.

Files in `.tmp` are generated output and must not be committed.

## Public validators

```bash
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
python3 scripts/generate_factory_reference_docs.py --check
```

`validate_public_surface_sync.py` checks manifest, required phrases, links, and public boundaries. `public_safety_scan.py` prevents dangerous public claims. `secret_safety_scan.py` prevents leaks.

## MkDocs

```bash
cd ..
python3 -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-check
```

Proves navigation and documentation build. It does not prove editorial quality by itself.

## Test suite

```bash
cd factory
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

The suite may print expected negative fixtures. The final status is what matters.

## Reading failures

Manifest failure usually means missing page, missing phrase, missing source_ref, or public overclaim.

Schema failure means JSON contract drift.

Docs build failure means navigation, link, or Markdown incompatible with strict MkDocs.

Worker profile failure means registry/profile/binding/permission drift.

## When live Hermes is required

Live Hermes is required to claim real execution, current worker results, runtime state, operational decisions, or private delivery. Local validation is not live Hermes E2E proof.
