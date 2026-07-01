# Operator experience

Overkill Factory is a product for operators, not only a set of scripts.

The question here is: what does the person see, send, receive, approve, and stop manually policing?

## What the operator sends

The operator may send a request, bug, release, incident, document, repo, screenshot, decision, or status question.

They should not have to transform everything into a perfect ticket. The factory must receive raw material and explain what is still missing before safe work begins.

## A good first response

Request:

```text
Launch the new onboarding tomorrow.
```

Bad response:

```text
Working on it.
```

Good response:

```text
I understand the goal. Before execution I need to confirm who enters the flow, what counts as success, and whether this touches payment, wallet, or sensitive data. I preserved the source and will prepare the product packet.
```

The good response creates control without dumping bureaucracy on the operator.

## Useful status

Bad status:

```text
In progress.
```

Good status:

```text
Source preserved. Product defined. Three work units created. Two are running in Hermes. One is blocked by conflict between “with KYC” and “no KYC.” Smallest safe next step: decide whether KYC is in v1.
```

The operator understands state without opening ten files.

## Good blockers

A good blocker says what is missing, why it is missing, who owns it, and the smallest safe next step.

A bad blocker says only “waiting on human.” That transfers factory laziness to the operator.

Not every blocker is human. Missing readback, attachment, worker result, consumed review, or valid evidence is factory work.

## When the operator acts

The operator acts when there is real authority: production, mainnet, funds, secrets, budget, release, waiver, residual risk, or power change.

They should not act to compensate for internal disorder.

## A good human question

A good human question shows:

- what is being approved;
- what is not being approved;
- which evidence exists;
- which risk remains;
- which options exist;
- what happens on approval;
- what happens on refusal.

That respects the human and preserves the decision trail.

## Reading a receipt

At the end, the operator should receive a receipt, not a confident declaration.

The receipt states request, delivery, evidence, review, and remaining items. If something is out of scope, it must be visible. If risk was accepted, it needs an owner. If delivery is partial, it cannot be sold as complete.

## Bridge and inbox

The operator bridge may carry context, ask for attention, record decisions, and build handoff. It must not create Hermes boards, close gates, execute factory work, or approve by itself.

Modes like `status_bridge`, `start_bridge`, `question_bridge`, `decision_bridge`, `change_bridge`, `exception_bridge`, `handoff_bridge`, and `learnback_forwarding` separate conversation from authority. `factory_bridge_start_request` and the Durable Operator Inbox transport context, but they still cannot bypass the Factory.

The `overkill-factory-gerente` profile talks with the operator. The `factory-orchestrator` worker owns orchestration. The `default Hermes store` must not be used as an implicit target when real execution requires an explicit board/run. Factory Mechanic remains the self-improvement owner. The bridge cannot execute factory work.
