# Critical Worker Automation

Use `scripts/factoryctl.py` in the Overkill Factory repository when cards need
to be converted into execution requests for specialists.

## Commands

```bash
python scripts/factoryctl.py validate-card path/to/card.md
python scripts/factoryctl.py validate-receipt path/to/receipt.json
python scripts/factoryctl.py gate-report --card path/to/card.md
python scripts/factoryctl.py worker-packet --worker all --card path/to/card.md --out path/to/worker-packets
python scripts/validate_worker_profiles.py
python scripts/factoryctl.py evidence-record --worker codex-security --card path/to/card.md --result PASS --tool codex-security:security-scan --actor security-runner --evidence-ref path/to/report.md
python scripts/factoryctl.py human-gate-record --card path/to/card.md --decision approved --human-actor product-owner --evidence-ref path/to/decision.md
```

## Worker Packets

Worker packets are not evidence. They are execution requests. They tell Hermes:

- which specialist is required;
- why the specialist is required;
- what input fields are missing;
- which Hermes profile and skill refs should execute the work;
- what output field must appear in Receipt Five;
- which gate remains blocked until real evidence exists.

The profile data comes from:

- `agents/worker-profiles.public.json`
- `agents/hermes-profile-bindings.public.json`

If a worker has no profile or binding, it is not an operable agent yet.

Use `evidence-record` only after the specialist really ran.
Use `human-gate-record` only after the human decision really happened.

## Critical Rules

- Codex Security Runner writes `security_scan_result`.
- Solana/Quasar Auditor Runner writes `auditor_result`.
- Product Face Validator writes `product_face_result`.
- Independent Reviewer writes `independent_review_result`.
- Human Gate Clerk writes `human_gate_record`.
- R3/R4 require `human_gate_packet`.
- R4 additionally requires `r4_gate`.
- Do not represent scan, Auditor, screenshot, review, or approval evidence with
  prose alone.
