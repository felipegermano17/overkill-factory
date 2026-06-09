# Managed Remote Proof Probe

Result: `PENDING`
Managed remote proof ready: `false`
Reusable for product approval: `false`

## Findings

Managed remote proof is not ready: crabbox CLI is not available on PATH; Crabbox broker/provider credentials are not configured for aws/azure/gcp/hetzner; Blacksmith Testbox CLI/config is not ready

## Required For Completion

- crabbox broker or blacksmith-testbox credentials
- provider-backed run handle
- remote command transcript
- artifact refs
- cleanup or stop evidence
- public-safe PASS remote_proof_result reusable only for the product target

## Boundary

This probe does not lease a managed runner, run product tests, collect provider cleanup evidence, or satisfy managed_remote_proof.
