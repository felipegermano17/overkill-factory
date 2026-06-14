# Product SOT Drafting Bundle

Use this bundle in a web LLM to turn public-safe product input into a Product
SOT candidate.

## Setup

Load these files into the web LLM:

- `SKILL.md`
- `templates/product-sot-candidate.md`
- `checklists/pre-import-checklist.md`

The operator may add public-safe source material, redacted notes or a short
product brief. Do not paste secrets, credentials, private keys, payment data,
raw private logs, customer data or private source dumps.

## Expected Output

The output must be marked `candidate_only` and shaped for
`schemas/product-sot.schema.json`.

The output must separate:

- source facts;
- assumptions;
- open decisions;
- scope in;
- scope out;
- risks;
- access or authority gaps;
- success criteria;
- evidence refs that are public-safe.

## Handoff

Bring the candidate back into the factory repo or runtime and validate it before
execution. The bundle output is not runtime proof, human approval, production
readiness or a final Product SOT by itself.
