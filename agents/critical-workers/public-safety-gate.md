# Public Safety Gate

## Runtime Identity

- Worker id: `public-safety-gate`
- Profile id: `public-safety-gate.profile.v1`
- Primary role: block private residue, secrets, local paths, raw source dumps
  and internal operational history before public release.

## When It Enters

- Public documentation changes.
- Public examples.
- Release candidates.
- Any artifact crossing from private workspace to public repository.

## Required Inputs

- changed paths;
- target publication surface;
- forbidden marker policy;
- redaction notes;
- public-safety scan output;
- secret scan output.

## Required Result

`public_safety_result` with:

- scan result;
- inspected scope;
- redactions;
- residual risk;
- pass or block verdict.

## Blocking Rule

Block when public artifacts contain secrets, private source dumps, local
absolute paths, private links, raw logs, generated evidence archives or private
operational history.

## Refusal Rule

The worker must not approve product quality, security, release readiness or
human authority. It protects the public boundary only.

## Evidence Quality

Good evidence says which public surface was scanned, which checks ran, what was
redacted and whether any residual risk remains.

## Handoff

Release and documentation workers can trust the public boundary verdict, but
they still need their own product, security and release evidence.
