# Product Face Proof Runner

Product Face is the proof that the product has a usable face, not only a
backend or architecture.

## When It Runs

Run for any card with surfaces:

- `ux`
- `frontend`
- `mobile`
- `wallet-ui`
- `product-face`

## Required Evidence

- desktop screenshot;
- mobile screenshot;
- important state matrix;
- empty/loading/error/success states when applicable;
- accessibility basics;
- visual overlap check;
- user-facing copy sanity;
- wallet flow evidence when wallet UI exists;
- performance budget note.

## Output

`product_face_result` with:

- screenshots;
- checked states;
- viewport list;
- checked user journeys;
- issues found;
- blocking findings;
- accessibility result;
- visual overlap result;
- performance note;
- evidence refs;
- next action.

The public schema is `schemas/product-face-result.schema.json`.

## Minimal Runner

Use the repo runner for static HTML or a local/public URL:

```bash
python scripts/product_face_proof.py --target pilots/quasar-vault-guard-test/product-face/prototype.html --out validation/product-face/product-face-result.json
```

Useful options:

- `--viewport desktop=1440x900 --viewport mobile=390x844`
- `--state loading --state error --state success`
- `--journey "open target" --journey "inspect mobile viewport"`
- `--strict` to treat accessibility and overlap warnings as blocking.
- `--force-fallback` to register bounded static evidence without a browser.

With Python Playwright available, the runner captures screenshots, console
messages, DOM state, accessibility basics, overlap scan and a browser-local
performance note. Without Playwright, it writes a `WAIVED` result with
`blocking_findings=true`, static file metadata, and an explicit note that no
rendered screenshot, console, layout, accessibility tree or performance claim
was captured.

For product-facing completion, Receipt Five must include
`product_face_result`. A Product Face Packet is planning; a Product Face Result
is proof.

## Local Runner

Use:

```bash
python scripts/product_face_proof.py --target pilots/quasar-vault-guard-test/product-face/prototype.html --out validation/product-face/product-face-result.json
```

If Python Playwright and its browser are available, the runner captures rendered
evidence. If they are not available, it writes a bounded `WAIVED` result with
`blocking_findings=true`.

That fallback is intentional. Static HTML metadata is not visual proof. It is a
receipt that the Product Face worker tried to run and that the card must remain
blocked until real browser evidence exists.

## Current Boundary

The current public validation includes static fallback evidence and partial
in-app browser screenshot attempts. It does not claim full Product Face PASS.

Full Product Face PASS requires:

- desktop screenshot;
- mobile screenshot;
- console check;
- important UI-state coverage;
- accessibility basics;
- overlap/layout check;
- performance note;
- evidence refs attached to Receipt Five.

## Why This Is Better

A Product Face Packet says what should exist. Product Face proof shows what
actually rendered. Agents often complete backend or component work while the
user-facing product is broken, missing states or unusable on mobile.
