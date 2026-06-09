# Real Profile Dispatch Smoke

Date: 2026-06-06

Purpose: prove that Hermes can dispatch a real specialist profile, preload the
Overkill Factory skill, execute a real scoped command and close through Kanban
with structured evidence.

## Failed Setup Attempt

A first disposable attempt forced `overkill-factory` before that skill was
available to the specialist profile runtime. The worker failed at startup with
an unknown-skill error.

Remediation:

- installed the complete `overkill-factory` skill package, including
  references and validator script, into the tested specialist profile homes;
- repeated the smoke with `overkill-factory` force-loaded on the card;
- left the failed attempt blocked with an explicit startup-failure reason, then
  removed the disposable board and workspace after capture.

This matters because a factory card that names a required skill must not kill a
worker before it can inspect the card.

## Successful Dispatch

Worker:

- profile: `public-safety-gate`;
- forced skill: `overkill-factory`;
- runtime path: Hermes dispatcher spawned a real worker process;
- workspace: disposable public repository clone;
- task type: Factory v3.5 R1 public-safety smoke.

Observed result:

- task moved from `ready` to `running` by Hermes dispatch;
- worker called `kanban_show`;
- worker ran `python3 scripts/public_safety_scan.py`;
- scanner output was `OK`;
- worker verified the result artifact existed;
- worker called Kanban completion with Receipt Five metadata;
- final status: `done`;
- run outcome: `completed`;
- run duration: about 46 seconds;
- completion metadata included `receipt_five`, `kanban_transition_event` and
  `public_safety_result`;
- disposable board and workspace were removed after capture.

## Boundary

This is real specialist-profile dispatch and real public-safety execution. It
does not prove that every specialist can perform product-specific work, nor does
it replace production Product Face proof, real onchain Auditor execution,
provider-backed remote proof or human approval.
