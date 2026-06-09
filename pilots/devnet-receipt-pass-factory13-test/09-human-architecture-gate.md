# Human Architecture Gate

Decision: approved for validation only.

Proof boundary: the actual operator authorization is external to this public
repository. The public artifact records the scope and constraints, but it is not
a reusable production approval.

Approved scope:

- Create local product files.
- Read Solana devnet via JSON-RPC.
- Generate worker packets and validation evidence.
- Close the factory card if all automated gates pass.

Forbidden scope:

- Signing.
- Devnet write.
- Mainnet write.
- Deploy.
- Secrets.
- Funds.
- Custody.
- Production release.

This gate is not approval for production. It exists to test the factory line and
the agent contracts. Any future production, deploy, signing, write, custody or
funds action needs a new human gate with its own evidence.
