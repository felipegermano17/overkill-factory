# Docs

This directory contains human guides for public onboarding, operation and
maintenance of Overkill Factory.

## What Belongs Here

- Public human guides that help an external operator understand, run and extend
  the factory.
- Concept guides, quickstart material, operations checks, architecture notes and
  public governance rules.
- Area manuals that explain a real factory area deeply enough for another agent
  to continue the work.

## What Does Not Belong Here

- Evidence from past runs, screenshots, raw source extraction or chat history.
- Private product context, private board links, local absolute paths or secrets.
- Roadmap doubts inside final/canonical documents.

## Source Of Truth

Executable contracts come first: schemas, scripts, adapter hooks and tests.
Docs explain how to use them. When a doc conflicts with executable behavior,
fix the mismatch and keep the runnable path authoritative.

## How It Is Validated

Run the document and public safety checks:

```bash
python scripts/validate_document_governance.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest tests.test_open_source_docs -q
```

Start with `docs/index.md`, then read
`docs/getting-started/install-in-hermes.md`,
`docs/reference/cli.md`, `docs/concepts/factory-flow.md` and
`docs/operations/validation-and-release.md`.
