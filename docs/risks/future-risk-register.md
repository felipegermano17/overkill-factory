# Future Risk Register

This register captures risks the factory can already see but has not fully
proven in real product pilots.

| Risk | What Can Break | Current Mitigation | Still Needed |
|---|---|---|---|
| Process becomes too heavy | Small tasks drown in contracts | Factory gates are opt-in and risk-tiered | Measure cycle time across multiple pilots |
| Agents confuse packet with result | Worker request is treated as evidence | Closure summary and Receipt Five distinguish required vs delivered | Stronger reconciler in `factoryctl.py` |
| Security remains generic | A single scan misses AppSec, AI, cloud or onchain risks | Security control matrix and specialist workers | Automated routing and domain-specific fixtures |
| Public repo leaks private context | Internal names, paths, source extraction or private board links enter docs | `public-safety-gate` and `public_safety_scan.py` | CI enforcement on every PR |
| Hermes update breaks gates | Upstream update removes adapter symbols or bypasses exit codes | compatibility manifest, runbook, check script and adapter patch chain | Disposable runtime update pipeline |
| Dashboard/API bypasses CLI gates | UI path mutates Kanban without same validation | Dashboard `ready` patch and live smoke; required update smokes | `done`, API and worker-route live test harness |
| AutoReview over-trusted | Automated review is treated as approval | AutoReview cannot replace independent or human gates | Review result schema and blocking-finding policy |
| Remote proof leaks secrets | Testbox/remote runner receives sensitive data | Secrets denied by default, TTL/cost/cleanup required | Secret allowlist scanner and remote proof fixtures |
| Handoff becomes prose | Handoff omits state, constraints or evidence | Handoff Packer contract | Replay validator with hashes/artifact checks |
| Memory poisoning | Old or malicious context becomes truth | Memory Steward, trust tier, freshness, source status | Memory test suite and poisoning examples |
| Product Face is under-tested | UI looks complete but lacks states/mobile/a11y | Product Face worker and packet | Automated browser/a11y/mobile proof runner |
| Onchain proof is shallow | Auditor preflight mistaken for real Quasar audit | Auditor result must state preflight vs real code audit | Real Quasar source pilots |
| Human gate becomes rubber stamp | Agents pressure approval without clear packet | Human Gate Clerk and R3/R4 packet | Approval UI/record with explicit scope and risk owner |
| Closed workers get promoted too early | A worker becomes rigid before the task shape is stable | open/closed promotion rule | Evals and repetition threshold tracking |
| CI is too thin | Local tests pass but package/release path breaks | CI added for unit, compatibility and public scan | Patch-apply CI against Hermes checkout |

## Review Cadence

Update this register after every pilot, failed gate, Hermes update and public
release. F18 learning loop should turn repeated risks into tests, workers,
skills or schema rules.
