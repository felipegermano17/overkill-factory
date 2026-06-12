# Security Specialist Matrix

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This guide explains security routing; product-specific security approval still requires current worker evidence and gates.

The factory does not use one generic security worker for every risk. Security
is routed by domain, timing and evidence type. This prevents an agent from
writing "security reviewed" while the real risk belongs to a different
specialty.

## Routing Rule

1. `security-orchestrator` maps the card to one or more domains.
2. Domain specialists run or prepare scoped evidence.
3. `codex-security` runs code/security scans when the card requires tool-backed
   security evidence.
4. Findings are fixed, waived by the right gate or kept as blockers.
5. No security worker can waive its own blocking finding.

## Required Domains

| Domain slug | Domain | Primary worker | Evidence expected |
|---|---|---|---|
| `networking` | Networking | `cloud-infra-security-specialist` | network exposure, ingress/egress, segmentation and firewall notes |
| `linux-systems` | Linux/Systems | `cloud-infra-security-specialist` | runtime user, file permissions, process boundary and host-hardening notes |
| `web-security` | Web Security | `appsec-owasp-specialist` | OWASP Web/API controls, auth/session, validation and safe error handling |
| `ethical-hacking` | Ethical Hacking | `codex-security` plus routed specialist | scoped attack-path review, no unscoped probing, no sensitive exploit publication |
| `security-tools` | Security Tools | `codex-security` and `supply-chain-gate` | scan command, target scope, tool output, finding status and rerun evidence |
| `cloud-security` | Cloud Security | `cloud-infra-security-specialist` | IAM, KMS, deploy posture, secret boundaries, rollback and logs |
| `detection-monitoring` | Detection & Monitoring | `detection-monitoring-worker` | logs, metrics, alert owner, incident path and rollback signals |
| `cryptography` | Cryptography | `crypto-key-management-specialist` | key boundary, custody model, signer authority, rotation and recovery |
| `security-operations` | Security Operations | `security-orchestrator` and `release-ops-worker` | control owners, waiver path, release blockers, response ownership |
| `future-security` | Future of Security | `agentic-ai-security-specialist` | AI security, prompt injection, tool misuse, memory poisoning and autonomous-defense limits |
| `supply-chain` | Supply Chain | `supply-chain-gate` | SLSA/provenance, attestation, lockfiles, container image, OIDC/workflow permissions and branch protection |
| `onchain-solana-quasar` | Solana/Quasar/Auditor | `solana-quasar-auditor` | Quasar-specific program model, Auditor corpus coverage, PDA/signer/CPI map, authority, oracle, economic, MEV, RPC and finality notes |

## Timing

| Factory moment | Required action |
|---|---|
| Source/SOT | `memory-steward` and `agentic-ai-security-specialist` classify untrusted text, memory and tool risk when agents are in scope. |
| Architecture | `security-orchestrator` routes domain specialists before decomposition and blocks unowned security domains. |
| Implementation | `codex-security`, AppSec, onchain, cloud, key, supply-chain or monitoring specialists run only if their surface is present. |
| Pre-done | Required worker results must exist and match the card scope. |
| Release | Human gate, release ops, monitoring and public-safety boundaries must pass before promotion claims. |

## Machine-Checkable Contract

Every security-critical profile carries:

- `domain_contract.domain_slugs`: the security domains it owns.
- `domain_contract.routing_moments`: when it must enter the factory.
- `domain_contract.required_controls`: the controls it cannot skip.
- `domain_contract.minimum_evidence`: the evidence that must exist.
- `waiver_contract`: owner, scope, expiry/review and human-gated waiver rules.

This is better than prose because an autonomous agent can be blocked for a
missing domain, missing waiver owner or late routing before the card reaches
execution.

## Why This Is Better

One broad security worker is fast but weak: it misses domain-specific failure
modes and gives agents a way to hide uncertainty. A routed matrix is heavier,
but it gives the factory an exact owner, exact evidence and exact blocker for
each risk surface. That is better for autonomous agents because they need
machine-checkable routing more than elegant prose.

## Non-Negotiables

- Onchain work needs the Solana/Quasar auditor path.
- Code and sensitive surfaces need scoped security scan evidence or a waiver.
- AppSec-sensitive work needs OWASP control coverage.
- Agentic systems need prompt-injection, memory and tool-boundary review.
- Key, custody and signer surfaces cannot be handled by an agent that can touch
  real keys or funds.
- Supply-chain work needs provenance, lockfile, workflow-permission and secret
  scan evidence.
- Solana/Quasar work needs Quasar-aware review and Auditor evidence; preflight
  is not a code-audit pass.
- Public artifacts must pass public-safety review before publication.
