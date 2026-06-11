# Expected Flow

The minimal project should move through Hermes as a controlled local validation
flow.

## Expected Gates

1. Source is compiled from `input-paper.md`.
2. Product SOT and scope boundaries are visible in the card.
3. Product Face packet exists because this is a visible product surface.
4. Hermes can create required worker cards from the gate report.
5. Completion blocks until Product Face evidence exists.
6. Completion blocks until Receipt Five points to current evidence.
7. Independent review is required before completion because the card asks for
   it.

## Expected Agents

- `factory-orchestrator` checks phase, risk and routing.
- `product-face` owns visible surface proof.
- `qa-verification-worker` checks the local validation evidence.
- `independent-reviewer` reviews the output without being the executor.
- `evidence-reconciler` checks that Receipt Five and worker results agree.
- `public-safety-gate` is used before publishing changed artifacts.

Control Tower is optional. If configured, it can show status and request review,
but Hermes cards and receipt artifacts remain the source of truth.

## Expected Output

For a local dry run, expected output is:

- a valid-card result;
- a gate report;
- worker packets under `.tmp/minimal-worker-packets`;
- a Product Face result once the screen is actually checked;
- a Receipt Five artifact shaped like `expected-receipt-five.json`.

The example does not prove production readiness, deployment, real customer
traffic, wallet behavior or external system mutation.
