# How it works

This page follows the normal operator experience from first message to final receipt.

## 1. You send the signal

A run starts when the operator sends material to the manager.

The material can be rough:

- “Build this product.”
- “Fix this broken repo.”
- “Turn this idea into a plan.”
- “Review this release.”
- “Migrate this system.”
- “Here is a document; make it real.”

The operator should not need to format the request as factory internals. The factory vocabulary exists to control the work after intake, not to burden the operator before intake.

## 2. The manager creates controlled intake

The manager receives the signal and creates a controlled intake.

The manager should identify:

- the type of work;
- the provided source material;
- whether this is a new run or continuation;
- whether a Hermes board already exists;
- what is explicit;
- what was inferred;
- what is missing;
- what needs human authority.

At this point, the manager should not promise completion. It should turn the request into a safe starting state.

## 3. The source boundary is recorded

The factory separates source truth from model interpretation.

This is important because a sentence in chat can contain facts, guesses, preferences, frustration and open questions all at once. The factory must not flatten that into “approved product truth.”

The source boundary says: this is what the operator actually gave us; this is what we inferred; this is what remains open.

## 4. Product definition / PRD becomes the target

Once source is clear enough, the factory creates or updates product definition.

This is the PRD layer in human language. Internally, older contracts may call it Product SOT. The important point is that the product target becomes explicit before the work graph is treated as official.

The PRD/product definition should make scope, non-scope, users, journeys, acceptance examples, risks and evidence expectations clear enough for specialists to work without replaying the chat.

If approval is required, the manager asks for it with context. If the definition can safely proceed as a candidate, the factory continues while keeping uncertainty labeled.

## 5. The factory checks coverage

The factory checks whether the whole product target is accounted for.

This prevents a common failure: the first obvious implementation slice becomes “the product,” while installation, docs, release, security, edge cases, operator experience or proof are forgotten.

Every important requirement needs a state: planned, done with evidence, blocked, deferred, out of scope, human-owned or replaced by decision.

## 6. The method is selected

The factory chooses the method for the type of work.

For example:

- documentation rewrite: source, audience, information architecture, writing, link/build validation;
- bug: reproduce, prove failure, fix, prove regression protection;
- product feature: PRD, architecture, experience, implementation, proof;
- release: version, rollback, monitoring, owner, approval;
- security-sensitive work: threat/control design before implementation.

The method defines gates, required artifacts and evidence.

## 7. Domain, risk and capability are routed

The factory asks what the work touches.

Does it involve frontend, backend, data, documentation, AI, agent runtime, Solana, payments, secrets, privacy, production or release?

That route determines workers and gates.

If a required capability is missing, the factory should search skills, providers, capability packs and references before asking the operator to solve it.

## 8. Architecture, experience and security shape the plan

Before execution, the factory shapes the product through three lenses:

- architecture: boundaries, dependencies, source of truth, runtime responsibilities;
- product experience: user journey, states, clarity, screenshots/proof, accessibility;
- security/release: access, secrets, risk, review, rollback, monitoring, authority.

This keeps quality from becoming an afterthought.

## 9. Work becomes Hermes state

The factory turns the plan into work units and materializes them in Hermes.

Hermes stores the durable graph: cards, dependencies, statuses, typed blocks, dispatch, worker tasks, logs and comments.

This is the difference between “the agent has a plan” and “the system has work state.”

## 10. Workers execute bounded tasks

Workers receive packets. A packet is an assignment, not proof.

A worker result must come back with evidence. The result must validate and be consumable by the parent work.

If the worker result is missing, malformed, stale or unsupported by evidence, the factory does not pretend the work is done.

## 11. Recoverable problems go to repair

The factory should repair what it can repair:

- regenerate a missing artifact;
- retry a recoverable read or dispatch;
- fix a dependency edge;
- rebuild a derived file;
- route a missing evidence packet;
- continue capability search.

The operator should not become the repair queue.

## 12. The manager asks for human decisions only

The manager asks the operator when there is a real human decision:

- approve or correct product definition;
- provide private source;
- approve cost;
- grant access;
- approve production;
- accept risk;
- decide between product directions;
- approve mainnet, funds, signer or secrets.

A good human gate includes context, options, consequence, recommendation and safe default.

## 13. Evidence is checked

The factory checks evidence by work type.

Code has a different proof path from documentation. Documentation has a different proof path from security. Security has a different proof path from release. Release has a different proof path from onchain work.

The common rule is simple: confidence is not evidence.

## 14. Receipt Five closes the run

When the work is ready to close, the factory produces Receipt Five:

1. what changed;
2. where it lives;
3. how it was verified;
4. who or what reviewed it;
5. what remains.

The final state can be release, block, operate or learnback. An honest block with evidence is better than a fake success.
