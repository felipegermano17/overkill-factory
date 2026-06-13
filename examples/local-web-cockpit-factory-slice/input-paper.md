# Local-First Factory Web Cockpit Input

## Request

Create a local-first Factory Web Cockpit through the Overkill Factory process.
The cockpit is for open-source operators who run the factory locally and decide
for themselves whether to publish it.

The operator must not hand-design or hand-implement the cockpit outside the
factory. The factory must produce the Product SOT, Method Contract, Product
Experience plan, Product Face Packet, security plan, worker packets and proof
requirements before implementation starts.

## Source Facts

- The cockpit must consume structured factory status snapshots and runtime
  contracts, not chat memory or raw logs.
- Discord is optional projection and approval inbox, not canonical state.
- Dense inspection, comparison, replay and long-running control belong in a
  local web cockpit unless another surface proves better.
- The previous poor Control Floor visual style is an anti-pattern. A generic
  AI dashboard look is a blocking Product Face defect.
- Public artifacts must not contain private paths, private Discord ids, raw
  screenshots from a private runtime, secrets or internal workspace evidence.

## Required Operator Jobs

- See portfolio state across projects or runs.
- See current factory phase and next safe action.
- See gates passed, failed, missing or stale.
- See blockers, owner and unblock condition.
- See parallel lanes, worktrees and execution state.
- See worker activity, review state and evidence refs.
- Inspect an evidence graph without rendering private raw evidence.
- Replay timeline/audit trail.
- Distinguish request, approval, done, blocked, released and superseded states.
- Run locally as an open-source user.

## Non-Goals

- No single-operator hosted service.
- No private Discord or private server coupling.
- No cockpit source-of-truth role.
- No implementation before gates are ready.
- No generic dashboard filler.
