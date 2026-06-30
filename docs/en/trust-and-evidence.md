# Trust and evidence

Overkill Factory is built around one uncomfortable fact: a process that looks alive is not the same as progress.

Agents can write files, move cards, produce confident summaries, and still miss the product. A dashboard can show activity while the real blocker sits untouched. A review can say pass without reading the artifact. A human can be asked for approval without being given the thing they are approving.

The factory treats those as product failures.

## Evidence before confidence

The factory prefers evidence over tone. A worker saying "done" is useful only if the claimed artifacts exist, can be read back, and match the requested work. A test result is useful only if it tests the relevant behavior. A review is useful only if it checks the right artifact and is consumed by the original task.

That is why many factory records look strict. They are not strict because the project loves paperwork. They are strict because loose evidence creates false progress.

## Receipt Five

Receipt Five is the completion receipt. It should answer five kinds of questions:

1. What was requested?
2. What was done or decided?
3. What evidence proves it?
4. Who reviewed it and what did the review say?
5. What remains blocked, risky, or next?

If Receipt Five cannot answer those questions, the honest state is not done. It may be ready for review, blocked, partially complete, or waiting for a human decision. But it is not done.

## Readback

Readback means the factory checks the artifact that a worker claims to have produced. It is not enough for a worker to say "I wrote the SOT" or "I added the test". The factory has to read the file, confirm it exists, and decide whether it is good enough for the next step.

This protects against a very common failure: process compliance without work quality. The worker may have followed the card, but the product output may still be thin, wrong, or missing.

## Independent review

Material work should be reviewed by a different identity when risk requires it. The executor can explain what it did. It should not be the final judge.

Review can pass, fail, or ask for repair. A pass must unblock or close the original task. A fail must create repair work. A review that sits unused is another form of false progress.

## No-idle and blockers

No-idle is not a productivity trick. It is a guard against silent stalls. If the board has work that should move, but nothing material changes, the factory should repair the state, dispatch the next safe worker, or fail visibly.

A blocker should also be honest. Some blockers are real human decisions. Many are not. If the factory needs an internal review, a readback, a missing artifact, or a repair task, that is factory-owned work. It should not be pushed to the operator as if the human has to solve it.

## Human gates

Human gates are serious. They belong to decisions where the operator owns authority: production release, mainnet, funds, secrets, budget, major risk, or explicit approval boundaries.

A good human gate is readable. It says what decision is needed, what evidence exists, what can go wrong, and what each option means. The operator should not have to parse raw JSON or reconstruct the situation from scattered comments.

## Security and risk

Security is not a late checklist. It is a route and architecture concern. Material risk can require threat modeling, trust boundaries, identity and authorization checks, supply-chain checks, secrets handling, privacy review, incident thinking, and residual-risk ownership.

The factory should never claim perfect security. It should claim the best possible security posture supported by evidence, gates, and explicit residual-risk decisions.

The public security matrix is now part of this trust model instead of a separate operator archive. Machine-checkable security domains include: `networking`, `linux-systems`, `web-security`, `application-security`, `ethical-hacking`, `security-tools`, `cloud-security`, `detection-monitoring`, `security-operations`, `cryptography`, `key-management`, `future-security`, `supply-chain`, and `onchain-solana-quasar`.

## The honest boundary

Local checks can prove that the public kernel is coherent. They cannot prove that a private product run shipped. Live product completion needs live Hermes state, product-specific evidence, review, and human approvals when required.

That boundary is not a weakness. It is how the factory stays honest.
