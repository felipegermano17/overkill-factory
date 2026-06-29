# Security Policy

## Reporting

Please report security issues privately through GitHub Security Advisories when
available. If advisories are not available, open a minimal issue that says a
private security report is needed and avoid exploit detail in public text.

## Public Boundary

Do not include secrets, private source dumps, local absolute paths, private
runtime identifiers, raw logs, screenshots with sensitive data or private board
links in issues, pull requests or committed files.

## Supported Version

Security fixes target the default branch until versioned releases define a
longer support window.

## Expected Checks

Before public release work, run:

```bash
factoryctl doctor
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
python scripts/validate_public_json_artifacts.py
python scripts/supply_chain_proof.py --check --no-write
```

GitHub also runs CodeQL, Dependency Review, Dependabot configuration checks and
the public security workflow. Those repository checks do not replace
product-specific security review, Auditor evidence or human gates.
