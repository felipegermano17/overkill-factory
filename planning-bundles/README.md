# Planning Bundles

Planning bundles are public-safe protocol packs for early factory work in a web
LLM environment. They are useful when conversation, summarization and research
are cheaper outside the local runtime.

They do not replace the factory runtime, schemas, gates, receipts or evidence.
Every bundle output is a candidate artifact until it is brought back into the
repo or runtime and validated by the canonical factory process.

## When To Use

Use a planning bundle for:

- source intake and clarification;
- Product SOT drafting;
- Specialist Research Plan drafting;
- Product Face Packet planning;
- Product Creation Plan drafting;
- checklist review before local implementation begins.

Do not use a planning bundle for:

- worker execution;
- runtime proof;
- approval recording;
- secret handling;
- release or production readiness claims.

## Public-Safe Rule

Do not paste secrets, credentials, private keys, payment data, raw private logs,
customer data or private source dumps into a web LLM. Use public-safe excerpts,
redacted summaries or operator-approved synthetic examples.

## Import Path

1. Run the bundle in the chosen web LLM.
2. Export the result as a candidate artifact.
3. Bring the candidate back into the repo or runtime.
4. Validate it against schemas, `factoryctl` gates and public safety scans.
5. Continue only when the factory accepts the candidate as part of the gated
   process.

The bundle helps create a better draft. The factory decides whether the draft is
usable.
