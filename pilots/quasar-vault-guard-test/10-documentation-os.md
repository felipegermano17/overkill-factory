# F10 Documentation OS

## Operating Docs

| Artifact | Purpose |
| --- | --- |
| `00-raw-paper.md` | Raw source input. |
| `01-source-ledger.md` | Source resolution and conflicts. |
| `02-product-sot.md` | Product truth for the pilot. |
| `04-architecture-candidate.md` | System design and authority boundaries. |
| `05-product-face-packet.md` | UI/state/mobile/a11y contract. |
| `07-onchain-work-package.md` | Quasar-only onchain package. |
| `08-security-scan-packet.md` | Security timing and acceptance policy. |
| `cards/qvg-first-slice.md` | First executable Factory card. |
| `evidence/receipt-five-first-slice.json` | Done evidence. |

## Decision Records

| Decision | Why This Over Alternative |
| --- | --- |
| Use a synthetic but difficult test product. | Better than waiting for a real paper because it exercises the factory now. |
| Keep all sensitive actions out of scope. | Better than a broader pilot because it tests control without risking keys/funds/network state. |
| Use Product Face prototype as first slice. | Better than backend docs because it proves visible product work is part of done. |
| Run Auditor preflight, not Auditor pass. | Better than fake audit because no Quasar code exists yet. |
| Cite chat authorization as human gate evidence. | Better than blocking forever and better than pretending a separate approval happened. |

## Evidence Paths

- Product Face: `evidence/product-face-validation-report.md`
- Security: `evidence/security-scan-report.md`
- Auditor: `evidence/auditor-preflight-report.md`
- Review: `evidence/independent-review-report.md`
- Human gate: `evidence/human-gate-record.json`
- Receipt Five: `evidence/receipt-five-first-slice.json`

## Test Strategy

1. Validate Factory card with `factoryctl.py validate-card`.
2. Generate gate report.
3. Generate required worker packets.
4. Validate prototype with screenshot evidence.
5. Create structured worker results.
6. Create and complete Hermes pilot card with Receipt Five.
7. Convert pilot lessons into V3.6 learning record.
