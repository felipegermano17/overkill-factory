# Security Scan Packet

## Scope

- Raw paper, SOT and architecture.
- Dashboard and receipt service.
- Quasar work package.
- Worker packets and worker results.
- Public safety and secret scan.
- Authority boundaries.

## Required Security Coverage

- OWASP Web/API basics.
- OWASP agentic/LLM tool-boundary thinking.
- Secrets and key exposure.
- Supply chain and scripts.
- Solana/Quasar preflight.
- Public repository hygiene.
- Release and monitoring boundary.

## Blocking Policy

Any finding that suggests signing, key access, write access, funds, deploy or
production promotion must block closure unless an explicit human waiver exists.

For this pilot, no such waiver is allowed except the bounded Auditor preflight
waiver that states no code audit is claimed.
