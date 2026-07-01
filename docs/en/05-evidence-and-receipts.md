# Evidence and receipts

The right question is: how do I know the agent is not just talking well?

The answer begins with an uncomfortable truth: a process that looks alive is not the same as progress.

## Progress theater

Progress theater is activity replacing delivery.

The worker says “done” without evidence. The test passes but covers the easy path. The screen exists but breaks on error. Review approves without reading the artifact. The human approves without material. The board moves while the real dependency is missing from the graph.

The factory treats that as a central failure.

## Weak proof and strong proof

Weak proof:

```text
Tests passed.
```

Strong proof:

```text
The test test_onboarding_email_error failed before the fix, passed after it, and covers exactly the error described in the request.
```

Weak proof:

```text
Screenshot attached.
```

Strong proof:

```text
Screenshots show desktop, mobile, loading, error, empty state, and happy path. Console is clean.
```

Weak proof:

```text
Review approved.
```

Strong proof:

```text
An independent reviewer read the diff, raised two repairs, both were fixed, and the final review unlocked the gate.
```

## Readback

Readback means reading again before believing.

If the worker says it created a document, the factory reads it. If it attached proof, the factory opens it. If it ran tests, the factory checks command and output. If it improved UI, the factory inspects the surface.

Without readback, the factory only trusts the worker.

## Consumed review

Review is not a stamp. Good review changes state.

If it passes, it unlocks. If it fails, it creates repair. If it finds risk, it records an owner. If it requires a decision, it becomes a human packet. If it floats in a comment, it was not consumed.

## Receipt Five

At the end, you receive a completion receipt. Internally it may appear as Receipt Five.

It answers:

1. What was requested?
2. What was done or decided?
3. Which evidence supports that?
4. Who reviewed it and what did review say?
5. What remains missing, blocked, or risky?

If an important answer is empty, it is not done.

## Evidence by work type

A bug needs reproduction before and after.

A release needs readiness, rollback, owner, window, and monitoring.

An interface needs journey, error, empty state, loading, mobile, basic accessibility, and console.

Security needs boundary, threat, permission, secret, supply chain, and residual risk.

Docs need clarity, navigation, first success, and absence of false claims.

## Security specialist matrix

Security-sensitive work can route to specialist domains when the surface requires it: networking, linux-systems, web-security, ethical-hacking, security-tools, cloud-security, detection-monitoring, cryptography, security-operations, future-security, supply-chain, and onchain-solana-quasar.

The point is not to turn every task into a security audit. The point is to make the security domain explicit when the work touches the surface.

## Local proof is not live delivery

A local command passing proves checkout coherence.

A live Hermes runtime proves work existed in that runtime.

A worker result proves a worker returned something in that scope.

A well-formed Receipt Five proves conclusion was reconciled.

Those are not the same. A local smoke does not prove product delivery. A file does not prove readback. Generic approval does not prove mainnet.
