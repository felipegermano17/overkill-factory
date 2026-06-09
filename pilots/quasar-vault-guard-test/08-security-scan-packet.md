# F8 Security Scan Packet

## Scan Owner

`security-runner`

## Timing

- Before Product Face completion.
- Before any onchain implementation card reaches ready.
- Before any R3/R4 done transition.
- Before promotion.

## Scope

- Product SOT and source resolution.
- Architecture candidate.
- Product Face prototype.
- Onchain Work Package.
- Worker packets.
- Human gate record.
- Receipt Five metadata.
- Authority boundaries.
- Prompt/process injection risk.

## Required Tools Or Profiles

- Codex Security/Cybersecurity analysis.
- solanabr/Auditor for onchain path.
- Browser/screenshot validation for Product Face evidence.

## Acceptance Policy

| Rule | Policy |
| --- | --- |
| Blocking findings allowed | No. |
| Missing evidence allowed | No for dry-pilot closure. |
| Human waiver allowed | Yes, only with explicit human gate record. |
| Prose-only review allowed | No. |
| Production authority granted | No. |

## Expected Output

`security_scan_result` in Receipt Five metadata, with evidence refs and
blocking findings status.
