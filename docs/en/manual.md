# Product manual

Overkill Factory is easier to understand if you start with the pain it solves.

A person asks for something: build a product, fix a bug, review a risky change, prepare a release, handle an incident, improve a worker, or turn an idea into a working system. A normal agentic workflow often turns that into one big instruction. The agent tries to be helpful, starts working, and reports progress. Sometimes that works. Often it produces motion without control.

Overkill Factory treats product work as controlled production. The factory does not ask an agent to "figure it out". It asks the system to preserve the source, define the product, choose the method, split the work, execute through Hermes, verify evidence, and close with a receipt.

## What "factory" means here

A factory is not a metaphor for bureaucracy. It means there is a line. Work enters at one end and must pass through states that protect the operator.

A product request should not jump straight to implementation if nobody has resolved the source. A release should not ship because an executor says it is ready. A security-sensitive change should not skip architecture. A human gate should not be hidden inside a chat comment. A worker should not be allowed to approve its own work.

That is controlled production. It is the difference between "an agent worked on it" and "the factory can explain what happened, why it happened, who had authority, and what evidence proves the result".

## The operator experience

The operator should not have to babysit the factory. They should not have to notice that a worker was lazy, that a review result was never consumed, or that a blocker was really a factory-owned task. The factory owns the process. The human owns real decisions.

A good run feels like this:

- The operator gives a goal or source material.
- The factory says what it understood and what is missing.
- The factory creates a product definition that can be reviewed.
- Work is split into pieces small enough for workers to finish and prove.
- Hermes tracks the live state.
- Reviews are independent where the risk requires it.
- Human gates arrive as decision packages, not vague interruptions.
- Completion comes with Receipt Five, not a cheerful status message.

## The product truth layer

The most important artifact is product truth. The factory calls it Product SOT, because it is the source of truth for the product. The name is technical, but the idea is ordinary: before workers build, everyone needs to know what product is being built.

A Product SOT should answer what the user asked for, what is in scope, what is out of scope, what risks matter, what evidence will count, and what would make the work unacceptable. Without that, the factory cannot safely choose a method or assign workers.

This is where many agent systems drift. They turn a large brief into a short summary, then build from the summary. Overkill Factory is designed to avoid that. A summary is not product truth. A helpful guess is not product truth. Product truth must be grounded in source material and reviewed when it matters.

## Methods are chosen, not improvised

Different work needs different methods. A bug fix needs reproduction and regression proof. A new product needs product definition and scope coverage. A release needs readiness, rollback, and approval. A security change needs threat thinking and evidence.

The route registry and method engines make that explicit. The factory currently has 14 route classes and 8 method engines. The point is not to impress the reader with a large list. The point is that the factory should not handle every request the same way.

When the method is right, the worker gets a bounded packet. It knows the task, the limits, the evidence expected, and the authority it does not have. That makes autonomy safer. The worker can move fast inside the lane because the lane is clear.

## Hermes is the floor

Hermes is where runtime state lives. Cards, dependencies, comments, workspaces, workers, blockers, and transitions belong there. Overkill Factory defines the production method and checks. Hermes runs the floor.

That separation matters. If the factory tried to become a second Hermes, it would become another hidden state machine. If Hermes held state but the factory ignored method and evidence, workers would move cards without product discipline. The design is deliberately split: Hermes owns live state; Overkill Factory owns the production contract.

## Done means evidence

The factory is strict about completion because agentic work can look convincing while being wrong. A file can exist and still be useless. A test can pass and still miss the product. A reviewer can approve without checking the right thing. A worker can say done and forget the artifact.

Receipt Five exists to prevent that. It records what was requested, what was done, what evidence proves it, who reviewed it, what remains risky or blocked, and what the next state is. If that evidence is missing, the honest answer is not "done". It is blocked, incomplete, or ready for review.

## What this project is not

Overkill Factory is not trying to hide complexity from the world. It is trying to put complexity in the right place. The operator should see clear state and real decisions. The workers should see exact packets. The code should carry schemas and tests. The public docs should explain enough for a new reader to trust the system without reading every internal file.

That is the bar for the project: simple on the outside, rigorous on the inside, honest at the boundary.

## A concrete example

Imagine the operator says: "Build the customer onboarding flow." A weak agentic system may start designing screens immediately. The factory should not.

First it asks what "customer" means in this product, what onboarding must achieve, which accounts or permissions exist, what the user must see, what must be logged, and what counts as a successful first run. If the product already has a design system, the factory should use it. If the flow touches money, identity, custody, or production data, the risk gates change.

Only after that does implementation become sensible. A frontend worker may receive one packet. A backend worker may receive another. A product-face worker may need screenshots and viewport proof. A QA worker may need a journey test. A reviewer may need to compare the result against the Product SOT. The operator should not have to coordinate all of that by hand.

That is the practical value of the factory. It turns one vague request into a set of small, reviewable, evidence-backed pieces.
