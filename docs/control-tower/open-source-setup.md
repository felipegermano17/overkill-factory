# Open Source Control Tower Setup

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py`, schemas, tests and current public guides.
> Runtime boundary: This guide configures the optional Control Tower; it does not create durable evidence or close factory gates.

The Control Tower is optional. It can make factory work easier to watch, but it
is not the source of truth.

## Source Of Truth Rule

Hermes Kanban state, worker result artifacts and Receipt Five are authoritative.
Discord messages, dashboards, webhooks and status summaries are operator views.
They can notify, request approval or show progress, but they must not close work
without the same receipts and gates.

## Run Without Discord First

Start with local validation:

```bash
python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
```

Add Discord only after the card and worker packet path is clear.

## Safe Environment Template

Use `.env.example` for variable names. Keep real values outside commits.

Minimum optional settings:

```bash
DISCORD_CONTROL_TOWER_ENABLED=false
DISCORD_BOT_TOKEN=example
DISCORD_GUILD_ID=example-guild-id
DISCORD_STATUS_CHANNEL_ID=example-status-channel
DISCORD_APPROVAL_CHANNEL_ID=example-approval-channel
```

Replace placeholder values only in your private runtime environment.

## Suggested Channels

Use role-based channel names rather than private ids in public docs:

| Channel | Purpose |
| --- | --- |
| `factory-status` | Human-readable progress summaries. |
| `factory-approvals` | Human gate requests and decisions. |
| `factory-incidents` | Blockers, failed scans and release concerns. |
| `factory-receipts` | Public-safe links to evidence and Receipt Five refs. |

## Permissions

The bot should have only the permissions it needs:

- read and send messages in factory channels;
- create threads if you use per-card discussion;
- attach files only for public-safe artifacts;
- no server administration by default;
- no access to private credentials or local-only evidence folders.

## Human Gates

High-risk cards can request approval through a Control Tower, but the final
record must be a structured human gate artifact. A message that says "approved"
is not enough unless it is captured into the required receipt field with scope,
actor role, decision, timestamp and evidence refs.

## What Not To Put In The Control Tower

Do not post:

- real secrets or tokens;
- private runtime paths;
- raw source dumps;
- private board or workspace links;
- unredacted logs;
- real wallet keys, account ids or funds-related material.

When in doubt, post a repo-relative evidence ref or a redacted summary and keep
the raw detail in a private evidence store.
