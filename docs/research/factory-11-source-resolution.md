# Factory 11 Source Resolution

This file records public-safe source decisions for Factory 11. It is not a raw
research dump.

## Source Notes

| Source | Status | Factory Decision |
|---|---|---|
| Shann Holmberg post on open vs closed specialists | confirmed_source | Use open specialists for exploration and judgment; promote to closed specialists only after repetition, predictable input and verifiable output. |
| Steipete posts on AutoReview, Crabbox and compact skills | confirmed_source | Add AutoReview as a pre-landing gate; use remote proof only when local proof is insufficient; keep skills compact with lazy-loaded references. |
| OpenClaw `agent-skills` repository | confirmed_source | Treat `autoreview`, `crabbox` and `handoff` as reusable public skill patterns. Do not vendor raw shared skills unless zero-setup portability is explicitly required. |
| Crabbox local docs | confirmed_source | Remote proof needs artifact paths, timing, status, TTL, cost and cleanup. It must not receive secrets by default. |
| Existing security tree source | confirmed_source | Security must be a specialist matrix, not a single generic review. |
| Prior memory/context-spine idea | inference | Keep durable memory/context spine as an architecture hypothesis with poisoning controls; do not attribute it to the open-vs-closed specialist source. |
| Handoff/replay with hashes | factory_decision | Adopt as Overkill handoff contract when work crosses worker, phase, context window, pause or risk boundary. |

## AutoReview

AutoReview enters before landing or promotion when a code diff, branch, patch or
implementation artifact exists.

It is better than post-mortem review because it catches issues before a weak
change becomes durable state. It is not a replacement for independent review,
security review or human R3/R4 gates.

## Handoff

Handoff enters when work moves between agents, pauses, crosses a phase boundary,
or is R2+.

It is better than a summary because it preserves state, constraints, evidence,
non-goals, open decisions and replay notes. A receiving agent should be able to
continue without guessing.

## Crabbox / Remote Proof

Remote proof enters when local validation is insufficient, when CI parity is
needed, when tests are heavy, or when a browser/runtime proof must run in a
clean environment.

It is better than running everything locally because it can provide isolated
evidence. It is worse for small tasks because it adds cost, latency and cleanup
surface. Use it only through a runtime contract.

## Shann Claim Boundary

Do not attribute these to the open-vs-closed specialist source:

- AutoReview;
- Crabbox/Testbox;
- Handoff/replay;
- Receipt Five;
- security gates;
- memory spine;
- remote proof TTL/cost/cleanup;
- skill-cleaning workflows.

The open-vs-closed source supports worker mode selection and promotion rules,
not the entire factory architecture.
