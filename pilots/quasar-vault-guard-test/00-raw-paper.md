# Raw Product Paper: Quasar Vault Guard

## Messy Original Notes

We need a small factory-style product for monitoring Solana vault safety before
money moves.

The user should open a page, connect wallet, see if a vault action is safe, and
know whether an instruction can be executed. It should be "one screen first",
but later maybe admin mode, simulation, historical diffs, alerts, Telegram, and
autonomous remediation.

Important: example program must be Quasar, not Anchor. The onchain program should
be the heart later, but for the first slice do not touch devnet/mainnet, keys,
funds, custody, signer authority, or production.

Maybe the product reads:

- vault account;
- signer authority;
- token account;
- pending instruction;
- expected PDA;
- CPI allowlist;
- compute budget;
- last audit status.

The UI must not be a backend-only thing. It needs a real face: desktop and
mobile, wallet states, loading, error, rejected signing, simulation failed, safe,
blocked, and unknown.

Security is critical. No agent should say "looks fine" without evidence.
Codex Security/Cybersecurity must scan at the right moment. Onchain needs
Auditor. If no Auditor can run because there is no real program yet, we need a
clear preflight result, not fake approval.

Human approval is required before architecture becomes decomposition and before
any R3/R4 action. The product owner authorized in the intake record on 2026-06-05 that Codex is authorized to
run this test pilot and use a test paper, but that is not production approval.

First slice idea:

- build visible Product Face prototype and evidence package;
- create onchain package and Auditor preflight;
- create security scan packet and scan report;
- create Hermes card and complete it with Receipt Five.

Out of scope:

- real deploy;
- devnet writes;
- mainnet writes;
- wallet signing;
- private keys;
- funds;
- custody;
- production release.

Concerns:

- Agents may confuse paper approval with implementation approval.
- Agents may treat Auditor "prepared" as Auditor "passed".
- Product Face may get skipped if no frontend code exists.
- A human gate record can be faked if evidence policy is weak.
