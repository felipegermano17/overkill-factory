# Discord Cockpit UX Study Gate

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `schemas/discord-control-tower-ux-audit.schema.json`,
> `templates/discord-control-tower-ux-audit.json`, #80 status snapshots and #82
> Product Face visual quality.
> Runtime boundary: Discord is optional projection and operator interaction. It
> is not the source of truth.

This gate exists because Discord is attractive but risky as a factory cockpit.
Chat is familiar, but factory operation needs state clarity, freshness,
auditability, low noise, safe approvals and fast operator comprehension.

No Discord cockpit implementation is accepted until the factory produces:

1. a public-safe Discord Cockpit UX Study;
2. a Discord Control Tower UX Proof Pack for the chosen shape;
3. Product Face visual quality review for the visible operator surface.

## Source Material

The study must read Discord as it is, not as a generic chat metaphor. Required
source areas include:

- Discord interactions overview:
  `https://docs.discord.com/developers/interactions/overview`;
- receiving and responding to interactions:
  `https://docs.discord.com/developers/interactions/receiving-and-responding`;
- application commands:
  `https://docs.discord.com/developers/interactions/application-commands`;
- component reference:
  `https://docs.discord.com/developers/components/reference`;
- threads:
  `https://docs.discord.com/developers/topics/threads`;
- permissions:
  `https://docs.discord.com/developers/topics/permissions`;
- rate limits:
  `https://docs.discord.com/developers/topics/rate-limits`;
- webhooks:
  `https://docs.discord.com/developers/resources/webhook`.

## Discord Material Facts

Discord gives the factory useful primitives:

- server categories, text channels, forums, threads and pins for navigation;
- slash commands, message commands and user commands for native actions;
- buttons, select menus and modals for structured interaction;
- roles, permission overwrites and command permissions for access control;
- webhooks for low-friction message projection;
- message edits for stable dashboard panels;
- notification controls, thread membership and archive behavior for attention
  management.

Those primitives have consequences:

- an interaction needs an initial response quickly, so long work needs defer,
  follow-up or runtime handoff;
- follow-up interaction tokens expire, so formal approvals need a durable
  runtime registration path and a validated fallback;
- component-rich messages use Discord's component model and layout limits, so
  dense dashboards can become cramped;
- threads can archive, hide from users without access, or split attention;
- permissions are layered by guild, channel, thread, role and user, so the
  study must test wrong-role and missing-permission cases;
- rate limits are per-route and global, so active multi-agent updates must
  coalesce, edit in place and retry from response headers;
- webhooks are easy to post with but create token custody and attribution
  boundaries;
- mobile and desktop scanning differ enough that a desktop-only proof is not a
  real cockpit proof.

## Operator Comprehension Contract

The cockpit has to answer different questions at different speeds.

In the first 5 seconds, the operator must know:

- whether anything needs attention;
- whether the displayed state is fresh;
- where the next safe action lives.

In the first 30 seconds, the operator must know:

- current phase;
- real blockers;
- pending approvals;
- missing access;
- latest evidence reference;
- whether Discord is projecting canonical runtime state or stale/manual state.

In the first 5 minutes, the operator must be able to inspect one project and
decide whether to approve, wait, grant access, ask for clarification, or move
to the local web cockpit for deeper inspection.

If any of those jobs requires hunting across channels, reading a long transcript
or guessing whether chat equals approval, Discord is not good enough for that
job.

## Recommended Role

Default recommendation:

```text
Discord = secondary operator cockpit, notification surface and structured approval inbox
local web cockpit = dense state, comparison, inspection and long-running control
runtime/Hermes = source of truth
```

Discord may become a primary cockpit only after the proof pack shows equal or
better comprehension, freshness and safety than the local web cockpit for the
specific operator workflow.

Discord should own:

- attention routing;
- short status projection;
- project conversation thread entry;
- structured approval request display;
- access/blocker/release notifications;
- links back to canonical evidence.

Discord should not own:

- canonical state;
- dense multi-project comparison;
- long-running evidence inspection;
- visual Product Face review;
- approval truth without runtime registration;
- hidden worker chatter.

## UX Proof Pack

The proof pack must measure practical operator consequences, not architecture
intent.

Required proof:

- comprehension at 5 seconds, 30 seconds and 5 minutes;
- findability of the next safe action;
- dashboard update behavior using edit-in-place where possible;
- approval/request boundary clarity;
- stale state display and recovery;
- duplicate event replay/idempotency;
- bridge-offline behavior;
- rate-limit retry behavior;
- notification volume during active multi-agent runs;
- desktop and mobile readability;
- public-safe output with no private Discord ids, tokens, channel names, raw
  logs, runtime URLs or local paths.

Required negative tests:

- stale status snapshot;
- duplicate bridge event;
- expired interaction fallback;
- approval from the wrong role;
- free-form chat treated as approval;
- missing runtime registration path;
- rate limit response during dashboard projection;
- archived or inaccessible thread.

## Gate Decision

Use `templates/discord-control-tower-ux-audit.json` to record the study gate.

Allowed recommendations:

- `reject`;
- `notification_surface_only`;
- `approval_inbox_only`;
- `secondary_operator_cockpit`;
- `primary_operator_cockpit_after_proof`.

The public factory default is `secondary_operator_cockpit` with
`required_for_dense_state` web cockpit boundary. That is intentionally
conservative: Discord is useful, but the factory must prove it is excellent
before it can carry dense operational control.

## Dependencies

The Discord cockpit study depends on:

- #80 because Discord must project canonical status snapshots rather than make
  up state;
- #82 because visible cockpit UX needs Product Face visual quality review;
- #84 because dense state and inspection should move to the local web cockpit
  unless Discord proof demonstrates that the chat surface is better.

## Public Safety

Do not publish:

- private Discord ids;
- private channel names;
- bot tokens or webhook tokens;
- private runtime URLs;
- raw Discord logs;
- local operator paths;
- screenshots from a private server unless explicitly sanitized and approved.

Public artifacts should use schema-valid summaries, redacted evidence refs and
stable methodology, not live workspace evidence.
