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
factoryctl phase-engine --card examples/minimal-hermes-project/card.md
factoryctl route-registry --route-class product_creation
factoryctl operator-interface --primary-interface telegram --out .tmp/operator-interface-profile.json
factoryctl validate-operator-interface .tmp/operator-interface-profile.json
factoryctl start-conversation --operator-interface .tmp/operator-interface-profile.json --source-envelope-ref external:operator-source-envelope --out .tmp/factory-start-conversation.json
factoryctl validate-start-conversation .tmp/factory-start-conversation.json
factoryctl intake --route-class product_creation --request-type product_new --signal-type product_paper --summary "Public-safe product brief enters source resolution and understanding confirmation." --source-ref external:source-card-product-brief --out .tmp/product-intake.json
factoryctl validate-signal-intake .tmp/product-intake.json
factoryctl intake --route-class bug_repair --request-type bug --signal-type bug_report --summary "Public-safe bug report enters reproduction and regression gates." --source-ref external:source-card-bug-001 --out .tmp/bug-intake.json
factoryctl validate-signal-intake .tmp/bug-intake.json
factoryctl source-resolution --intake templates/universal-signal-intake.json --intake-ref templates/universal-signal-intake.json --out .tmp/source-resolution-packet.json
factoryctl validate-source-resolution templates/source-resolution-packet.json
factoryctl source-ledger --source-resolution templates/source-resolution-packet.json --source-ref external:source-card-product-brief --out .tmp/product-source-ledger.json
factoryctl validate-source-ledger templates/product-source-ledger.json
factoryctl understanding-confirmation --source-ledger templates/product-source-ledger.json --operator-response-ref external:sanitized-operator-understanding-confirmed --confirmed --out .tmp/operator-understanding-confirmation.json
factoryctl validate-understanding-confirmation templates/operator-understanding-confirmation.json
factoryctl briefing-package --operator-interface templates/operator-interface-profile.json --artifact-type product_sot --artifact-ref templates/product-sot.json --decision-required --out .tmp/operator-briefing-package.json
factoryctl validate-briefing-package templates/operator-briefing-package.json
factoryctl outcome-contract --source-ledger templates/product-source-ledger.json --operator-understanding-confirmation-ref external:sanitized-operator-understanding-confirmed --out .tmp/outcome-contract.json
factoryctl validate-outcome-contract templates/outcome-contract.json
factoryctl product-sot --outcome-contract templates/outcome-contract.json --out .tmp/product-sot.json
factoryctl validate-product-sot templates/product-sot.json
factoryctl full-scope-coverage --product-sot templates/product-sot.json --out .tmp/full-product-sot-scope-coverage.json
factoryctl validate-full-scope-coverage templates/full-product-sot-scope-coverage.json
factoryctl method-contract --full-scope-coverage templates/full-product-sot-scope-coverage.json --out .tmp/method-contract.json
factoryctl validate-method-contract templates/method-contract.json
factoryctl method-engines --engine-id spec_first_sdd
factoryctl validate-method-engines templates/method-engine-registry.json
factoryctl product-creation-plan --method-contract templates/method-contract.json --out .tmp/product-creation-plan.json
factoryctl validate-product-creation-plan templates/product-creation-plan.json
factoryctl product-implementation-readiness --product-creation-plan templates/product-creation-plan.json --out .tmp/product-implementation-readiness.json
factoryctl validate-product-implementation-readiness templates/product-implementation-readiness.json
factoryctl operating-systems --os-id hermes_worker_runtime_os
factoryctl validate-operating-systems templates/factory-operating-system-registry.json
factoryctl operating-system-scorecard --out .tmp/factory-runs/operating-systems/factory-operating-system-scorecard.json
python scripts/hermes_runtime_proof.py --boards-json .tmp/hermes-runtime/boards.json --profile-list-text .tmp/hermes-runtime/profile-list.txt --status-text .tmp/hermes-runtime/status.txt --task-list-json .tmp/hermes-runtime/task-list.json --done-task-runs-json .tmp/hermes-runtime/done-task-runs.json --blocked-task-show-json .tmp/hermes-runtime/blocked-task-show.json --out .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json
factoryctl operating-system-scorecard --runtime-proof .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json --out .tmp/factory-runs/operating-systems/factory-operating-system-scorecard-runtime-proven.json
factoryctl validate-operating-system-scorecard .tmp/factory-runs/operating-systems/factory-operating-system-scorecard.json
python scripts/factory_completion_audit.py --runtime-proof .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json --out-dir .tmp/factory-runs/completion-os-check
factoryctl ready-work-unit-packets --product-creation-plan templates/product-creation-plan.json --product-implementation-readiness templates/product-implementation-readiness.json --forbidden-context-ref external:sanitized-off-limits-parallel-thread --out .tmp/ready-work-unit-packets
factoryctl validate-ready-work-unit-packets templates/ready-work-unit-packets.json
factoryctl validate-signal-corpus templates/universal-signal-golden-corpus.json
factoryctl signal-coverage --out .tmp/factory-runs/signal-coverage/factory-signal-coverage-scorecard.json
factoryctl v1-completion-gate --release-preflight .tmp/factory-runs/release/release-integration-preflight.json --github-actions-result PASS --open-v1-blockers 0 --open-prs 0
factoryctl validate-v1-completion-gate templates/factory-v1-completion-gate.json
factoryctl gate-report --card examples/minimal-hermes-project/card.md
factoryctl unblock-plan --card examples/minimal-hermes-project/card.md
factoryctl recovery-plan --card examples/minimal-hermes-project/card.md --receipt .tmp/receipt.json --worker-results-dir .tmp/worker-results
factoryctl help-next --card examples/minimal-hermes-project/card.md --worker-results-dir .tmp/worker-results --out .tmp/factory-help.json
factoryctl reconcile-board --board product-alpha --snapshot .tmp/hermes-board-snapshot.json --out .tmp/factory-board-reconcile-plan.json
factoryctl validate-reconcile-board .tmp/factory-board-reconcile-plan.json
factoryctl worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
factoryctl transition-plan --card examples/minimal-hermes-project/card.md --from-status draft --to-status ready
factoryctl status-snapshot --card examples/minimal-hermes-project/card.md --out .tmp/factory-status-snapshot.json
```

`validate-signal-intake` checks the first routing contract for any incoming
signal: paper, idea, bug, repo, incident, release, research, UX, analytics,
security, docs, migration, refactor or agent/model change. It requires a known
route, required artifacts, public-safe references, explicit non-human recovery
and execution blocked until the factory has enough source and scope.

`phase-engine` computes the active factory frontier from materialized artifacts,
not from agent memory, card title, comments or the declared `phase` alone. It
emits `factory_phase_engine_state` with the computed phase, computed frontier,
next required artifact, allowed current workers and human-gate allowance. A card
that declares a later phase such as F9 while the computed frontier still needs
`operator_briefing_package` or `method_contract` is blocked before the operator
is asked for a decision.

`reconcile-board` applies that rule to a Hermes/Kanban board snapshot. It is the
deterministic no-idle decision contract: running work is observed, ready work is
left to native Hermes dispatch, missing canonical cards become board-contract
repair, and a single canonical card can create only the next artifact selected
by the phase engine. It must not ask for a human gate unless
`phase_engine.human_gate_allowed=true` and the decision package is complete.
Unlike the public template validation path, board reconciliation runs the phase
engine in runtime-strict mode: `templates/...`, `source-ledger.md`,
`factoryctl:gate-report`, bare scaffold refs and placeholder packets copied from
`templates/vfinal-factory-card.json` do not count as materialized product
evidence. A live board must carry product-specific artifacts before it can move
from intake to SOT, method, architecture, readiness or execution.
The reconcile task contract includes `workflow_template_id=overkill-vfinal`,
the computed `current_step_key`, and a fallback `kanban_workflow_binding` in the
task body so Hermes/Kanban state, not chat context, carries the current phase.
For Solana/onchain cards at F4 or later, a missing Solana AI Kit provider or
usage receipt is a factory-owned route defect and becomes a bounded repair task,
not an optional architecture opinion and not an operator approval question.

`route-registry` exposes the canonical route matrix used by the validators:
route class, request types, signal types, required artifacts, workers, recovery
policy and Hermes boundary. `operator-interface` records the primary human
conversation surface, such as Telegram, Discord or Cockpit. It makes proactive
notifications, attachment support and summary limits explicit, so the operator
does not need to poll the bot for status. `start-conversation` is the
conversational pre-start packet: the manager can ask open product-understanding
questions and compile the confirmed conversation before a formal factory start
request exists. It does not create Hermes boards or cards.

`intake` builds a valid Universal Signal Intake from that registry without
executing work. `source-resolution` turns a valid
intake into the next factory-owned source-resolution handoff packet, keeping
Product SOT ungenerated and execution blocked until the source ledger, route
artifacts, gates and workers pass. `source-ledger` materializes that handoff as
a product source ledger with public-safe refs, claim table, unresolved gaps and
the next factory-owned artifact. It still does not generate Product SOT or allow
execution. `understanding-confirmation` summarizes what the factory believes the
product is, asks the operator for a concise confirmation or correction, and
blocks Product SOT until that understanding is confirmed. It is not execution
approval and it must not ask the operator to reconcile internal factory
bookkeeping. `briefing-package` prepares a deep operator review package for
important artifacts such as Product SOT, architecture or security architecture:
short channel projection plus markdown and PDF attachments, with optional
diagram, video or audio explainer slots. `outcome-contract` turns the source ledger and confirmed
understanding into a bounded product or route outcome without treating the input
as Product SOT and without allowing execution. `product-sot` turns that outcome
into the first Product SOT and keeps execution blocked until full scope coverage,
method contract, readiness and gates pass. `full-scope-coverage` accounts for every Product SOT requirement before
method routing, so execution slices cannot silently become scope cuts.
`method-contract` turns that coverage into factory-owned method, artifact,
worker, gate and evidence requirements without handing DDD/BDD/spec choices to
the operator. `method-engines` exposes the Method OS registry that maps selected
methods to executable method engines such as spec-first SDD, test-first TDD,
BDD, discovery/research, security-first, design-first, legacy diagnosis and
incident-first. A method label alone cannot authorize execution.
`product-creation-plan` turns the Method Contract into a complete
product decomposition with work units, proof ids, blockers, stop rules,
reconciliation and the next readiness gate, while keeping execution blocked.
`product-implementation-readiness` checks that Product Creation Plan work units
are aligned enough to materialize only explicit ready units, or blocks with
named owners and human decisions.
`ready-work-unit-packets` turns those explicit `ready_work_units` into
deterministic execution requests without mutating live Hermes, without exposing
private refs and without allowing any complete-product claim from a bounded
slice. Each packet carries a `context_boundary` and a resolved
`work_unit_context_packet`: workers may inspect only the named allowed refs and
must receive the owner worker's required inputs, such as `done_definition`,
`phase`, `risk_effective`, `surfaces`, rollback or human-gate state when that
profile requires them. Broad repo history search is forbidden. If required
context is missing, stale, forbidden, ambiguous or only named without a resolver,
validation blocks materialization and the repair route stays factory-owned
instead of asking the operator to coordinate. `--forbidden-context-ref` is
repeatable and is intended for public-safe refs that must stay outside the
worker's search space during a run.
`ready-work-unit-hermes-plan` prepares the blocked-first Hermes materialization
contract for those packets. The live Hermes adapter then has a strict sequence:
collect route readiness, materialize blocked tasks, release exactly the verified
blocked tasks to `ready`, and only then run the native dispatch wrapper. Release
does not dispatch workers and dispatch does not complete the product. The
materialization plan copies the same `context_boundary` into each Hermes task
contract, along with the same `work_unit_context_packet`, so runtime workers
receive both the bounded-search rule and the resolved context contract proven by
the packet validator.
`validate-signal-corpus` and `signal-coverage` prove that the public
Golden Corpus covers every known route without treating contract coverage as
production readiness.

`operating-systems` exposes the canonical OS registry: the factory-wide owners
for Product Truth, Method, Authority, Hermes Runtime, Evidence, Domain Packs,
Operator Experience, Security/Release, Product Quality, Velocity/Cost and
Learning. `validate-operating-systems` checks the registry shape and semantic
guardrails: every P0 OS has an issue, every OS has a runtime boundary and
fail-closed rules, and the registry itself cannot claim product-specific
production readiness. `operating-system-scorecard` turns the registry plus an
optional completion audit into a readiness scorecard. It exits non-zero while
P0 OS work is planned, blocked pending runtime proof or mapped to active
completion blockers. That is deliberate fail-closed behavior, not a CLI crash.
`hermes_runtime_proof.py` builds the public-safe runtime proof from read-only
Hermes evidence; passing that proof with `--runtime-proof` can prove the Hermes
Worker Runtime OS without publishing raw private board content. A passing OS
scorecard is kernel/runtime-spine evidence only. Product-specific completion
still needs Receipt Five, current worker results, release evidence and any
required human-gate records. `factory_completion_audit.py --runtime-proof`
consumes the same proof to clear runtime-backed audit requirements while keeping
product/release/security requirements blocked until product-specific evidence
exists.

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

## Operator Bridge Commands

`scripts/factory_bridge.py` is the secondary operator bridge helper. Use it when
Codex or another assistant needs a durable operator inbox without acting as a
factory worker.

```bash
python scripts/factory_bridge.py summarize-inbox --text
python scripts/factory_bridge.py classify-prompt --prompt "status da fabrica"
python scripts/factory_bridge.py source-envelope --run-id example-run --project-mode new_project --operator-goal "Start a new product project." --source-ref external:operator:brief --out .tmp/factory-runs/example/source-envelope.json
python scripts/factory_bridge.py start-request --run-id example-run --project-mode new_project --operator-goal "Start a new product project." --source-envelope-ref external:operator:source-envelope --out .tmp/factory-runs/example/start-request.json
python scripts/factory_bridge.py handoff --run-id example-run --out .tmp/factory-runs/example/bridge-handoff.json
```

Bridge output is observability and operator response material. It does not
replace Hermes, worker results, human gate records or Receipt Five.

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

### `scripts/factory_production_gate_receipts.py`

Materializes the public-safe receipts consumed by
`scripts/factory_production_readiness.py`:

```bash
python scripts/factory_production_gate_receipts.py
python scripts/factory_production_gate_receipts.py --runtime-status-evidence .tmp/factory-runs/hermes-live/hermes-runtime-readonly-evidence.json
python scripts/factory_production_gate_receipts.py --no-write
```

Materialization success is not production approval. The script fails closed by
writing `BLOCKED` receipts when live Hermes, private Control Tower evidence or
release integration proof is not ready. The aggregate gate remains
`factory_production_readiness.py`.

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
QVG contract for the product-shaped validation fixture, or pass `--graph-contract` for a
different Product SOT/capability-pack set.

```bash
python scripts/production_full_product_worker_graph.py --no-write
python scripts/production_full_product_worker_graph.py --graph-contract path/to/production-full-product-graph.contract.json
```

The script validates evidence lanes. It does not create missing worker evidence,
approve human gates, release production, or make Product Face proof reusable by
declaration alone.
