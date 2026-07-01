# Maintainer guide

Public documentation is part of the product. If it decays, the factory falls back to chat memory.

## When a change needs docs

Update docs when behavior, command, schema, route class, method engine, worker, gate, boundary, claim, README, visual map, or validation changes.

## Updating README

README is entry, not inventory. Keep it short, clear, and free of opening jargon. Technical details belong in reference, validation, or status.

## Updating MkDocs

Navigation should answer real reader questions, not internal names. Do not reintroduce `manual.md`, `lifecycle.md`, or the old structure as canonical navigation.

## Updating the manifest

`docs/public-surface.manifest.json` protects links, required phrases, source refs, and proof boundaries. Register every public page.

## Updating tests

`tests/test_open_source_docs.py` should protect structure, depth, absence of false claims, and MkDocs build. Do not use tests to freeze bad copy.

## Updating counts

Count phases, routes, methods, operating-system areas, workers, schemas, templates, and tests with tools. Do not update numbers by memory.

## Preserving legacy

Old docs live in `factory/legacy-docs/`. Use them as historical evidence, not canonical copy. If content returns, translate it into the new structure.

## Never publish

Do not publish secrets, private paths, private runtime evidence, generated worker packets, sensitive gate reports, private screenshots, temporary output, or unsanitized human decisions.

## PR checklist

- README remains human.
- Core pages begin with reader pain.
- Internal terms appear after human explanation.
- Good and bad examples exist where they matter.
- Local proof vs live delivery is clear.
- Manifest is updated.
- MkDocs strict passes.
- Public validators pass.
- Relevant tests pass.

## Merge checklist

- CI green.
- Old pages did not return to canonical navigation.
- No runtime claim without live proof.
- No generated file tracked accidentally.
- EN and PT share structure and facts while keeping native voice.
