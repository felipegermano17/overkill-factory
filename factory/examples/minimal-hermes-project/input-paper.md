# Input Paper: Receipt Pass

Receipt Pass is a tiny web product for teams that need to prove whether a work
item is actually done.

## Problem

Teams often close agent work with a chat message but cannot later answer what
changed, which checks ran, who reviewed it or what remains open.

## Proposed Product

Build a read-only local web screen that shows one work item and its Receipt Five
status.

The first slice should show:

- item title;
- current phase;
- required worker evidence;
- review status;
- human gate status;
- final receipt status.

## Non-Goals

- No production deploy.
- No real customer data.
- No Discord dependency.
- No wallet, signing, funds or onchain behavior.

## Acceptance Criteria

- The screen has loading, empty, success and blocked states.
- Mobile and desktop layouts are readable.
- The completion state points to a Receipt Five artifact.
- The card cannot close without Product Face evidence and Receipt Five.
