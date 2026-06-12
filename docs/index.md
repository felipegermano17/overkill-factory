# Overkill Factory Docs

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: README.md, scripts/factoryctl.py, schemas/, tests/
> Runtime boundary: This page is navigation. Runtime gates live in scripts,
> schemas, adapter hooks and Hermes state.

## Operator Path

Use this order from a fresh checkout:

1. `factoryctl doctor`
2. `factoryctl run minimal`
3. `factoryctl init --out ../my-product-factory --project-name my-product --paper ./product-paper.md`
4. Read `getting-started/install-in-hermes.md`
5. Connect generated worker packets to your Hermes only after local checks pass.

## Install In Your Hermes

Start with `getting-started/install-in-hermes.md`. Hermes is your runtime floor;
Overkill Factory supplies contracts, profiles, packets and gates.

## CLI Reference

Use `reference/cli.md` for the supported operator commands. Prefer `factoryctl`
over calling many scripts directly.

## Examples

Use `examples/gallery.md` to choose a minimal, Product Face, security or onchain
example. Example files are source material, not historical proof.

## Security

Use `security/oss-security.md` before changing dependencies, workflows, release
state, public docs or adapter behavior.

## Release

Use `operations/release-policy.md` before tagging, packaging or publishing a
release.

## Maintainer Internals

Use `maintenance/repo-surface.md` to decide whether a file belongs in the
operator surface, maintainer internals or generated output.
Use `maintenance/factory-mechanic-loop.md` for the Factory Mechanic Loop: the
factory-wide improvement loop that turns learnback and maturity findings into
radar records, issues or bounded proposals.
