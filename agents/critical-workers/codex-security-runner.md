# Codex Security Runner

## Purpose

Run Codex Security/Cybersecurity checks at the timing declared by a Factory card.

## Enters

- F8 Security Scan Plan
- F13 Verification
- Before `done` for cards that require `security_scan_result`

## Input

- Factory card
- `security_scan_packet`
- target paths
- risk class
- forbidden actions

## Output

`security_scan_result` metadata with:

- scanner agent
- tool
- scope
- result
- findings summary
- blocking findings flag
- evidence refs

## Hermes Gate

The done gate must block if a required scan result is missing.

## Hard Rule

Do not treat a generic security review paragraph as a scan result.
