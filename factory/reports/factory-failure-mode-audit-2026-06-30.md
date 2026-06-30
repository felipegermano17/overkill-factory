# Overkill Factory failure-mode audit — 2026-06-30

Status: in progress
Scope: no-idle runtime, reducers, dispatch/guard lifecycle, worker blockers, artifact materialization, internal reviews, safety gates.

Mandate:
- Minimize avoidable stopped-factory scenarios.
- Do not count a live guard process as proof of useful work.
- Internal missing artifacts/contracts/reviews must self-repair.
- Real human gates remain explicit: cost/budget, production/mainnet/funds/custody/signing/credentials/authority decisions.

## Current high-risk architecture observations

1. `adapters/hermes/live_kanban_adapter.py` is a hotspot: ~11.5k lines, 291 top-level functions.
2. `no_idle()` is ~1,282 lines and mixes classification, reconcile preemption, task creation, stale id replacement, reducer outputs, and public sanitization.
3. `classify_no_idle_state()` is ~451 lines and encodes many overlapping blocker classes.
4. Recent fixes #551-#557 show the same architectural pattern: specific reducer/repair intent being masked by generic reconcile/board repair or stale task interpretation.
5. Guard/process liveness can be misleading unless tied to material progress: running/ready changes, blocker reduction, or distinct frontier work.

## Failure-mode matrix draft

| ID | Scenario | Symptom | Root risk | Current mitigation | Gap / audit question | Priority |
|---|---|---|---|---|---|---|
| FM-001 | Materialization blocker + unrelated TODO backlog | no-idle loops on `repair_board_contract`; Spawned=0 | specific repair preempted by generic board repair | PR #557 regression tests | Search for other targeted strategies missing from `targeted_legacy_repair_available` | P0 |
| FM-002 | Stale remediation id replay | no-idle returns terminal/done task id; no fresh worker starts | idempotency hides progress | PR #552 bounded stale replacement | Test all remediation creators, not only board reconcile | P0 |
| FM-003 | Review PASS instruction contains REVIEW FAIL wording | PASS review parsed as FAIL | body instructions mixed with terminal result | PR #556 | Verify all review parsers prefer events/comments/metadata over body templates | P0 |
| FM-004 | Completed repair readback interpreted as review FAIL | duplicate repair chain, done grows, blocker remains | repair tasks reused as authority | PR #553/#555 | Add lineage depth / duplicate-title loop monitor | P0 |
| FM-005 | Terminal repair counted as active repair | no new repair created although only done repair exists | active/terminal state conflation | PR #554 | Apply same rule to all repair classes | P0 |
| FM-006 | Guard/watchdog alive but no progress | user sees process running while factory stopped | guard dispatches on stale remediation id or loops empty | local active guard had no-progress breaker; repo watchdog now has `--max-unchanged-no-progress` test/logic | Keep CI green and ensure cron uses the versioned watchdog, not only local script | P0 |
| FM-006A | Stale remediation id presented as created remediation | watchdog says remediation created although no fresh worker can start | `remediation_task_id` truthy without checking `remediation_task_stale` | fixed locally with regression `test_watchdog_does_not_call_stale_remediation_id_created` | Merge/CI | P0 |
| FM-007 | Missing worker skill ref | worker crashes before work | manual card uses skill absent from target profile | skill doc updated | Add preflight in card creation / no-idle repair creator to reject invalid skills | P1 |
| FM-008 | Internal review-required blocker without reviewer card | worker blocks waiting for internal reviewer; no reducer creates review | no-idle lacks reviewer-card creation for some domains | manual WU-12 review created | Add generic internal-review-required detector/creator for `review-required:<profile>` | P0 |
| FM-009 | Done task without declared artifact readback | downstream trusts process done, but files absent | done != quality/evidence | missing declared artifact materializer exists | Audit whether all done transitions enforce artifact readback | P0 |
| FM-010 | False human/operator gate from forbidden text | factory asks user though text is only safety boundary | keyword-only gate classifier | existing mitigations in classifier | Fuzz classifier with forbidden_actions examples | P1 |
| FM-011 | True human gate suppressed as internal repair | unsafe automation attempts around mainnet/funds/signing | overbroad internal-materialization markers | external markers list | Add negative tests for mainnet/funds/custody/signing phrasing mixed with missing artifacts | P0 |
| FM-012 | Running worker stale/heartbeat dead | guard waits forever | running count without heartbeat freshness | Hermes dispatch reclaim maybe handles | Audit reclaim thresholds and active guard freshness checks | P1 |
| FM-013 | Ready task undispatched due to profile missing | ready>0 but Spawned=0 | assignee profile invalid/missing | profile discovery docs | Add ready-profile-invalid classification and repair/reassign path | P1 |
| FM-014 | Duplicate independent reviews | multiple auditors on same target, reducers race | idempotency missing/stale across manual/no-idle cards | some idempotency keys used manually | Enforce idempotency key pattern in review creators | P1 |
| FM-015 | Public/private leakage in audit/debug output | tokens/paths/task IDs leak into public surface | unsanitized debug/report | public_safety_scan | Include new audit reports in scan baseline | P0 |

| FM-016 | Active running task without deterministic runtime contract | no-idle returns `factory_phase_invariant_violation`; active worker may keep running while watchdog does not classify no-progress because running>0 | safety invariant detects the issue but has no automated containment/recovery path | existing tests assert blocking/no dispatch | Needs architecture decision: auto-block/reclaim unsafe active worker vs fail-loud operator event; do not silently observe | P0 |

| FM-017 | Internal review FAIL mentions PASS evidence and is reduced as PASS | blocked task incorrectly completed; repair skipped | PASS parser accepted generic ` pass` text | fixed locally: structured FAIL/BLOCK now wins over text; regression added | Merge/CI | P0 |
| FM-018 | Older review FAIL preempts newer review PASS | duplicate repair loop after valid PASS | FAIL reducer ran before considering latest PASS for same target | fixed locally: newer PASS timestamp suppresses older FAIL; regression added | Merge/CI | P0 |
| FM-019 | Done/malformed internal review request blocks fresh review forever | `review-required` blocker remains with no active reviewer | existing review detector counted `done` request tasks | fixed locally: only non-terminal review requests count as existing; regression added | Merge/CI | P0 |
| FM-020 | ISO timestamp in ready-work-unit materialization plan crashes ordering | no-idle aborts before classifying/reconciling | `int(completed_at)` on ISO strings | fixed locally: uses `parse_timestamp_seconds`; regression added | Merge/CI | P0 |
| FM-021 | Directed materialization remediation replays stale done task | blocker persists, no fresh repair spawned | idempotency replay returned terminal repair task | fixed locally for materialization repair with bounded stale replacement; regression added | Extend same pattern to package/review/post-review repairs | P0 |

| FM-022 | Materialization text mixed with external API/private key requirement | no-idle creates internal repair for work requiring operator/credential input | external markers did not include API/private-key phrases | fixed locally: external API/private key/wallet key markers route to operator input, not materialization repair; regression added | Merge/CI | P1 |
| FM-023 | Complete human-gate package mentions `target_repo_paths`/scan scope as context | decision-ready gate is misclassified as operator input | contextual operator-input markers outranked complete human gate packet | fixed locally: complete decision package wins unless explicit operator input is requested; regression added | Merge/CI | P1 |

| FM-024 | Ready work exists while another worker is running | ready tasks can sit idle if orchestrator reads only `running_work_exists` | running branch hid `native_dispatch_required_next` and ready refs | fixed locally: running state now exposes ready/running refs and dispatch signal when ready exists | Merge/CI | P1 |

## Live-board observations during audit

- 2026-06-30T12:32Z: board had `blocked=3`, `running=1`, `todo=14`; running task was `Repair factory materialization contracts` and blockers were WU-09/WU-10/WU-13 input/capability materialization issues.
- 2026-06-30T12:39Z: after the materialization repair completed, `no-idle --create-remediation` reduced internal review PASS blockers; board moved to `blocked=1`, `done=172`, `running=1`, `todo=12`.
- Remaining live issue at that point: `F15/WU-17 - Test automation and remote proof harness` blocked for missing input/capability materialization, while WU-18 was running without explicit `current_step_key`/workflow fields. This matches FM-016: runtime contract invariant detection exists but should be made fail-loud in watchdog supervision.

## Immediate audit commands/baseline

- `python3 -m pytest tests/test_hermes_live_kanban_adapter.py -q` baseline after #557: 163 passed, 3 subtests passed.
- `python factory/scripts/public_safety_scan.py` baseline after #557: OK.

## Next work

1. Run targeted watchdog tests and inspect whether repo watchdog has no-progress behavior matching local guard.
2. Search all `remediation_strategy` values and confirm each either preempts generic board repair or intentionally yields.
3. Add tests for internal review-required reviewer creation where no reviewer card exists.
4. Add negative tests for real human gates mixed with materialization language.
5. Add tests for running heartbeat stale/no-progress guard behavior.
