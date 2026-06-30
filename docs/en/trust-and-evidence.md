# Trust and Evidence

The factory is built around a blunt rule: a process that looks alive is not the same as progress.

This matters because agentic systems can produce convincing status while doing the wrong work, skipping source truth, hiding blockers, or declaring completion without evidence. Overkill Factory treats that as a product failure, not a communication style issue.

## Evidence before confidence

A worker statement is not enough. The factory expects evidence that can be inspected later: files, commands, test output, readback records, screenshots, receipts, review records, or structured artifacts.

The strongest evidence has three properties:

1. it points to a real artifact;
2. it can be read back after the worker finishes;
3. it traces to the product truth or method contract it claims to satisfy.

## Readback

Readback means the factory checks that claimed artifacts still exist and contain the expected content. This prevents a worker from naming files that were never created, were created in the wrong workspace, or disappeared after the run.

For critical artifacts, readback is not bureaucracy. It is the difference between "the agent said it" and "the system can prove it."

## Independent review

Execution and review are different jobs. A builder can finish a task, but a reviewer must inspect whether the result satisfies the contract. For material work, the same identity should not be both executor and reviewer.

A review result must be reduced back into the original runtime state. If a review passes but the original card stays blocked forever, the factory is still failing.

## No-idle

No-idle is not supposed to be a normal route authority. It is a guardrail. Its job is to notice when the board is stuck, when a worker declared artifacts that cannot be read, when ready work is not being dispatched, or when a repair loop is duplicating itself.

A valid no-idle system must fail loudly when unfinished work remains. Heartbeats are not progress.

## Blockers

The factory separates blockers into two broad kinds:

- non-human blockers that the factory should repair or reroute;
- human authority gates that require a real operator decision.

A missing artifact, stale worker, failed readback, or needed internal review should not be dumped on the operator. Production access, funds, signer authority, release approval, or risk acceptance may require a human.

## Receipt Five

Receipt Five is the closing evidence package. It should include the request, artifact evidence, verification evidence, review evidence, release/block decision, and remaining risks.

A Receipt Five package is not a decorative summary. It is the proof boundary between work in progress and a claim that the factory can defend.

## Security and risk

Security is not a late checklist. It is a route and architecture concern. Material risk can require threat modeling, trust boundaries, identity/authorization checks, supply-chain checks, secrets handling, privacy review, incident thinking, and residual-risk ownership.

The factory should never claim perfect security. It should claim the best possible security posture supported by evidence, gates, and explicit residual-risk decisions.

The public security matrix is now part of this trust model instead of a separate operator archive. Machine-checkable security domains include: `networking`, `linux-systems`, `web-security`, `application-security`, `ethical-hacking`, `security-tools`, `cloud-security`, `detection-monitoring`, `security-operations`, `cryptography`, `key-management`, `future-security`, `supply-chain`, and `onchain-solana-quasar`. These domains route work to specialists such as cloud infrastructure security, OWASP/AppSec, Codex Security, detection and monitoring, crypto/key management, supply-chain gate, agentic AI security, and Solana/Quasar audit workers.

## Self-improvement is bounded

Local validation can prove that the public kernel is coherent. It cannot prove that a private product run is production-ready. Product readiness needs runtime state, product-specific evidence, review, Receipt Five, and human approval when risk requires it.
