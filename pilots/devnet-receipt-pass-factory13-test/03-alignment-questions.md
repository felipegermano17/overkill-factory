# Alignment Questions

## Answered For This Pilot

1. Can the product touch devnet?
   Yes, read-only JSON-RPC only.

2. Can the product sign or deploy?
   No. Signing, deploy and writes are forbidden.

3. Can Auditor pass as a real code audit?
   No. Auditor may only produce preflight evidence or a waiver in this runtime.

4. Can Product Face pass without screenshots?
   No. The dashboard is a visible product surface.

5. Can release workers approve production?
   No. They can only verify that promotion remains blocked.

## Deferred For Future Work

- Real Quasar toolchain install.
- Devnet write test with a separate signing gate.
- Full Auditor corpus/code-audit run.
- Production release plan with live monitoring.
