# Skills

This directory contains installable Codex skill material for operating Overkill
Factory from a public clone.

## What Belongs Here

- Codex skill instructions that are public-safe and aligned with the current
  factory contracts.
- Skill references and helper scripts that can be installed without private
  workspace context.
- Open-source stewardship rules for maintaining the public repository surface.

## What Does Not Belong Here

- Local-only memories, private paths, private project names or internal board
  references.
- Partial mirrors of generated contracts that can drift from schemas or tests.
- Evidence from past validation runs.

## Source Of Truth

The public skill should match the public repository contracts and the current
factory operating rules. When the local operator skill evolves, this copy must
be reviewed before publishing so GitHub users do not receive stale behavior.

## How It Is Validated

Validate the skill and the public docs together:

```bash
python -m unittest tests.test_open_source_docs -q
python scripts/public_safety_scan.py
```
