# F3 Understanding Alignment

The factory asked only questions that change architecture, risk, execution, or
authority.

| Question | Answer Used In Pilot | Impact |
| --- | --- | --- |
| Is the first slice allowed to be a controlled test product? | Yes. User explicitly authorized a paper of test and full closure. | Enables dry pilot without waiting for a real KAXIS product paper. |
| Is production, deploy, devnet, mainnet, signing, or funds movement allowed? | No. Authorization is scoped to test pilot. | Keeps all sensitive actions blocked. |
| Must Product Face be included? | Yes. | Forces prototype and visual evidence. |
| Must onchain/Solana be included? | Yes, as Quasar-only package and Auditor preflight. | Forces Auditor path without fake program audit. |
| Can human approval be recorded? | Yes, as test-only evidence referencing the chat authorization. | Lets the dry pilot pass human gate honestly. |

## Decision Packet

Run a dry pilot with a synthetic but intentionally difficult product paper.
Close one first slice through Hermes Kanban with Receipt Five. Do not claim
production readiness.
