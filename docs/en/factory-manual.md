# Overkill Factory Manual

Overkill Factory is a product factory operated by AI agents.

It exists because asking an agent to "make a product" is risky when there is no production process around the agent. A capable agent can still misunderstand the request, start coding too early, invent requirements, forget risk, say it finished without proof, hide a human decision inside a status update, or produce polished documents that do not help anyone build or verify the product.

The Factory tries to make AI work controllable. It does not make AI perfect. It makes work visible, bounded, reviewable and auditable.

The core idea is:

Raw intent -> source understanding -> product truth -> method -> plan -> work units -> Hermes cards -> worker execution -> evidence -> review -> Receipt Five -> release, block or learnback.

## The Factory Does Not Start By Building

The first professional behavior is restraint.

A normal agent hears "I want an app" and starts creating files. The Factory should not do that. It first asks or derives the few things that change the product, the risk or the authority boundary:

- who the product is for,
- what problem it solves,
- what outcome would prove success,
- whether login, sensitive data, money, blockchain, payments, production, external accounts or legal risk are involved,
- whether the repository, design, environment and access already exist,
- who can approve risk, cost, production, secrets, funds or mainnet.

The Factory should not ask a long bureaucratic questionnaire. It should ask when the answer changes something important. If the next step is safe and obvious, it continues. If the next step requires real authority, it stops and asks clearly.

Building too early is one of the main sources of product failure. If the initial understanding is wrong, every artifact after it becomes wrong with confidence.

## The Factory Works Through Artifacts

An artifact is anything concrete that records or proves something:

- a Product SOT,
- a JSON contract,
- a Kanban card,
- a worker packet,
- a test output,
- a screenshot,
- a pull request,
- a review result,
- a human gate package,
- a release proof,
- a Receipt Five.

The Factory does not trust vague language such as "I understood", "looks good", "done", "almost finished" or "trust me". If the next step depends on information, that information must be recorded somewhere another person or agent can inspect.

This is the first discipline: important state cannot live only in the agent's head.

## Source, Facts, Assumptions And Decisions Are Different Things

A conversation contains many different types of information: facts, preferences, examples, guesses, corrections, doubts, risks and decisions. If all of that stays mixed together, the Factory becomes chaos with a nicer interface.

The Factory separates:

- source: the raw material that arrived from the operator, a document, a repository, a link, an issue or a message,
- facts: things confirmed by source or by the operator,
- assumptions: things that might be true but are not confirmed,
- inferences: conclusions drawn by the Factory,
- conflicts: source items that disagree,
- questions: missing answers that change product, risk or execution,
- decisions: choices the product owner actually made.

Example: "I want a Nubank-like app for crypto investing" proves an experience direction. It does not prove custody, trading authority, regulatory scope, money movement, or who can sign transactions. Treating those assumptions as facts would be dangerous.

## Product SOT Is The Official Product Truth

SOT means Source of Truth. Product SOT is the document that answers: what product are we building?

It should name the product, the audience, the problem, the intended outcome, what is in scope, what is out of scope, constraints, risks, dependencies, decisions already made, open questions, success criteria, authority limits and human approvals required.

Without Product SOT, each worker can build a different product:

- frontend imagines one experience,
- backend imagines another data model,
- security reviews a different threat surface,
- docs explain a different promise,
- release prepares for an environment that was never approved.

The Product SOT is not decoration. It is the shared product truth that prevents the production line from splitting into parallel guesses.

## Outcome, Scope And Method Come Before Execution

The Factory does not only ask what to build. It asks what transformation matters.

"Create a dashboard" is too weak. A better outcome is: "An operator can open one screen, see pending requests, filter by status and export CSV without opening the database."

That kind of outcome tells the Factory:

- who uses the product,
- what the person can do,
- how success is proven,
- what evidence should exist,
- what failure looks like.

After that, the Factory checks the full scope. It looks for missing pieces: login, admin, empty states, error states, loading states, mobile behavior, documentation, deploy, rollback, security, observability, access control, secrets, tests, migration and onboarding.

Then it chooses a Method Contract. The method is the rule for how this type of work should be built and proven.

A typo fix does not need the same process as a mainnet token launch. A local prototype does not need the same authority as production. A public documentation rewrite does not need the same proof as a system that handles money.

The Method Contract defines phases, workers, gates, evidence, forbidden actions, human authority boundaries, risk tier and proof level.

## Product Experience Is Part Of The Product

The Factory does not treat product as "backend plus code". A product has a face:

- web UI,
- mobile UI,
- CLI or TUI,
- documentation,
- chat interface,
- wallet/onchain experience,
- admin panel,
- onboarding,
- error and empty states.

Product Face Packet is the plan for the product surface. Product Face Result is the proof that the surface exists and was checked.

"Frontend done" is not enough. For visual work, the Factory should expect screenshots, desktop and mobile checks, primary journey verification, button behavior, error states, console health, accessibility basics, overflow checks and evidence that the design system was respected.

The same rule applies to CLI products. A CLI needs installation proof, help output, real command output, useful errors and terminal behavior.

## Architecture Must Help Execution

Architecture answers: which pieces exist and how do they talk?

It should identify frontend, backend, database, queues, login, storage, external APIs, payment gateways, smart contracts, admin surfaces, deploy targets, observability and rollback paths when relevant.

Good architecture tells workers what to build, where data lives, who calls whom, who can access what, where secrets exist, which boundaries matter, how to test, how to monitor and how to recover.

Decorative architecture is useless. Architecture that does not help execution, security or verification is noise.

## Security, Access And Budget Are Early Questions

Security is not a scanner at the end. It starts before execution.

The Factory should detect whether the work involves sensitive data, login, permissions, abuse risk, prompt injection, agent tool risk, supply chain risk, keys, tokens, wallets, signing, money, production, cloud cost, paid APIs, GPU, mainnet or external accounts.

If capability is missing, the Factory should not immediately throw the problem back to the operator. It should first try safe capability acquisition: look for the right skill, provider, reference, CLI, docs, example, smoke test or capability pack.

But secrets, money, production, billing, accounts, funds, signing and mainnet require explicit human authority.

## Work Units And Worker Packets Make Execution Bounded

A Product Creation Plan connects the product truth to executable work. It decides order, dependencies, parallel lanes, workers, required proof, gates and definition of done.

The plan becomes work units. A weak work unit says: "do backend." A strong work unit says: "create POST /orders with validation X, persistence Y, test Z, no deploy, with pytest output and one curl example."

Each work unit should define:

- objective,
- scope,
- out of scope,
- required input,
- expected output,
- responsible worker,
- reviewer,
- risk,
- authority,
- forbidden actions,
- dependencies,
- definition of done,
- required evidence.

Then the work unit becomes a Hermes Kanban card and a worker packet. The worker packet tells the worker what it is, what it can do, what sources to use, what not to do, which tests to run and how to return evidence.

The Factory does not rely on the worker's "common sense". It gives the worker rails.

## Hermes Is The Factory Floor

The repository defines the Factory kernel. Hermes is where live work happens.

Hermes provides sessions, tools, Kanban, profiles, workers, gateways, Telegram or Discord channels, cron, logs, memory, execution and evidence.

Hermes Kanban remains the runtime source of truth. A chat message can explain status, but the work must be visible in live runtime state. If Telegram says "done" but there is no card, no evidence and no Receipt Five, the product is not done. If the Kanban has a blocked gate and the operator never received the decision package, the Factory failed the operator interface.

## The Gerente Bridge Does Not Do Factory Work

The `overkill-factory-gerente` is the front desk between a human conversation and the Factory floor. It helps the operator ask, start, decide, change or understand work, but it must not execute factory work.

The bridge modes are:

- `status_bridge`: explain current state from evidence and runtime references,
- `start_bridge`: shape a new request into `factory_bridge_start_request`,
- `question_bridge`: answer operator questions without mutating the Factory,
- `decision_bridge`: capture explicit human decisions,
- `change_bridge`: route change requests into the proper factory path,
- `exception_bridge`: surface unsafe, ambiguous or blocked situations,
- `handoff_bridge`: preserve context when a handoff is required,
- `learnback_forwarding`: forward real failure lessons to the learning loop.

The bridge can prepare or route messages, but the `factory-orchestrator` owns factory execution. The bridge uses the Durable Operator Inbox so human decisions and pending messages are not lost between chat, Hermes and the default Hermes store.

The bridge cannot approve, execute or mutate factory work on behalf of the operator.

Factory Mechanic remains the self-improvement owner. The bridge can report a friction point, but it does not silently rewrite the Factory.

## The Work States Matter

The basic states are:

- Todo: the task exists but is not ready,
- Ready: a worker can take it,
- Running: someone is executing it,
- Blocked: work cannot safely continue,
- Review: independent verification is needed,
- Done: output, evidence, criteria, review and risk handling are complete enough for the next step.

Done must never mean "the worker said done." Done means the output exists, evidence exists, criteria were met, review passed when required, risks were handled and the next step can consume the result.

## Blocked Is Not Failure

A real block is healthy when it protects the product.

Good blocks:

- production cannot proceed without approval,
- mainnet cannot proceed without funds/signing authority,
- Product SOT cannot proceed because source decisions conflict,
- a worker declared an artifact that does not exist,
- evidence does not support the conclusion.

Bad blocks:

- "depends on user" without a clear question,
- review needed but no review task created,
- missing artifact but no repair task created,
- card stuck because nobody looked,
- done without proof.

The Factory should distinguish honest blocking from passive waiting.

## No-Idle Prevents Silent Stalling

No-idle means the Factory should not sit still when it can safely advance.

It should notice:

- ready work with no worker,
- running cards whose process died,
- blocked cards the Factory can repair,
- review PASS that nobody consumed,
- declared artifacts that do not exist,
- hidden human gates,
- inverted dependencies,
- required work outside the graph.

If the problem is internal, the Factory should repair or dispatch. If the decision is truly human, it should deliver a clear question. It should not wait for the operator to ask "what happened?"

## Human Gates Are Authority, Not Politeness

A human gate is needed when the Factory needs the owner's authority:

- spending money,
- using production,
- changing scope,
- accepting residual risk,
- using secrets,
- touching funds,
- signing,
- mainnet,
- high-impact architecture,
- sensitive publication,
- destructive action.

A bad human gate says: "do you approve?" with no context.

A good human gate delivers a decision package:

- exact decision,
- options,
- consequence of each option,
- recommendation,
- risks,
- what approval authorizes,
- what approval does not authorize,
- evidence attached,
- expected answer format.

The human should not be bothered with factory chores such as "I forgot to read the file" or "review task was not created." Those are Factory responsibilities.

## Review, Readback And Evidence Are The Trust Engine

The Factory should not let the executor approve itself.

The reviewer checks whether the card was fulfilled, evidence exists, tests passed, scope was respected, forbidden actions were avoided, documentation and security are sufficient, output is useful and risk is declared.

Readback is the act of checking reality. If a worker says a file exists, the Factory reads it. If a worker says tests ran, the Factory checks output. If a worker says UI is correct, the Factory checks screenshots, viewports, console health and the actual journey.

Evidence is not enough by itself. The evidence-reconciler asks: does this evidence support this conclusion?

A log exists, but what does it prove? A screenshot exists, but does it show the required flow? A test passed, but does it cover the relevant risk? A PR opened, but did CI pass?

## Receipt Five Closes The Loop

Receipt Five is the delivery receipt. It answers:

1. What was requested?
2. What was produced?
3. What evidence supports it?
4. Who reviewed it?
5. What is the final state: accepted, blocked, needs repair, or risk remains?

Receipt Five prevents empty "done". It lets someone later inspect the delivery and understand what happened without trusting the original agent's confidence.

## Release Is Serious

Release means something leaves the safe environment: merge to main, deploy, docs publication, tag, GitHub Release, production bot, contract, public version or mainnet path.

The Factory should know what is being released, for whom, in which environment, how to prove it is alive, how to roll back, who owns it, which risks remain, whether CI passed, whether docs are coherent and whether the final URL or object was checked.

A professional public GitHub release does not stop at "PR opened." If the scope is complete and approved, the loop includes merge, issue closure, branch cleanup, synced main, tag or release when applicable and final verification.

## Learnback Makes The Factory Better

Every real failure should improve the Factory:

- a hidden gate becomes a rule,
- a shallow worker result becomes a quality firewall,
- a silent card becomes no-idle logic,
- confusing documentation becomes a rewrite,
- escaped risk becomes a check,
- missing capability becomes a capability pack,
- manual repetition becomes automation.

Learnback should not be a pretty note. When serious, it becomes a test, validator, skill update, contract improvement, script, issue, pull request or flow change.

## Bad Delivery Versus Good Delivery

Bad delivery looks like:

- work without proof,
- vague cards,
- workers without authority limits,
- reviewer equals executor,
- hidden human gates,
- shallow Product SOT,
- decorative architecture,
- security at the end,
- docs that do not help,
- release without rollback,
- production without approval,
- progress that exists only in text,
- Kanban movement without material artifact,
- done without readback,
- public GitHub full of internal leftovers.

Good delivery looks like:

- product defined,
- scope clear,
- risk explicit,
- small work units,
- right worker,
- limited authority,
- real execution,
- real tests or proper proof,
- readable evidence,
- independent review,
- human gate only when necessary,
- clear human decision,
- release with rollback when needed,
- useful documentation,
- final receipt,
- traceable state,
- learnback incorporated.

## What The Operator Should Demand

You do not need to understand every schema. You should be able to ask:

- what does the Factory know for sure?
- what is it assuming?
- what still needs a decision?
- what is the next safe step?
- what is blocked?
- does this need me, or is it Factory work?
- where is the evidence?
- who reviewed it?
- does this authorize production, or is it partial proof?
- what is the Receipt Five?
- what risk remains?

If the answers are clear, the Factory is healthy. If the answers are vague, there is probably theater.

## The Honest Boundary

The Factory is not magic. It does not eliminate mistakes. It makes mistakes visible earlier, with a trail, an owner and a next step.

The repository proving local checks does not prove a live product was delivered. The visual map does not prove runtime readiness. A gateway being connected does not prove a specific Factory Run is correct. A worker registry does not prove every worker executed well.

Real product proof requires live Hermes state, a real card, worker result, specific evidence, readback, independent review, Receipt Five and human gate approval when required.

The golden rule remains: nothing is done because an agent said it is done. It is done when the Factory can show the request, the produced work, the proof, the reviewer, the remaining risk and the authorized final state.
