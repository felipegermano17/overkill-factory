# Overkill Factory

Overkill Factory is an open product-production factory for autonomous agents.

It turns a messy product paper into a controlled production line:

```text
raw product paper
-> source resolution
-> Product SOT
-> architecture
-> specialist reviews
-> documentation OS
-> decomposition
-> Hermes Kanban cards
-> agent execution
-> evidence
-> independent review
-> human gates
-> stable release
```

The core belief is simple: autonomous agents do not need prettier prose. They
need contracts, gates, receipts, and a runtime that refuses weak work.

## What This Repository Contains

- The Overkill Factory methodology.
- Machine-checkable card and receipt contracts.
- Hermes/Kanban adapter patches.
- Example cards, worker packets, gate reports, and Receipt Five metadata.
- A Codex skill for operating the factory.
- Initial automation for critical factory workers: Product Face, Codex Security,
  onchain auditor, independent reviewer, and human gate clerk.
- Factory 11 hardening: public source policy, security control matrix, worker
  registry, Hermes update safety, public-safety scan and CI.
- Live Hermes Kanban adapter evidence: real board, main card, required worker
  cards, dependency links, negative done block, positive done reconciliation.
- Real Hermes specialist dispatch evidence: `public-safety-gate` preloaded the
  factory skill, ran a public-safety scan and completed with Receipt Five.
- Official Hermes main patch smoke: the public adapter patch applied to official
  Hermes commit `56236b16e383cc656bb8c88429902f4de83f1faf` and the focused
  regression suite passed.
- Real supply-chain gate evidence: Hermes `supply-chain-gate` validated
  least-privilege CI permissions, commit-pinned GitHub Actions, public scans,
  source SBOM and unit tests on a clean public clone.
- Completion audit guard: Hermes `independent-reviewer` confirmed the public
  evidence is still `NOT_COMPLETE` for practical 10/10 and that
  `--require-complete` blocks until production/provider-backed evidence exists.
- Bounded full product worker graph evidence: QVG now reconciles ten real lanes
  into one product-specific public validation graph while preserving
  `reusable_for_product=false` and `completion_claim_allowed=false`.
- Managed remote-proof readiness probe: Hermes `remote-proof-runner` confirmed
  managed Crabbox broker / Blacksmith Testbox proof remains `PENDING` without
  configured provider credentials, while public output stays redacted.
- Production-like Product Face proof: Hermes `product-face` validated the QVG
  public validation product as a reusable Product Face lane with scoped product
  id, production-like static artifact class, screenshots, DOM state, console,
  a11y basics, overlap checks and target hash.
- Production-validation Quasar Auditor proof: Hermes `solana-quasar-auditor`
  validated the QVG public validation product source under `products/` with a
  clean Docker Quasar build/test, Auditor corpus/checklist coverage and a
  scoped reusable Auditor lane.
- Multi-context validation battery artifacts with Product Face, security,
  onchain, release, agentic and public-repo stress scenarios.

## Why Hermes Is Required

The first supported runtime is Hermes.

Hermes is the factory floor: the agents live there, the work moves through its
Kanban, and the gates block bad transitions before autonomous execution starts.

Overkill Factory stays separate from Hermes so the methodology remains its own
project, but the Hermes adapter is a first-class and required integration.

## Current Status

Factory 10 has been validated in a real Hermes runtime and in a multi-context
offline battery.

The portable Hermes adapter patch is kept under `adapters/hermes/patches/`.
The live adapter entrypoint is `adapters/hermes/live_kanban_adapter.py`.
Official-main patch evidence is recorded in
`validation/hermes-live/official-main-patch-smoke.md`.

The first dry pilot is complete and kept under:

```text
pilot: pilots/quasar-vault-guard-test
status: done
```

## Quick Start

Read these in order:

1. `docs/methodology/overkill-factory-v0.md`
2. `docs/methodology/overkill-factory-v3-6.md`
3. `docs/planning/execution-plan.md`
4. `docs/automation/worker-automation-v0.md`
5. `adapters/hermes/README.md`
6. `agents/worker-roster.md`
7. `agents/worker-registry.public.json`
8. `docs/security/security-control-matrix.md`
9. `adapters/hermes/compatibility-manifest.md`
10. `docs/maps/whimsical-board.md`
11. `pilots/quasar-vault-guard-test/README.md`
12. `docs/roadmap/factory-11-action-plan.md`
13. `docs/methodology/factory-11-operational-hardening.md`
14. `docs/validation/heavy-validation-results.md`
15. `docs/reviews/heavy-validation-adversarial-review.md`

Run the local preflight:

```bash
python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md
python scripts/factoryctl.py gate-report --card examples/cards/v35_valid_onchain_auditor_scan.md
python scripts/factoryctl.py worker-packet --worker all --card examples/cards/v35_valid_onchain_auditor_scan.md --out examples/worker-packets/onchain-card
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/cards/v35_valid_onchain_auditor_scan.md --out examples/worker-packets/onchain-card
python scripts/factoryctl.py validate-completion --card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md --receipt pilots/quasar-vault-guard-test/evidence/receipt-five-first-slice.json
python scripts/factory_battery.py
python adapters/hermes/compatibility-check.py
python scripts/supply_chain_proof.py --check --no-write
python scripts/full_product_worker_graph.py --require-pass
python scripts/managed_remote_proof_probe.py
python scripts/factory_completion_audit.py
python scripts/public_safety_scan.py
python -m unittest discover -s tests -p "test_*.py" -q
```

For release gating, `python scripts/factory_completion_audit.py --no-write
--require-complete` is expected to fail until the remaining production and
provider-backed blockers are cleared. That failure is the guardrail, not a test
flake.

After a specialist really runs, write structured evidence metadata:

```bash
python scripts/factoryctl.py evidence-record --worker codex-security --card examples/cards/v35_valid_security_with_scan.md --result PASS --tool codex-security:security-scan --actor security-runner --evidence-ref reports/security-scan.md
python scripts/factoryctl.py human-gate-record --card examples/cards/v35_valid_onchain_auditor_scan.md --decision approved --human-actor product-owner --evidence-ref decisions/r3-human-approval.md
```

## Current Boundaries

The repo prepares contracts and worker packets. It does not fake scanner output,
Auditor results, screenshots, independent approval, or human decisions.

The dry pilot proves the factory process and Hermes gates. It does not prove
production readiness, deploy readiness, real onchain program safety, wallet
signing, devnet/mainnet behavior, funds movement, or custody safety.

The live Hermes smoke proves that the adapter can materialize a synthetic
Solana/Quasar R3 card into real Hermes Kanban tasks and block/allow completion
based on worker results. The smoke worker results are intentionally marked as
synthetic and cannot be reused as real product evidence.

The real profile dispatch smoke proves one specialist profile can be spawned by
Hermes, load the factory skill, run a scoped scanner and complete with Receipt
Five. It does not prove all specialist profiles or product-specific execution.

The official-main patch smoke proves the public patch applies to the tested
Hermes main commit and keeps focused Kanban/dashboard regression tests green. It
does not prove future Hermes releases will remain compatible without rerunning
the compatibility manifest.

The first production-intent pilot still needs a real raw product paper.

The completion audit currently blocks practical 10/10 because the repository
does not yet contain production CU/SVM/economic proof, managed remote proof,
production release human gate evidence or a production product graph with every
critical lane marked `reusable_for_product=true`. Production-like Product Face
and production-validation Quasar Auditor are now achieved only for the named
QVG public validation product lanes.

The QVG full product graph now proves bounded product-specific reconciliation
across Product Face, Security, Auditor, CU/SVM/economic proof, Remote Proof,
Independent Review, Human Gate, Release Ops, Supply Chain and Receipt Five. It
now includes reusable Product Face and Quasar Auditor lanes, but it is
intentionally not reusable as production approval because the remaining critical
lanes keep production boundaries.

The managed remote-proof probe records the current provider gap explicitly:
static SSH proof exists, but managed Crabbox broker / Blacksmith Testbox still
needs credentials, a provider-backed run handle, transcript, artifacts and
cleanup evidence.

## Public Repository Safety

Raw study material, screenshots of private sessions, private source ledgers,
local paths, private board links and internal project names do not belong in
this repository. Run `python scripts/public_safety_scan.py` before publishing or
opening a pull request.

## License

MIT.
