# Product definition / PRD

Product definition is the target of the run.

In common product language, this is the PRD area: the product definition document or product requirements definition. Older internal contracts may still use the name Product SOT. Public docs should explain PRD / product definition first because it is easier for a human reader.

## Why the factory needs it

Agents can move fast without knowing what product they are building. That is dangerous.

A worker can implement a visible slice while missing the real outcome. A documentation task can create pages without explaining the product. A bug fix can solve a symptom while ignoring release risk. A redesign can improve the surface while breaking the operator journey.

The PRD/product definition prevents that by defining the target before the work is treated as official.

## What it contains

A usable product definition should answer:

- What are we building?
- Who is it for?
- What problem does it solve?
- What is in scope?
- What is out of scope?
- What user journeys matter?
- What does success look like?
- What examples prove acceptance?
- What risks matter?
- What dependencies exist?
- What access or environment is required?
- What evidence proves completion?
- What decisions require human approval?

It does not need to be beautiful at first. It needs to be explicit and testable enough to guide the factory.

## Source versus product truth

The operator’s message is source. It is not automatically final product truth.

The factory may infer a candidate definition from the message, but it must label what was inferred. If the inference affects product direction, human approval may be required.

This distinction matters because an operator may send rough language, emotional feedback, examples, constraints and open questions in the same message. The factory must not silently turn all of that into locked requirements.

## PRD and Product SOT

Product SOT is an older/internal phrase for the same general control point: the source of truth for product intent.

For public users, PRD / product definition is clearer.

Recommended public language:

```text
The factory creates or updates the product definition / PRD. Internally, some contracts may refer to this as Product SOT, but the human idea is simple: the run needs a clear product target before it decomposes work.
```

## Approval

A product definition can have different states:

- candidate: generated from source and ready for review;
- approved: accepted by the operator or already determined by explicit source;
- partial: enough to continue some safe work but not enough to close the run;
- blocked: missing a decision that changes product direction;
- superseded: replaced by a newer definition.

The factory should not stop every time a definition is not perfect. It should continue on safe parallel work and ask only for decisions that materially change the route.

## How it controls execution

The PRD/product definition feeds:

- scope coverage;
- method selection;
- worker decomposition;
- acceptance examples;
- evidence requirements;
- release gates;
- Receipt Five.

If a worker result cannot point back to the product definition, the result may be useful, but it is not enough to close the product work.
