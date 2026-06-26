# Overkill Factory Docs

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: README.md, scripts/factoryctl.py, schemas/, tests/
> Runtime boundary: This page is navigation. Runtime gates live in scripts,
> schemas, adapter hooks and Hermes state.

## Operator Path

Use this order from a fresh checkout:

1. `factoryctl doctor`
2. `factoryctl run minimal`
3. `factoryctl init --out ../my-product-factory --project-name my-product`
4. Read `getting-started/install-in-hermes.md`
5. Connect generated worker packets to your Hermes only after local checks pass.

For the first full public run, use
`getting-started/first-external-operator-walkthrough.md`.

## Install In Your Hermes

Start with `getting-started/install-in-hermes.md`. Hermes is your runtime floor;
Overkill Factory supplies contracts, profiles, packets and gates.

## CLI Reference

Use `reference/cli.md` for the supported operator commands. Prefer `factoryctl`
over calling many scripts directly.

## Factory Operating Systems

Use `architecture/factory-operating-systems.md` to understand the canonical OS
registry: Product Truth, Method, Authority, Hermes Runtime, Evidence, Domain
Packs, Operator Experience, Security/Release, Product Quality, Velocity/Cost and
Learning. The registry maps owners and proof obligations; it does not claim
product-specific production readiness by itself.

Use `architecture/deterministic-control-plane.md` before changing dispatch,
no-idle, bridge start, phase binding, human gates or domain-brain routing.

## Examples

Use `examples/gallery.md` to choose a minimal, Product Face, security or onchain
example. Example files are source material, not historical proof.

## Security

Use `security/oss-security.md` before changing dependencies, workflows, release
state, public docs or adapter behavior.

## Release

Use `operations/release-policy.md` before tagging, packaging or publishing a
release.

Use `operations/parallel-execution-and-status.md` before scaling agents,
splitting work across branches/worktrees or presenting a operator console/status view.

Use `operations/fast-autonomy-lane.md` before allowing a card to move quickly
without another human prompt. It separates reversible fast work from forbidden
global YOLO authority.

Use `operations/promise-to-implementation.md` before changing README, release
notes, public docs or visual surfaces. It maps public promises to implementation,
proof and explicit boundaries.

Use `operator/overkill-factory-bridge.md` when Codex or another assistant is
bridging a human operator to the factory without acting as a factory worker.

Use `operator/overkill-factory-bridge-plugin.md` when installing the Codex
Bridge plugin, reviewing hook trust or checking how inbox catch-up works after
Codex was closed.

## Maintainer Internals

Use `maintenance/repo-surface.md` to decide whether a file belongs in the
operator surface, maintainer internals or generated output.

Use `maintenance/self-improvement-loop.md` for learnback issue candidates,
missing-capability completion plans, owner issue intake, reasoning policy,
factory readiness scorecards, SDLC feedback loops, reference quality packets
and governance audit artifacts.

Use `maintenance/factory-learning-skill-evolution-os.md` when repeated
execution findings should become validated skills, rules, gates, tests, workers,
schemas, hooks, MCP/tool proposals, install profiles, issues or rejections.

Use `maintenance/hermes-learn-integration.md` when Hermes `/learn` is available
and a repeated workflow should become a staged skill candidate without
bypassing Factory Mechanic, proposal validation or human gates.
