# Changelog

All notable public changes should be recorded here.

The format follows Keep a Changelog principles and uses semantic versioning for
public releases.

## Unreleased

Nothing yet.

## 1.5.2 - 2026-06-24

- Fix Hermes no-idle classification so dependency-gated `todo` chains behind
  blocked ancestors do not create generic remediation loops.
- Add explicit `input_required`/`operator_input_required` no-idle handling so
  Telegram-first operators are asked for exact missing inputs instead of being
  told the factory has no human action.

## 1.5.1 - 2026-06-24

- Harden authority/autonomy enforcement so planning-only continuation, source
  resolution, Product SOT review, method routing and specialist routing cannot
  become human approval requests unless a real authority trigger is present.
- Remove `understanding` and `plan` from the `approval-request` approval types;
  understanding is confirmation, and planning is briefing/status unless access,
  budget, risk, scope change, release or production authority is required.
- Tighten `human-gate-clerk`, Control Tower and operator docs so Telegram,
  Discord or bridge surfaces distinguish proactive briefing from real human
  gates.
- Add regression tests for F9 planning-only cards, false planning gates,
  approval-request schema boundaries and Control Tower approval examples.

## 1.5.0 - 2026-06-24

- Added the canonical Factory Operating System registry and scorecard for the
  11 OS areas tracked in issues #400-#410.
- Added Method OS engine registry for spec-first SDD, TDD, BDD,
  discovery/research, security-first, design-first, legacy diagnosis and
  incident-first routing.
- Added public-safe Hermes runtime proof generation and scorecard integration.
- Hardened factory start so rich product material requires source inventory,
  brownfield handling, questions and briefing before Product SOT promotion.
- Updated README/docs/CLI reference and public manifest for the OS spine,
  Hermes runtime proof, Telegram-first operation and completion-audit
  boundaries.

## 1.4.0 - 2026-06-23

- Add Telegram-first operator interface, conversational start and deep briefing
  package contracts so new product work confirms understanding before Product
  SOT and pushes PDF/markdown decision packages instead of relying on shallow
  chat summaries or operator polling.
- Add `factoryctl operator-interface`, `factoryctl start-conversation`,
  `factoryctl briefing-package` and `factoryctl understanding-confirmation`
  validation/build commands for public-safe startup flows.
- Require Solana/onchain product signals to route deterministically through the
  `solana-ai-kit-core` domain brain before execution.
- Harden the public validator so confirmed factory starts require a real start
  request ref and confirmed product understanding requires a real operator
  response ref.

## 1.3.0 - 2026-06-23

- Add Fast Autonomy Lane contracts: `fast_autonomy` for reversible low-risk
  work and `yolo_sandbox` for disposable R0/R1 diagnostics, both blocked from
  production, mainnet, funds, signing, secrets, billing, destructive actions
  and human-gate approval.

## 1.2.1 - 2026-06-23

- Harden Hermes `enforce-done --complete-main` so local or scratch completion
  artifacts must be copied to durable attachment storage, read back with a
  matching SHA-256 hash and rewritten to durable logical refs before Hermes
  `complete`.
- Reject metadata-only `kanban-artifact:` and `kanban-attachment:` completion
  evidence unless the receipt carries explicit artifact readback proof.
- Add the Hermes `no-idle` controller, which classifies ready/running/todo/
  blocked state, creates only safe factory-owned remediation cards when the
  board would otherwise sit silently idle, and never dispatches workers itself.
- Add the public Hermes update guard and runbook coverage for safer Hermes
  updates and gateway restarts around active Kanban work.

## 1.2.0 - 2026-06-22

- Require a project-level design-system / `DESIGN.md` contract for
  product-facing frontend work, wire it into Product Face validation, worker
  packets, public templates, schemas and examples.

## 1.1.1 - 2026-06-19

- Document the v1.1.0 Codex Bridge plugin release surface in the public
  changelog and root READMEs.
- Clarify that the v1.0.1 visual map is a supporting visual surface versioned
  separately from the release tag and that Solana AI Kit routing is authoritative
  in capability packs, worker packets and validation.
- Mark intentional maintainer/audit pages as excluded from MkDocs navigation
  warnings.
- Keep local generated build output and runtime bridge inbox records out of
  public validation discovery.
- Pin the Solana AI Kit domain-brain provider to the resolved `v2.0.2` commit
  and record the unsigned upstream tag as a supply-chain gate input.
- Require `remote-proof-runner` for high-risk Solana/onchain cards even when a
  card omits an explicit `runtime_contract.remote_proof_required=true`.
- Extend the validation battery with Solana bank R4 routing scenarios covering
  wallet, signing, funds, mainnet, Product Face, security, key-management,
  release, remote proof and supply-chain gates.
- Harden public-safety and SBOM/source inventory scans against transient local
  paths that appear or disappear while validation is running.
- Add public schemas for generated doctor and quickstart smoke result
  artifacts so local audit output stays contract-validated.

## 1.1.0 - 2026-06-19

- Shipped the public Overkill Factory Bridge Codex plugin package, including
  install docs, inbox resolution, hook trust boundaries and the rule that the
  plugin acts only as an operator bridge, not as Hermes, the factory runtime,
  a gate approver or Receipt Five evidence.
- Replaced the legacy Solana core pack with `solana-ai-kit-core`, backed by
  `solanabr/solana-ai-kit@v2.0.2` as the official Solana domain-brain provider.
- Added deterministic Solana surface inference to worker routing. Worker
  packets now expose `input_contract.surface_router` with declared, inferred
  and effective surfaces plus route reasons.
- Added `domain_brain_provider` to Solana-domain worker packets and dynamically
  inject `solana-ai-kit` into relevant planning, architecture, build, wallet,
  QA, integration and security workers.
- Require `solana_ai_kit_usage_receipt` for real `PASS` results from
  Solana-domain workers, including cases where Solana was inferred from card
  content instead of declared in `surfaces`.
- Expanded public Solana coverage across Anchor, Pinocchio, Token-2022, SPL,
  NFT, Metaplex, DeFi, AMM, staking, governance, RPC, wallet and transaction
  surfaces while keeping Factory gates, Hermes state, Receipt Five, signer
  rules and human approvals above provider guidance.

## 1.0.0 - 2026-06-16

- Added the operator-first CLI path: `factoryctl doctor`, `factoryctl init` and
  `factoryctl run minimal`.
- Added public docs site navigation, CLI reference, Hermes install guide,
  example gallery, release policy and OSS security guide.
- Added Dependabot, CodeQL, Dependency Review and security workflow surfaces.
- Replaced dead public metadata URLs with canonical GitHub metadata, added a
  `.github/` entrypoint README and tightened public-safety scanning around
  metadata-only repository URLs and generated local build output.
- Added factory-owned recovery, status, readiness, truth and blocker paths so
  non-human blocks route back into explicit repair actions instead of hidden
  operator work.
- Added Product Face proof profiles, executable state/journey drivers and
  stricter Product Face PASS validation.
- Added capability-pack activation, full-product worker graph contracts and
  production/release preflight checks for public-safe repository releases.
- Added public-surface synchronization checks so docs and the published visual
  map can be verified against the repository source of truth.

Known boundary: the public repository release validates the factory kernel,
schemas, docs, CLI, examples and public safety. Private runtime/operator console
production readiness still requires operator-owned Hermes evidence and real
approval records outside the public repo.

## 0.1.0

- Initial public alpha package metadata, public quickstart, Hermes adapter,
  worker registry, schemas, examples and validation scripts.
