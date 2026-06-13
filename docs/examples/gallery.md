# Example Gallery

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: examples/, scripts/factoryctl.py, tests/
> Runtime boundary: Examples are public-safe source material. They are not proof
> that production work has run.

## Minimal Hermes Project

- Path: `examples/minimal-hermes-project/`
- Use when: first install, first smoke, first worker packet generation.
- Command: `factoryctl run minimal`

## Product Face Example

- Path: `examples/cards/v35_valid_product_face.md`
- Use when: visible product work needs Product Experience OS and Product Face
  proof before completion.
- Command: `factoryctl gate-report --card examples/cards/v35_valid_product_face.md`

## Local Web Cockpit Factory Slice

- Path: `examples/local-web-cockpit-factory-slice/`
- Use when: starting the local-first web cockpit through factory gates without
  hand-building the UI outside the factory.
- Command: `factoryctl worker-packet --worker all --required-only --card examples/local-web-cockpit-factory-slice/card.md --out .tmp/local-web-cockpit-worker-packets`

## Security Example

- Path: `examples/cards/v35_valid_security_with_scan.md`
- Use when: a card needs a security scan packet and independent review without
  onchain risk.
- Command: `factoryctl worker-packet --worker all --required-only --card examples/cards/v35_valid_security_with_scan.md --out .tmp/security-example-packets`

## Onchain Auditor Example

- Path: `examples/cards/v35_valid_onchain_auditor_scan.md`
- Use when: Solana/Quasar work needs Auditor, Codex Security, supply-chain and
  human-gate coverage.
- Command: `factoryctl gate-report --card examples/cards/v35_valid_onchain_auditor_scan.md`

## Rule

Examples stay small, public-safe and reproducible. Generated worker packets,
gate reports, screenshots and receipts belong in `.tmp/`, not in `examples/`.
