# Factory vFinal Provider/Model Audit

Date: 2026-06-11

## Scope

This is a public-safe live configuration audit for the Factory worker layer and
the dedicated Discord GERENTE gateway profile.

It checks whether the current Factory-facing profiles are aligned to the
canonical provider/model without storing private runtime ids, raw logs, Discord
ids, auth files, env values or local paths.

Machine-readable receipt:

- `validation/hermes-live/factory-vfinal-provider-model-audit.json`

## Result

PASS.

## What Was Checked

- 40 public worker profiles are present in Hermes.
- 1 dedicated gateway profile is present: `overkill-factory-gerente`.
- 41 Factory-scope profiles were checked.
- 0 public workers are missing in Hermes.
- 0 Factory-scope profiles differ from `openai-codex/gpt-5.5`.
- 0 Factory-scope profiles are missing auth.
- The private product profile is not the Factory gateway profile.

## Important Boundary

One private non-Factory product profile still exists and still uses its own
product/project model, but it is outside the Factory gateway scope and was
observed stopped. That is acceptable for this audit because the Factory gateway
now runs as `overkill-factory-gerente`.

Two worker profiles do not have their own `.env` file:

- `control-tower-projection-worker`
- `discord-control-tower-bridge`

That is acceptable for this audit because they are worker profiles. The
persistent Discord gateway credentials live in the dedicated gateway profile,
not in these workers.

## What This Does Not Prove

This does not prove product-specific quality, release approval, security waiver
or human approval. It only proves that the Factory-facing profile configuration
is aligned enough for the next pre-pilot checks.
