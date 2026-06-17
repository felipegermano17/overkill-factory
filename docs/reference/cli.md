# CLI Reference

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: scripts/factoryctl.py, README.md, tests/
> Runtime boundary: The CLI creates and validates local artifacts. Hermes remains
> the runtime source of truth for real cards and transitions.

## Operator Commands

### `factoryctl doctor`

Checks local install health, package metadata, public entrypoints, the minimal
example and whether Hermes runtime checking is configured. It does not claim a
real Hermes E2E harness.

```bash
factoryctl doctor
factoryctl doctor --json
```

### `factoryctl run minimal`

Runs the public first-value path through the single CLI entrypoint.

```bash
factoryctl run minimal
factoryctl run minimal --out .tmp/quickstart-result.json --packets-out .tmp/minimal-worker-packets
```

### `factoryctl init`

Creates a Hermes-friendly operator workspace for a product.

```bash
factoryctl init --out ../my-product-factory --project-name my-product
```

## Card And Worker Commands

```bash
factoryctl validate-card examples/minimal-hermes-project/card.md
factoryctl route-registry --route-class product_creation
factoryctl intake --route-class bug_repair --request-type bug --signal-type bug_report --summary "Public-safe bug report enters reproduction and regression gates." --source-ref external:source-card-bug-001 --out .tmp/bug-intake.json
factoryctl validate-signal-intake templates/universal-signal-intake.json
factoryctl source-resolution --intake templates/universal-signal-intake.json --intake-ref templates/universal-signal-intake.json --out .tmp/source-resolution-packet.json
factoryctl validate-source-resolution templates/source-resolution-packet.json
factoryctl source-ledger --source-resolution templates/source-resolution-packet.json --source-ref external:source-card-product-brief --out .tmp/product-source-ledger.json
factoryctl validate-source-ledger templates/product-source-ledger.json
factoryctl outcome-contract --source-ledger templates/product-source-ledger.json --out .tmp/outcome-contract.json
factoryctl validate-outcome-contract templates/outcome-contract.json
factoryctl product-sot --outcome-contract templates/outcome-contract.json --out .tmp/product-sot.json
factoryctl validate-product-sot templates/product-sot.json
factoryctl full-scope-coverage --product-sot templates/product-sot.json --out .tmp/full-product-sot-scope-coverage.json
factoryctl validate-full-scope-coverage templates/full-product-sot-scope-coverage.json
factoryctl method-contract --full-scope-coverage templates/full-product-sot-scope-coverage.json --out .tmp/method-contract.json
factoryctl validate-method-contract templates/method-contract.json
factoryctl product-creation-plan --method-contract templates/method-contract.json --out .tmp/product-creation-plan.json
factoryctl validate-product-creation-plan templates/product-creation-plan.json
factoryctl product-implementation-readiness --product-creation-plan templates/product-creation-plan.json --out .tmp/product-implementation-readiness.json
factoryctl validate-product-implementation-readiness templates/product-implementation-readiness.json
factoryctl ready-work-unit-packets --product-creation-plan templates/product-creation-plan.json --product-implementation-readiness templates/product-implementation-readiness.json --out .tmp/ready-work-unit-packets
factoryctl validate-ready-work-unit-packets templates/ready-work-unit-packets.json
factoryctl validate-signal-corpus templates/universal-signal-golden-corpus.json
factoryctl signal-coverage --out .tmp/factory-runs/signal-coverage/factory-signal-coverage-scorecard.json
factoryctl v1-completion-gate --release-preflight .tmp/factory-runs/release/release-integration-preflight.json --github-actions-result PASS --open-v1-blockers 0 --open-prs 0
factoryctl validate-v1-completion-gate templates/factory-v1-completion-gate.json
factoryctl gate-report --card examples/minimal-hermes-project/card.md
factoryctl unblock-plan --card examples/minimal-hermes-project/card.md
factoryctl recovery-plan --card examples/minimal-hermes-project/card.md --receipt .tmp/receipt.json --worker-results-dir .tmp/worker-results
factoryctl help-next --card examples/minimal-hermes-project/card.md --worker-results-dir .tmp/worker-results --out .tmp/factory-help.json
factoryctl worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
factoryctl transition-plan --card examples/minimal-hermes-project/card.md --from-status draft --to-status ready
factoryctl status-snapshot --card examples/minimal-hermes-project/card.md --out .tmp/factory-status-snapshot.json
```

`validate-signal-intake` checks the first routing contract for any incoming
signal: paper, idea, bug, repo, incident, release, research, UX, analytics,
security, docs, migration, refactor or agent/model change. It requires a known
route, required artifacts, public-safe references, explicit non-human recovery
and execution blocked until the factory has enough source and scope.

`route-registry` exposes the canonical route matrix used by the validators:
route class, request types, signal types, required artifacts, workers, recovery
policy and Hermes boundary. `intake` builds a valid Universal Signal Intake
from that registry without executing work. `source-resolution` turns a valid
intake into the next factory-owned source-resolution handoff packet, keeping
Product SOT ungenerated and execution blocked until the source ledger, route
artifacts, gates and workers pass. `source-ledger` materializes that handoff as
a product source ledger with public-safe refs, claim table, unresolved gaps and
the next factory-owned artifact. It still does not generate Product SOT or allow
execution. `outcome-contract` turns the source ledger into a bounded product or
route outcome without treating the input as Product SOT and without allowing
execution. `product-sot` turns that outcome into the first Product SOT and keeps
execution blocked until full scope coverage, method contract, readiness and gates
pass. `full-scope-coverage` accounts for every Product SOT requirement before
method routing, so execution slices cannot silently become scope cuts.
`method-contract` turns that coverage into factory-owned method, artifact,
worker, gate and evidence requirements without handing DDD/BDD/spec choices to
the operator. `product-creation-plan` turns the Method Contract into a complete
product decomposition with work units, proof ids, blockers, stop rules,
reconciliation and the next readiness gate, while keeping execution blocked.
`product-implementation-readiness` checks that Product Creation Plan work units
are aligned enough to materialize only explicit ready units, or blocks with
named owners and human decisions.
`ready-work-unit-packets` turns those explicit `ready_work_units` into
deterministic execution requests without mutating live Hermes, without exposing
private refs and without allowing any complete-product claim from a bounded
slice.
`ready-work-unit-hermes-plan` prepares the blocked-first Hermes materialization
contract for those packets. The live Hermes adapter then has a strict sequence:
collect route readiness, materialize blocked tasks, release exactly the verified
blocked tasks to `ready`, and only then run the native dispatch wrapper. Release
does not dispatch workers and dispatch does not complete the product.
`validate-signal-corpus` and `signal-coverage` prove that the public
Golden Corpus covers every known route without treating contract coverage as
production readiness.

`v1-completion-gate` is the finish-line gate for the public Factory v1 kernel.
It does not search forever for new work. It requires current release preflight,
GitHub check state, open PR count and open v1 blocker count, then classifies
remaining findings as `v1_blocker`, `vnext` or `not_planned`. `PASS` allows
closing Factory v1 public kernel work; it does not claim product-specific
completion, hosted service release or universal runtime proof.

`help-next` reads the card, workflow catalog and gate report, then separates the
factory's next action from bounded user decisions. With `--receipt` or
`--worker-results-dir`, it also exposes active recovery routes so a recoverable
non-human block points back into the factory-owned repair path instead of asking
the operator to infer the next worker from prose. It does not dispatch workers,
approve gates, or make the operator coordinate schemas, worker packets or
internal evidence machinery.

`status-snapshot` projects card, gate, lane and evidence state for operators. It
does not replace Hermes, card contracts, gate reports or Receipt Five as the
source of truth.

`recovery-plan` emits machine-readable recovery routes for blocked factory
work. With `--receipt` or `--worker-results-dir`, it also turns `BLOCKED`
worker/review results into semantic repair routes. It does not execute workers
or unblock cards. Recovery work must be materialized as native Hermes Kanban
tasks, links, comments, runs and block/unblock events.

## Evidence And Truth Commands

```bash
factoryctl export-hermes-evidence --board my-board --workspace ../my-hermes-workspace --out .tmp/factory-runs/hermes-evidence/sanitized-package.json
factoryctl evidence-graph --card examples/minimal-hermes-project/card.md --worker-results-dir .tmp/worker-results --out .tmp/factory-runs/evidence/evidence-graph.json
factoryctl readiness-ledger --card examples/minimal-hermes-project/card.md --evidence-graph .tmp/factory-runs/evidence/evidence-graph.json --out .tmp/factory-runs/readiness/readiness-truth-ledger.json
factoryctl truth --target issue-94 --card examples/minimal-hermes-project/card.md --out .tmp/factory-runs/truth/truth-packet.json
factoryctl prepilot-checklist --evidence-graph .tmp/factory-runs/evidence/evidence-graph.json --readiness-ledger .tmp/factory-runs/readiness/readiness-truth-ledger.json
```

These commands are JSON-first. They summarize cards, worker results, receipts,
readiness and sanitized Hermes evidence without importing raw private runtime
evidence into the public repository. A weaker truth layer such as
`contract_exists` or `runtime_enforced` must not be read as
`production_ready`.

### Test Runner Fallback

Worker packets should run commands as argv lists, not shell strings. Use
`scripts/safe_shell.py` as the local pattern when a packet needs a fallback for
runner failures, timeouts, or Windows sandbox launch errors. A fallback result
is `BLOCKED` until the same argv is rerun successfully or replaced by a
traceable worker result.

## Maintainer Scripts

Scripts outside `factoryctl` are maintainer tools or compatibility entrypoints.
Promote repeated operator flows into `factoryctl` instead of adding another
script name to the public path.

### `scripts/factory_self_improvement.py`

Creates dry-run self-improvement artifacts for maintainers:

```bash
python scripts/factory_self_improvement.py reference-registry --out .tmp/reference-source-registry.json
python scripts/factory_self_improvement.py missing-capability-plan --gate-report .tmp/gate-report.json --out .tmp/missing-capability-plan.json
python scripts/factory_self_improvement.py learnback-issues --record .tmp/execution-learnback-record.json --out .tmp/issue-candidates.json
python scripts/factory_self_improvement.py learning-proposals --record .tmp/execution-learnback-record.json --out .tmp/learning-proposals.json
python scripts/factory_self_improvement.py issue-intake --config templates/owner-issue-intake-config.json --issues .tmp/issues.json --out .tmp/issue-intake-report.json
python scripts/factory_self_improvement.py governance-audit --out .tmp/ai-codebase-governance-report.json
```

These commands do not dispatch Hermes, activate workers, post GitHub comments or
approve gates. They prepare public-safe plans and candidates for review.

### `scripts/production_full_product_worker_graph.py`

Builds a production-scoped worker graph from a product contract. Use the default
QVG contract for the public validation product, or pass `--graph-contract` for a
different Product SOT/capability-pack set.

```bash
python scripts/production_full_product_worker_graph.py --no-write
python scripts/production_full_product_worker_graph.py --graph-contract path/to/production-full-product-graph.contract.json
```

The script validates evidence lanes. It does not create missing worker evidence,
approve human gates, release production, or make Product Face proof reusable by
declaration alone.
