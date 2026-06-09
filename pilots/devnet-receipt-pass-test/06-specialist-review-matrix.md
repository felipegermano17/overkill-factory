# Specialist Review Matrix

| Worker | Focus | Blocking Question |
| --- | --- | --- |
| Product Face Validator | Visual product, mobile, states, a11y | Can a user see the state and boundaries? |
| Codex Security Runner | Repo, app, boundaries, scans | Is any sensitive action or secret exposed? |
| Solana/Quasar Auditor Runner | PDA and instruction intent | Is any onchain claim overstated? |
| AppSec OWASP Specialist | Web/API/browser controls | Are dashboard and RPC surfaces safe enough? |
| Agentic AI Security Specialist | Tool and memory boundaries | Could an agent treat untrusted text as authority? |
| Cloud and Infrastructure Security Specialist | Deploy, CI, infra boundary | Is deployment blocked unless gated? |
| Crypto and Key Management Specialist | Signing, keys, custody | Are keys and signing fully out of reach? |
| Supply Chain Gate | Node, CI, artifacts | Are dependencies and generated artifacts controlled? |
| Remote Proof Runner | Runtime parity | Is local proof enough, or is an external proof required? |
| Release Operations Worker | Promotion | Is production release explicitly blocked? |
| Detection and Monitoring Worker | Monitoring | Is future production observability identified? |
| Public Safety Gate | Public repo hygiene | Are public artifacts free of private residue? |
| Independent Reviewer | Adversarial review | Can a different worker break the claim? |
| Human Gate Clerk | Human authority | Is the approval scope real and limited? |
| Handoff Packer | Replayability | Can another worker continue without chat memory? |
| Memory Steward | Source reuse | Are source and memory trust tiers clear? |
| Skill Eval Distiller | Future skill improvement | Did the pilot reveal a reusable skill update? |
