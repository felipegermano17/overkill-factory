# Changelog

All notable public changes should be recorded here.

The format follows Keep a Changelog principles and uses semantic versioning for
public releases.

## Unreleased

Nothing yet.

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
