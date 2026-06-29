# Swiss Watch Reliability Program

> Document status: CURRENT MAINTAINER EXECUTION PLAN.
> Current authority: Hermes native runtime state, `factory/scripts/factoryctl.py`, adapters,
> schemas, tests and live Hermes evidence.
> Runtime boundary: This document is a reliability plan. It does not replace
> Hermes Kanban, factory contracts, Receipt Five, human gate records or tests.

## Mission

Make Overkill Factory operate like a Swiss watch without reducing the factory.
Every existing stage remains allowed to exist. The work is to make every gear
mesh correctly: autonomous when safe, blocked when necessary, secure by default,
fast enough to feel alive, and strict enough that shallow agent work cannot pass.

The factory must not become a mini-Hermes. The default answer is to use Hermes
native capability: Kanban graph state, parent dependencies, typed blocks,
dispatch, comments, runs, logs, attachments, schedules, notifications and worker
state. Overkill Factory adds native code only when Hermes has no suitable native
primitive or when the factory needs a product-method contract above the runtime.

## Non-Negotiables

1. Do not remove stages to make the system look simpler.
2. Do not let agents select route, phase, gate or promotion path from memory,
   prose, enthusiasm, title text or chat context.
3. Prefer Hermes-native graph/dependency/block/dispatch behavior over sidecar
   loops and factory-owned shadow schedulers.
4. Treat no-idle and watchdog code as integrity auditors and repair paths, not
   normal route authority.
5. A worker packet is assignment, not proof.
6. A PASS requires product-specific evidence, not generic template-shaped prose.
7. The operator is contacted only for real human decisions or missing operator
   input, never for internal dependency, capability, retry or repair states.
8. Public artifacts must stay public-safe. Runtime/private evidence stays in
   `.tmp/`, private evidence storage or operator-owned Hermes.
9. Every fix must produce a regression test or validator that catches the exact
   failure class again.
10. Before saying done, show evidence: command, result, changed files, remaining
    risk and next safe action.

## The Eight Workstreams

### 1. Gear Audit

Question for every phase: does this gear have explicit input, output, authority,
quality floor, timeout/retry behavior, proof and next gear?

Required gears:

- F0 sealed/source envelope
- F1 intake
- F2 source ledger/source resolution
- F3 understanding alignment
- F4 outcome/discovery
- F5 Product SOT
- F6 full-scope coverage
- F7 Method Contract
- F8 Product Experience/capability selection
- F9 architecture boundary
- F10 security/access/budget
- F11 Product Creation Plan
- F12 Decomposition Coverage Review
- F13 execution packets/work units
- F15 verification/review
- human gate event only when real decision is required
- Receipt Five
- release/block decision
- operations/learnback

Deliverables:

- phase-by-phase gear matrix with input/output/authority/proof.
- gap list: missing test, missing authority, missing proof, missing UX contract.
- one regression or validator per critical missing gear behavior.

### 2. Swiss Watch Scorecard

Measure each gear against five dimensions:

- Autonomy: advances safely without operator babysitting.
- Performance: avoids idle loops, duplicate remediation and slow recomputation.
- Security: fails closed, preserves boundaries and protects secrets/private refs.
- Quality: rejects shallow, generic or template-only worker output.
- UX: tells the operator exactly what matters, in the right language, only when
  human input is truly required.

Deliverables:

- scorecard schema/template if no existing contract is enough.
- `factoryctl` command only if this becomes a repeated operator/maintainer path.
- tests that fail when a required dimension silently disappears.

Hermes-native rule:

- If Hermes already exposes state needed for a score, read Hermes state. Do not
  create a parallel factory truth store.

### 3. Real Operator Experience First

Optimize the lived flow, not just the contract surface.

Representative target flow:

```text
operator material
-> understanding package
-> operator confirms/corrects
-> Product SOT with real depth
-> coverage/method/architecture/security/product experience
-> work units and worker execution
-> review rejects shallow work
-> repair stays on rails
-> Receipt Five proves completion or block
```

Deliverables:

- operator-experience regression scenarios for the above flow.
- clear expected operator messages for real human gates.
- tests proving dependency/capability/transient/review repair states do not page
  the operator as generic human approval.

### 4. Worker Quality Floors

Agents must stop passing with simplistic work.

Minimum rule:

- Every critical worker must have a quality floor that is specific enough for a
  reviewer or validator to reject shallow output.

Priority workers:

- product-sot-planner
- source-ledger-worker
- product-architect
- product-face/frontend-builder
- decomposition-planner
- independent-reviewer
- qa-verification-worker
- evidence-reconciler
- security-orchestrator and security specialists
- handoff-packer
- human-gate-clerk

Deliverables:

- quality-floor checklist per priority worker.
- worker result acceptance tests for generic/shallow output rejection.
- reviewer behavior that routes repair instead of accepting weak PASS.

Hermes-native rule:

- Use Hermes worker results, comments, attachments and task state as evidence.
  Factory code validates quality; it does not become a second worker runtime.

### 5. Stall Classification and No-Idle Reliability

The factory must classify stalled states exactly.

Critical states:

- dependency wait
- needs input
- capability acquisition
- transient retry/repair
- review failed
- repair completed but not reconciled
- worker terminal metadata present
- human gate required
- ready frontier exists
- graph invariant violation
- board truly idle

Deliverables:

- state matrix mapping state -> owner -> next safe action -> operator contact?
- regression tests for every state above.
- no-idle behavior proves it audits/repairs but does not become route authority.

Hermes-native rule:

- Current Hermes typed block and dependency state wins over factory prose.
- Parent edges and current status must beat historical event text when deciding
  whether a task is actually waiting.

### 6. Operator Experience Regression Suite

Create tests for experience failures, not only schemas.

Required scenario classes:

- no operator page for internal dependency.
- no operator page for capability search until search is complete and blocked.
- no duplicate remediation after self-evidenced repair PASS.
- no fake human gate from free-text gate wording.
- decision package delivered before decision question.
- Portuguese operator flow receives Portuguese owner-facing material.
- shallow Product SOT or shallow worker result is rejected.
- board with safe next action does not remain silently idle.
- failed review routes targeted repair, then re-review, then human gate only if
  real decision remains.

Deliverables:

- one test module or clearly named tests under existing test files.
- fixtures kept public-safe and minimal.
- tests run in CI without private runtime.

### 7. Systematic Fix Discipline

No patch roulette.

For every bug:

1. reproduce with a tight command.
2. identify root cause.
3. write or locate the red test.
4. implement the smallest root-cause fix.
5. run targeted test.
6. run relevant integration tests.
7. run public safety/secret safety when public surface or artifacts change.
8. record remaining risk.

Deliverables:

- each code change tied to a failure class.
- no broad refactor mixed with bug fix unless explicitly scoped.
- every accepted fix leaves behind a guardrail.

### 8. Factory Reliability Engineer Loop

Make reliability a continuous operating mode.

The loop:

```text
observe bad UX or runtime stall
-> classify exact failure class
-> reproduce locally or with public-safe fixture
-> fix root cause using Hermes-native primitive when available
-> add regression
-> update docs/skill only if behavior/pitfall changed
-> run validation battery
-> keep release notes honest
```

Deliverables:

- reliability backlog grouped by failure class, not vague complaints.
- release audit showing which failure classes were reduced.
- repeatable validation battery before claiming improvement.

## Immediate Execution Plan

### Phase A: Stabilize Current Main

A1. Reproduce the current failing unit test in isolation.

- Command: `python -m unittest tests.test_factory_concierge_discord_automation.FactoryConciergeDiscordAutomationTest.test_run_automation_empty_inboxes_posts_idle_health_receipt -q`
- Expected now: FAIL until root cause is fixed.

A2. Trace root cause through Discord automation channel/guild resolution.

- Files: `factory/scripts/factory_concierge_discord_automation.py`,
  `factory/scripts/factory_concierge_discord_bridge.py`,
  `factory/tests/test_factory_concierge_discord_automation.py`.

A3. Fix only the root cause.

- Must preserve Hermes/factory boundary.
- Must not add a new runtime path or sidecar scheduler.

A4. Verify.

- targeted failing test passes.
- full Discord automation/bridge tests pass.
- full unittest suite passes or any remaining failure is documented with command
  and root cause.

### Phase B: Prevent Local Runtime Artifacts From Breaking Validation

B1. Inspect why local `.worktrees/` appears in public safety scan.

B2. Decide by repo rule:

- if `.worktrees/` is a generated/transient local workspace, ignore or exclude it
  from public-safety discovery.
- if it contains material that belongs in public fixtures, move only the minimal
  public-safe fixture.

B3. Add a regression so local worktrees/private runtime materials do not cause a
false public-surface failure, while tracked public files remain scanned.

### Phase C: Build the Gear Matrix

C1. Generate or write the first gear matrix from existing workflow/contracts.

C2. Use existing sources first:

- workflow compiled plan
- phase graph contracts
- worker registry/profile bindings
- Hermes typed block policy
- Product Experience control plane
- security route contracts

C3. Add tests for any critical missing state.

### Phase D: Add Operator Experience Regression Cases

D1. Inventory existing tests for no-idle, human gate, operator interface,
Telegram/Discord, Product SOT and worker result acceptance.

D2. Add missing tests in the smallest existing test module that owns the behavior.

D3. Keep tests public-safe and deterministic.

### Phase E: Add Worker Quality Floors

E1. Start with Product SOT because shallow Product SOT poisons every downstream
phase.

E2. Define unacceptable shallow output patterns.

E3. Add a failing test proving shallow output is rejected.

E4. Add validator/worker acceptance logic only where existing contracts cannot
already express the rule.

E5. Repeat for architecture, Product Face, review and evidence reconciliation.

### Phase F: Prove Hermes-Native Runtime Direction

F1. Audit code paths that create scheduling, dependency, block, dispatch or
state-reconciliation behavior.

F2. For each path, answer:

- is Hermes native capability available?
- is factory code duplicating Hermes?
- can this become a Hermes adapter call, validator or contract instead of a
  parallel runtime behavior?

F3. Convert duplication into Hermes-native use where safe, with tests.

### Phase G: Validation Battery

Required before claiming improvement:

```bash
python factory/scripts/swiss_watch_audit.py --out .tmp/swiss-watch-audit.json --markdown .tmp/swiss-watch-audit.md
python factory/scripts/factoryctl.py doctor
python factory/scripts/factoryctl.py run minimal
python factory/scripts/validate_document_governance.py
python factory/scripts/generate_factory_reference_docs.py --check
python factory/scripts/validate_public_json_artifacts.py
python factory/scripts/validate_worker_profiles.py
python factory/scripts/validate_promise_implementation_map.py
python factory/scripts/factoryctl.py validate-v2-runtime-contracts
python factory/scripts/factoryctl.py validate-agent-skill-boundaries
python factory/scripts/factoryctl.py validate-reference-superiority
python factory/scripts/public_safety_scan.py
python factory/scripts/secret_safety_scan.py
python -m unittest discover -s tests -q
```

If a validation is intentionally blocked by local runtime state, the blocker must
be classified and either fixed or documented as non-public local state with a
regression preventing false release failures.

## First Success Criteria

The first complete reliability pass is not done until:

- current main has no unexplained test failure.
- local public/secret scans are meaningful and not polluted by private transient
  workspaces.
- at least one operator-experience regression catches a previously plausible bad
  UX path.
- at least one worker quality-floor regression rejects shallow output.
- the gear matrix exists and points to real contracts/tests, not prose-only
  promises.
- the plan remains Hermes-native: no new mini-Hermes runtime code is introduced.
