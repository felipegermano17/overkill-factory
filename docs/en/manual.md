# Product Manual

Overkill Factory exists because agentic work often looks productive before it is actually controlled.

A normal agent workflow can answer quickly, write code quickly, and produce a convincing status update quickly. The failure usually appears later: the source was misunderstood, a partial slice quietly replaced the full product, a worker declared done without proof, a risk was treated as a checklist, or the operator had to notice that the system was idle.

The factory turns that fragile workflow into a production line.

## What the factory is

Overkill Factory is a method layer and public kernel for running product work through bounded agents.

It gives the work a shape:

- the source is captured before it is interpreted;
- product truth is separated from assumptions;
- method is selected by contract, not by vibes;
- workers receive bounded packets;
- every important transition needs evidence;
- human gates stay human;
- non-human blockers are repaired by the factory instead of being dumped on the operator;
- completion means evidence-backed delivery, not a confident message.

## What Hermes owns

Hermes is the factory floor. It owns durable runtime state: Kanban boards, cards, dependencies, typed blocks, worker dispatch, comments, logs, schedules, workspaces, and state transitions.

The factory must not recreate that runtime in prompt space. If something is runtime state, Hermes is the authority.

## What Overkill Factory owns

Overkill Factory owns the production method around Hermes:

- the phase graph;
- the route registry;
- method contracts;
- templates and schemas;
- worker authority rules;
- Product SOT / product truth contracts;
- Product Experience and Product Face proof expectations;
- security, access, and release gates;
- evidence and Receipt Five rules;
- public validation commands.

The factory can project status and prepare packets, but it should not pretend that a local projection is the real runtime.

## What agents own

Agents are bounded workers. They do not own the route. They do not decide that the product is done. They execute a packet, return evidence, and accept review.

A worker can be strong without being trusted blindly. The factory is designed around that distinction.

## What humans own

Humans own real authority decisions: funding, production access, signing, release acceptance, material risk, final business judgment, and explicit waivers.

A human gate should be rare and clear. It should not ask the operator to read internal machinery. It should present the decision, the artifact, the evidence, the risk, and the consequences.

## The core promise

The factory's promise is not "agents will never fail." The promise is: when agents fail, the system should know where, why, what evidence is missing, whether the blocker is human or non-human, and what the next safe action is.

That is the difference between autonomous theater and controlled production.

## The public/private boundary

This repository is the public kernel: code, contracts, tests, examples, public worker registries, and public docs. A real product run happens in an operator-owned Hermes runtime. That runtime may contain private boards, private source materials, secrets, evidence, product decisions, and human approvals. Those do not belong in public GitHub.
