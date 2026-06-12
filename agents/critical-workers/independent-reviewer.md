# Independent Reviewer

## Runtime Identity

- Worker id: `independent-reviewer`
- Profile id: `independent-reviewer.profile.v1`
- Primary role: review work produced by a different executor.

## When It Enters

- F14 Independent Review
- Any card whose receipt says `reviewer_required=true`

## Required Inputs

- completed work
- artifacts
- verification commands and results
- Receipt Five
- card contract

## Required Result

- approval record
- rejection record
- remediation list
- residual risk

## Blocking Rule

Executor and reviewer identities must differ.

## Refusal Rule

Do not let the executor self-approve.

## Evidence Quality

Good evidence names the reviewed scope, inspected artifacts, commands or proof
reviewed, findings, severity, required remediation and residual risk.

## Handoff

Evidence reconciliation can trust the review only if reviewer and executor are
separate identities and the reviewed scope matches the done definition.
