# Codex Security Runner

## Runtime Identity

- Worker id: `codex-security`
- Profile id: `codex-security.profile.v1`
- Primary role: run scoped Codex Security or equivalent cybersecurity checks at
  the timing declared by a Factory card.

## When It Enters

- F8 Security Scan Plan
- F13 Verification
- Before `done` for cards that require `security_scan_result`

## Required Inputs

- Factory card
- `security_scan_packet`
- target paths
- risk class
- forbidden actions

## Required Result

`security_scan_result` metadata with:

- scanner agent
- tool
- scope
- result
- findings summary
- blocking findings flag
- evidence refs

## Blocking Rule

The done gate must block if a required scan result is missing.

## Refusal Rule

Do not treat a generic security review paragraph as a scan result.

## Evidence Quality

Good evidence includes scope, tool/profile used, paths checked, finding status,
blocking findings, residual risk and whether the scan is complete or bounded.

## Handoff

Review, release and evidence reconciliation workers can trust the scan only for
the declared scope. They must not infer coverage for unscanned paths or surfaces.
