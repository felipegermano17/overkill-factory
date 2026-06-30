# Telegram Operator Experience

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `factory/schemas/operator-interface-profile.schema.json`, `factory/schemas/operator-briefing-package.schema.json`, `factory/scripts/factoryctl.py`, Hermes Kanban state and tests.
> Runtime boundary: Telegram is an operator interface. Hermes Kanban, receipts and factory contracts remain the source of truth.

Telegram can be the only place where the human operator talks to the factory.
That does not make Telegram the factory. It is the front desk.

## Simple Picture

The operator should not need to chase the factory.

The factory should:

1. receive the operator's material;
2. confirm what it understood;
3. work through Hermes;
4. push status when something meaningful changes;
5. send a real decision package when human input is required;
6. keep working without polling when no human decision is needed.

## What Telegram May Do

- Receive source material from the operator.
- Ask clarifying questions during conversational start.
- Send short status updates.
- Send markdown and PDF decision packages.
- Register the operator's bounded decision after the package is delivered.
- Let `overkill-factory-gerente` report when work is blocked by a real
  `needs_input` decision.

## What Telegram Must Not Do

- Become the runtime source of truth.
- Ask for approval before the operator has received the decision material.
- Turn dependency waits, repair loops or missing worker bookkeeping into human gates.
- Mark cards done.
- Approve implementation, release, funds, signing, custody, secrets or production action by implication.
- Replace Hermes Kanban dispatch, transitions, comments, runs or receipts.
- Send direct worker, Kanban event, cron or artifact-dump notifications to the
  operator. Those events may feed the manager, but only the manager talks to the
  human.

## Decision Package Rule

A human gate needs a package before it needs an answer.

For material decisions, the operator-facing message must point to:

- the short explanation;
- the markdown package;
- the PDF package when the channel supports attachments;
- evidence index;
- exact decision options;
- what approval allows;
- what approval does not allow.

A bare chat question is not enough for a material human gate.

## Language Rule

Operator-facing communication uses the operator's primary language.

This includes Telegram messages, status updates, decision questions, decision
packages, owner-readable Markdown/PDF attachments and Hermes Kanban card titles
or summaries. If the operator is speaking Portuguese, the manager speaks
Portuguese and the Kanban cards visible to the operator are Portuguese.

Internal factory surfaces may stay in English when they are machine contracts:
schema keys, record types, phase ids, step keys, worker ids, profile ids,
technical artifact ids, internal reasoning and machine logs.

## Proactive Status Rule

The factory should have the manager report when:

- a worker batch completes;
- a real human decision is needed;
- a gate blocks material progress;
- a no-idle watchdog repairs non-human idle state;
- a repeated same-cause block escalates to triage;
- release or production readiness changes.

The factory should not spam the operator for internal retries, dependency waits,
normal worker progress, worker completion events or raw artifact dumps.

Even when a human decision is required, the operator should receive a manager
message with the decision package. A direct Kanban subscription, worker message
or automatic notification is noise.

## Typed Block Mapping

Telegram notification follows Hermes typed block meaning:

| Block reason | Telegram behavior |
| --- | --- |
| `dependency` | No operator page. Wait and auto-resume when parent work completes. |
| `needs_input` | The manager reports only after the complete decision package exists. |
| `capability` | Factory searches providers, skills, packs and references before blocking. |
| `transient` | Retry or route repair. Do not ask the operator to approve a transient hold. |

## Validation

Use:

```bash
python -m unittest tests.test_operator_experience -q
python factory/scripts/factoryctl.py validate-v2-runtime-contracts
```
