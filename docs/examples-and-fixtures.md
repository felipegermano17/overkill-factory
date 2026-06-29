# Examples and fixtures

Examples and fixtures are allowed only when they have a clear purpose.

They are not a place to store old runs, generated proof archives, private product material or historical clutter.

## Examples

Examples should help a new operator or contributor understand and validate the public path.

A good example is:

- small;
- public-safe;
- readable;
- runnable or checkable;
- connected to a documented command;
- not copied from a private customer/project run.

Current example family:

| Path | Purpose |
| --- | --- |
| `factory/examples/minimal-hermes-project/` | Minimal public source example for quickstart-style validation. It contains a small source paper, card, expected flow and expected Receipt Five. |
| `factory/examples/cards/` | Public-safe positive and negative card examples used to validate gate behavior. |
| `factory/examples/receipts/` | Public-safe receipt metadata examples used by contract tests. |

## Fixtures

Fixtures are test inputs.

A good fixture is:

- minimal enough to understand;
- public-safe;
- required by an automated test or validator;
- focused on one contract behavior when possible;
- not a generated output dump.

Current fixture family:

| Path | Purpose |
| --- | --- |
| `factory/fixtures/v2/` | Regression fixtures for V2/factory control-plane behavior. |
| `factory/fixtures/incidents/` | Small incident-shaped fixtures for blocked/ready/capability edge cases. |
| `factory/fixtures/status-snapshot-v0/` | StatusSnapshot v0 cases for fail-closed/read-only operator console behavior. |
| `factory/fixtures/product-validation/` | Product-shaped validation fixtures for advanced production/onchain lanes. These are regression targets, not the default public product path. |

## What does not belong

Do not keep:

- generated worker packets;
- generated gate reports;
- generated run summaries;
- screenshots from private workspaces;
- private board exports;
- raw logs;
- local absolute paths;
- old pilot evidence;
- large archives when a small fixture proves the rule;
- product material that belongs to a private operator.

## Deletion rule

If an example or fixture cannot answer “who uses this and what test or operator path does it support?”, it should be deleted or moved out of the public package in a focused cleanup.

Keeping examples and fixtures is not automatic. They carry a burden of proof.
