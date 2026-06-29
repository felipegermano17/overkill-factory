# Security and release

Security and release are not final decorations. They are part of the factory method.

## Security before implementation when risk is material

If work touches secrets, keys, money, user data, production, onchain programs, permissions, authentication, supply chain or public release, the factory should route security thinking before or during planning.

Security review after implementation can catch issues, but it cannot replace security architecture for high-risk work.

## Risk surfaces

The factory should identify whether work touches:

- secrets or credentials;
- production systems;
- customer/user data;
- payments or funds;
- Solana/onchain programs;
- admin permissions;
- authentication;
- supply chain;
- deployment automation;
- public product claims;
- rollback and monitoring.

Each surface changes gates and evidence.

## Human authority

Some decisions cannot be delegated to the model.

Examples:

- approving production release;
- accepting material risk;
- approving cost;
- granting access;
- handling private keys or secrets;
- moving funds;
- approving mainnet actions;
- changing customer-facing claims.

The manager should present a human gate package, not bury the decision inside a status update.

## Release gate

Release requires more than passing tests.

A release gate should answer:

- what is being released;
- where it is being released;
- what changed since the last state;
- how rollback works;
- who owns the release;
- what monitoring exists;
- what evidence supports promotion;
- what risk remains;
- whether human approval is required.

## Public repository safety

The public repository is a product surface.

Do not publish:

- raw study dumps;
- private local paths;
- chat artifacts;
- screenshots from private workspaces;
- credentials or tokens;
- internal acceptance notes;
- generated temporary proof archives;
- docs that only make sense inside one private session.

Public docs should explain the product. Internal artifacts belong outside the public repo or in clearly separated private workspaces.

## Honest status

Security and release claims must be precise.

“Local tests passed” is not the same as “live release is safe.”
“Secret scan passed” is not the same as “the production secret process is approved.”
“Docs build passed” is not the same as “the operator experience is live.”

The factory should say exactly what was proven.
