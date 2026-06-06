# Whimsical Board

Primary editable map:

The editable Whimsical board lives in the maintainer's private visual
workspace. Public snapshots and source diagrams are kept in this repository.

Local snapshot:

`docs/maps/overkill-factory-factory-10-readable-flow-snapshot.png`

## Why This Is The Primary Map

This board uses a vertical production-line spine. Each phase has its explanation
attached to the side, so the user can follow the full sequence without hidden
notes or branches under the wrong point.

It includes:

- F0-F19 full product factory path.
- Product Face before decomposition.
- Specialist reviews before human architecture approval.
- Hermes live adapter as the runtime bridge from factory card to real Kanban
  task graph.
- Worker packets, Hermes Ready Gate, worker results and closure summary.
- Receipt Five, missing-result done block, positive done reconciliation and
  Hermes Done Gate.
- Factory 10 + Hermes V3.5 + Hermes V2 completion compatibility.
- Critical workers, worker-role explanations and agent misread warnings.
- Multi-context validation battery as the learning-loop proof surface.
- F27-F34 operational hardening: real Codex Security, stricter gates, clean
  remote proof, remaining nota-10 gaps, a durable Whimsical MCP fallback,
  stricter Auditor/Quasar contracts, source-pinned Quasar runtime proof and
  dashboard ready no-bypass smoke.

## Supporting Diagram

`docs/maps/factory-10-flow.mmd`

This supporting diagram is a strict mind-map chain: phase -> explanation ->
next phase. It is useful for review and regeneration when the editable board is
updated.

## Current Update Note

The public source diagram now includes live Hermes materialization, worker
dependency graph, negative/positive done enforcement, the multi-context factory
battery and the F27-F34 hardening block. If the editable Whimsical board is
updated manually, mirror those additions from `docs/maps/factory-10-flow.mmd`.

## Durable MCP Fallback

Some Codex sessions may not expose Whimsical as native callable tools even when
the desktop MCP is healthy. Use the repo wrapper instead of relying on chat
memory:

```bash
python scripts/whimsical_mcp.py health
python scripts/whimsical_mcp.py inspect-state
python scripts/whimsical_mcp.py board-read --grep "Factory 10" --format simple
```

Use `tool-call` for precise edits after inspecting the current board:

```bash
python scripts/whimsical_mcp.py tool-call --name board_read --args-json "{\"format\":\"simple\",\"limit\":50}"
```

The wrapper redacts private Whimsical URLs, local paths and maintainer identity
by default. Use `--no-redact` only for local interactive operation when the
output will not be committed.
