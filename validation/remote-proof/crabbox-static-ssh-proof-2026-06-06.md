# Crabbox Static SSH Remote Proof

Result: `PASS`

Crabbox `v0.26.0` was installed from the official release archive with checksum
verification. The managed broker/Testbox path could not be used because no
approved broker or provider token was available, so the proof used Crabbox's
official static SSH provider fallback.

What was proven:

- Crabbox CLI ran against a clean public clone.
- Crabbox synced `488` files (`4.3 MiB`) to an external Linux SSH runner through
  `ssh+rsync`.
- Remote preflight detected Python, Git, Node, npm, Docker and tar on the
  runner.
- The remote runner executed:
  - `python3 --version`
  - `python3 scripts/validate_public_json_artifacts.py`
  - `python3 scripts/secret_safety_scan.py`
  - `python3 scripts/public_safety_scan.py`
- All validation commands returned `OK`.
- Crabbox returned exit code `0` with timing evidence.

What was not proven:

- This was not a Crabbox managed broker lease.
- This was not Blacksmith Testbox.
- It does not approve production product work.
- No secrets, deploys, funds, custody actions or production authority were used.

Public JSON receipt:

- `validation/remote-proof/crabbox-static-ssh-proof-2026-06-06.json`
