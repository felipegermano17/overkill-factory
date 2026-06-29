# Incident Replay Fixtures

These fixtures capture production-shaped failure modes that must stay
deterministic:

- an earlier blocked phase prevents future ready/running work from dispatching;
- text-only approval prose is not a human gate;
- Solana/onchain work requires the Solana AI Kit domain-brain provider or usage
  receipt before execution.

They are public-safe and intentionally small. The replay test materializes any
template card patches before calling the board reconciler, then asserts the
exact reducer action expected for the incident.
