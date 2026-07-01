# Start here

Overkill Factory is a production system for agentic work.

It turns vague requests into small, traceable, proven work. The idea is simple: an agent may execute, but it may not invent scope, hide risk, approve its own work, or call something done without evidence.

That is controlled production.

## Who this is for

This is for people using agents for product, code, releases, review, operations, incidents, or documentation who are tired of becoming the process inspector.

Without a factory, you must check whether the agent understood the request, whether the source was summarized incorrectly, whether the test proves the right behavior, whether risk was accepted by someone, whether review was consumed, and whether a blocker belongs to you or to the factory itself.

If you do that manually for every card, the agent may help, but the operation still depends too much on you.

## The simplest example

You write:

> Launch the new onboarding tomorrow.

A loose agent may answer “working on it” and start with the UI. That looks productive, but it may already be wrong.

Which customer? End user, internal operator, investor, admin, wallet holder? Onboarding until where? Account creation, wallet connection, KYC, signature, first deposit, group entry, dashboard? Does it touch payment, sensitive data, production, mainnet, funds, or secrets? Is there a Figma? Is there a backend? What counts as success?

The factory slows down the dangerous part. It preserves the source, separates fact from inference, identifies conflict, defines product truth, chooses route, breaks work down, and only then sends workers through Hermes.

## What you receive

You receive a request reading, a product definition, a small plan, status in Hermes, blockers with owners, well-formed human decision requests when necessary, and a final receipt.

The final receipt is not “the agent says it is done.” It is a verifiable story: the request was this, the source was this, the work was this, the evidence is this, review said this, and the remaining risk or gap is that.

## What it does not promise

It does not promise that agents never fail. It does not replace human decisions. It does not turn local tests into proof of live delivery. It must not pretend that a vague request became a complete product while source, authority, capability, or evidence is still missing.

The promise is different: make error, gap, risk, and blocker visible early enough that you do not discover them too late.

## Continue

Read [The product problem](02-factory-flow-and-hermes-architecture.md) to understand why a good agent is not enough. Read [How a request moves](02-factory-flow-and-hermes-architecture.md) to see the full flow.
