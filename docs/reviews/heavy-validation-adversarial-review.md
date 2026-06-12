# Heavy Validation Adversarial Review

> Document status: HISTORICAL EVIDENCE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This is not the current factory rule; old "Still open" notes are snapshots unless promoted into current runtime gates or the active risk register.

This file consolidates critical review feedback from parallel reviewers during
the heavy validation battery.

## Security Critic

Score before fixes: 6.8/10.

Key criticism:

- public worker packets leaked absolute local paths;
- public worker registry had only 12 workers while the CLI had 27;
- public repo release did not require Codex Security;
- security was mostly routed, not executed;
- supply chain controls were still shallow.

Actions taken:

- redacted `source_card_path`;
- regenerated worker packets;
- expanded public worker registry to all 27 workers;
- added registry/schema drift tests;
- made Codex Security trigger for code, CI, supply-chain, public and agentic
  surfaces;
- kept full security scan as a remaining real-execution gate.

## Product Face Critic

Score before fixes: 7.4/10.

Key criticism:

- Product Face was routed but not proven;
- no blocking contract existed for screenshots, states, accessibility, overlap
  and mobile evidence;
- pre-decomposition Product Face proof was not enforced.

Actions taken:

- added `schemas/product-face-result.schema.json`;
- added Product Face completion validation;
- added negative and positive tests;
- updated the Hermes adapter patch to require Product Face result metadata for
  product-facing completion.

Still open:

- real browser proof must run against a real UI.

## Agent/Hermes Operability Critic

Score before fixes: 7.6/10.

Key criticism:

- required-only helps but does not define queues;
- Hermes still does not automatically fan out workers;
- remote proof lacked hard runtime-contract fields;
- update compatibility is marker-based, not disposable-runtime proof.

Actions taken:

- added `--required-only`;
- added aggregate `gate_status`;
- added remote proof contract fields;
- documented that automatic Hermes orchestration remains open.

Still open:

- implement worker queues: blocking-before-ready, blocking-before-done and
  advisory/review;
- implement Hermes worker fan-out and result reconciliation.

## Solana/Quasar/Auditor Critic

Score before fixes: 7.0/10.

Key criticism:

- Auditor was mandatory by contract but not executed against real Quasar code;
- preflight result could be mistaken for code-audit PASS;
- no schema required corpus, vectors, instruction matrix or state model.

Actions taken:

- added `schemas/auditor-result.schema.json`;
- added auditor-result validation;
- changed dry-pilot Auditor preflight from `PASS` to `WAIVED`;
- added tests blocking preflight-as-PASS.

Still open:

- build/import real Quasar source;
- run real Auditor;
- add build, tests, compute profile and fuzz/property coverage.
