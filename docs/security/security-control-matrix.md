# Security Control Matrix

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This guide explains security coverage; a product still needs current scan evidence, worker results and gates.

Security in Overkill Factory is a matrix of specialists and controls. A generic
security comment is not enough.

## Minimum Specialist Coverage

| Area | Worker | Required Evidence |
|---|---|---|
| Networking and systems | `cloud-infra-security-specialist` | network boundaries, exposed ports, hardening, least privilege |
| Linux and runtime operations | `cloud-infra-security-specialist` | service model, filesystem permissions, logs, rollback |
| Web/AppSec | `appsec-owasp-specialist` | OWASP Web/AppSec checklist, input/output, SSRF, CORS, file handling |
| API security | `appsec-owasp-specialist` | auth, authorization, rate limits, schema validation, safe errors |
| Auth and session | `appsec-owasp-specialist` | session lifecycle, cookies/tokens, account recovery, failure cases |
| Agentic AI / LLM | `agentic-ai-security-specialist` | prompt injection, tool misuse, data exfiltration, excessive agency |
| Memory and context | `memory-steward` | trust tier, freshness, expiry, poisoning notes, source status |
| Supply chain | `supply-chain-gate` | dependency checks, lockfile, SBOM/provenance, CI, secret scan |
| Secrets and keys | `crypto-key-management-specialist` | secrets policy, KMS/key lifecycle, signing boundaries |
| Cryptography | `crypto-key-management-specialist` | algorithm choice, key rotation, misuse review |
| Cloud/IaC | `cloud-infra-security-specialist` | IAM, KMS, DNS, deploy permissions, IaC scan |
| Detection and monitoring | `detection-monitoring-worker` | logs, metrics, alerts, incident owner |
| Incident response | `detection-monitoring-worker` | rollback drill, incident runbook, escalation |
| Privacy and data | `security-orchestrator` | data map, retention, minimization, consent, access control |
| Solana/Quasar | `solana-quasar-auditor` | Auditor evidence, PDA, signer, CPI, compute, replay/idempotency |
| Public artifact safety | `public-safety-gate` | forbidden-term scan, private-link scan, raw-source exclusion |

## Timing

- F0/F1: protect source intake against prompt injection and memory poisoning.
- F4/F6: threat model architecture and choose required specialists.
- F8: create `security_scan_packet`.
- F13: run scans, Auditor and domain checks.
- F14/F15: independent review and AutoReview.
- F16/F17: public safety, release security, monitoring and rollback.
- F18: turn failures into tests, skills and checklists.

## Waiver Rule

A waiver is allowed only when it names:

- who owns the risk;
- why the control is not applicable;
- what evidence supports that;
- what compensating control exists;
- when it expires.

`not_applicable` without evidence is a failed control.
