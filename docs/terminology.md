# Terminology

Overkill Factory has internal contracts, but public language should stay human.

## Preferred terms

| Use this | Meaning |
| --- | --- |
| Operator | The human asking for work and making human-only decisions. |
| Manager | The human-facing factory voice. |
| Initial signal | The first request/material sent by the operator. |
| Source boundary | The separation between provided facts and inferred assumptions. |
| Product definition / PRD | The product target. Older internal contracts may call this Product SOT. |
| Method | The selected process for this kind of work. |
| Work graph | Durable Hermes cards and dependencies. |
| Worker packet | Assignment to a specialist. Not proof of execution. |
| Worker result | Evidence-bearing output from a specialist. |
| Gate | Rule that decides whether work may advance. |
| Human gate | A real human decision package. |
| No-idle | Recovery/continuity mechanism that wakes the next safe action. |
| Receipt Five | Closure receipt: changed, where, verified, reviewed, remains. |
| Fail closed | Missing proof blocks promotion instead of pretending success. |

## PRD and Product SOT

Use PRD / product definition in public docs.

Product SOT may remain as a technical/internal alias where older contracts require it, but it should not be the first concept a new reader sees.

## Worker packet and worker result

This distinction should always be explicit.

A packet means work was assigned. A result means work produced output. Evidence means the output can be trusted enough to advance.

## Human gate

A human gate is not “permission to continue.”

It is a decision request that only the human can make safely.

## Receipt Five

Receipt Five should be explained as a receipt, not as abstract governance.

It tells the operator what changed, where it lives, how it was verified, what reviewed it and what remains.
