# How a request moves

The machine has a detailed workflow. You do not need to start there.

The human path is:

```text
request -> preserved source -> understanding -> product truth -> route and method -> small work -> Hermes -> worker result -> readback -> review -> human decision when needed -> delivered, blocked, or learned
```

## 1. Request

Everything starts with a signal: sentence, bug, repo, document, incident, screen, release, or decision.

At that moment the factory does not know enough. Executing immediately is guessing.

## 2. Preserved source

The factory stores the original message, attachments, links, repository, documents, and context before summarizing.

This prevents a bad early summary from deleting the sentence that explains the decision later. The internal name `F0 — Pre-Start / Sealed Source Envelope` exists for the machine and tests. The human reading is simple: seal the source before interpreting it.

## 3. Understanding

The factory separates five things:

- fact: came from source;
- inference: plausible, but not source;
- decision: chosen by valid authority;
- conflict: two sources disagree;
- gap: missing information required to proceed safely.

Without that split, inference becomes scope and gaps become invisible work.

## 4. Product truth

The factory defines what will be delivered, for whom, within which limits, with which risk, and what evidence ends the argument.

The internal name is Product SOT. The useful translation is product truth. It prevents frontend, backend, QA, security, and operator from building different versions of the same request.

## 5. Route and method

Bugs, releases, incidents, interfaces, documentation, security, agents, integrations, and Solana do not ask for the same evidence.

The route answers: what kind of work is this?

The method answers: how will this work be done and proven?

If the method does not change the proof, it is only a label.

### Product truth is not a summary

A summary says, “the user wants onboarding.” Product truth says what onboarding means for this product, which user enters it, where the journey starts, where it ends, what is deliberately out of scope, which risks matter, and what evidence will settle the question.

A weak Product SOT looks like this:

```text
Build onboarding. Make it good. Use the current design.
```

That is not enough for controlled production. It gives the worker permission to invent the product.

A usable Product SOT is explicit:

```text
User: new workspace admin.
Goal: create a workspace and reach the first useful dashboard state.
Must include: account creation, workspace name, invite step, loading state, empty state, confirmation state.
Out of scope: billing setup, KYC, team-role editor, production email migration.
Risks: account permissions, email deliverability, confusing empty state, mobile overflow.
Acceptance evidence: Product Face screenshots, first-run journey test, backend workspace-state check, review result, Receipt Five.
Open gaps: whether invite email uses existing provider or mocked staging provider.
```

The Factory treats those fields differently. “Must include” becomes work. “Out of scope” becomes protection against drift. “Risks” become gates. “Acceptance evidence” becomes the proof contract. “Open gaps” become either factory-owned discovery or a real operator decision.

### Route changes the shape of the work

A bug route should not behave like a greenfield product route. A release route should not behave like a documentation route. A mainnet route should not behave like a local UI route.

```text
Request type                       Better route/method              Required proof
Bug with regression                bug repair / test-first          failing reproduction before, passing regression after
Visible UI journey                 product experience / design-first Product Face packet, screenshots, journey proof
Security-sensitive dependency      security / security-first         risk review, scan, residual risk, independent review
Unknown legacy behavior            diagnosis / baseline-first        baseline, hypothesis, rollback, regression guard
Production promotion               release / gate-first              release memo, rollback, evidence bundle, human approval
Mainnet or funds                   onchain / authority-first         dry run, signer boundary, risk packet, explicit approval
```

A method that does not change artifacts, worker packets, reviewers, gates, or evidence is not a method. It is decoration.

### Running example

If the request is “Build the customer onboarding flow,” the Factory should not immediately create a card called “code onboarding.” It should first decide whether this is product creation, UI repair, backend workflow, documentation, release, or discovery. If the product truth is missing user, success state, out-of-scope, and evidence requirements, execution is premature.

If the request is “Users cannot reset passwords after the latest release,” the Factory should not ask for a design packet first. It should preserve reproduction source, create a regression route, require a failing test or equivalent reproduction, and block done until the specific behavior is proven fixed.

If the request is “Promote version 1.2.0 to production,” the Factory should not let a worker self-approve. It should assemble release evidence, rollback, residual risk, and human authorization.

## 6. Capability and authority

Before sending a worker, the factory checks capability, access, specialist pack, and authority.

If the work touches secrets, production, mainnet, wallets, signatures, funds, or material risk, the bar rises. If capability is missing, block. If human authority is missing, prepare a packet. If readback, attachment, or review is missing, the factory fixes it; it does not dump the problem on the operator.

## 7. Small work

The product becomes executable units.

A good unit has input, output, owner, dependency, evidence, reviewer, and rule of done. A bad unit says “build the product.”

Without that, the agent receives intention, not a task.

## 8. Hermes as live floor

Hermes Kanban remains the runtime source of truth.

Cards, dependencies, workers, comments, attachments, blockers, and transitions appear there. The Factory must not keep hidden parallel state. It enforces the contract; Hermes shows the living work.

## 9. Worker result and readback

The worker returns structured result and evidence. The factory reads back.

If the worker says it created a file, the factory reads it. If it attached evidence, the factory opens it. If it ran a test, the factory checks command and output. If it improved UI, the factory inspects the surface.

## 10. Consumed review

Review only matters when it changes state.

If it passes, it unlocks. If it fails, it creates repair. If it finds risk, it records owner and consequence. If it needs a decision, it becomes a human packet.

## 11. Human decision

Some decisions belong to the operator: production, mainnet, funds, secrets, budget, release, waiver, residual risk, and authority change.

In those cases, the factory prepares context. The human does not approve blind.

## 12. Closure

The request ends honestly:

- delivered, when evidence is sufficient;
- blocked, when something material is missing;
- learned, when execution shows the factory itself must change.

A good factory does not force a happy ending. It tells the operational truth.
