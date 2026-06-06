# Whimsical Board

Primary editable map:

The editable Whimsical board lives in the maintainer's private visual
workspace. Public snapshots and source diagrams are kept in this repository.

Local snapshot:

`docs/maps/overkill-factory-factory-10-readable-flow-snapshot.png`

Hardening block snapshot:

`docs/maps/overkill-factory-hardening-f27-f41-snapshot.png`

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
- Map-reading legend for colors, side explanations and primary/lateral arrows.
- Multi-context validation battery as the learning-loop proof surface.
- F27-F41 operational hardening: real Codex Security, stricter gates, clean
  remote proof, remaining nota-10 gaps, a durable Whimsical MCP fallback,
  stricter Auditor/Quasar contracts, source-pinned Quasar runtime proof and
  dashboard ready/done, worker-style done no-bypass, real profile dispatch and
  official Hermes patch smokes, product-like Quasar/Auditor proof, updated
  Product Face proof and Crabbox static-SSH proof.
- Official-main patch compatibility: the public Hermes adapter patch applies to
  the tested official Hermes main commit and passes focused regression tests.

## Supporting Diagram

`docs/maps/factory-10-flow.mmd`

This supporting diagram is a strict mind-map chain: phase -> explanation ->
next phase. It is useful for review and regeneration when the editable board is
updated.

## Current Update Note

The public source diagram now includes live Hermes materialization, worker
dependency graph, negative/positive done enforcement, the multi-context factory
battery, the F27-F41 hardening block and the same map-reading legend added to
the editable Whimsical board. The editable board was updated through the local
Whimsical MCP and now contains three clean official flowchart blocks plus one
legend block:

- `Lki1eW`: main F0-F19 factory spine;
- `8kQkhJ`: F20-F26 hardening bridge;
- `AyHQAj`: F27-F41 operational hardening block.

Important current IDs in `AyHQAj`:

- F27 node id: `AyHQAj`;
- F31 node id: `Pd32Hj`;
- F36 node id: `Dkwa8P`;
- F37 node id: `NUuuFx`;
- F37 description id: `2YiC8u`.
- F38 node id: `8emoZb`;
- F38 description id: `YKnVtt`.
- F39 node id: `5AHbk4`;
- F39 description id: `8hNjNF`.
- F40 node id: `GMiHHi`;
- F40 description id: `SePcVQ`.
- F41 node id: `MyT6hD`;
- F41 description id: `BXFFri`.
- Map legend node id: `GBGPXU`.

If the editable Whimsical board is updated manually, mirror those additions
from `docs/maps/factory-10-flow.mmd`.

MCP note: older duplicate F27-F37 blocks and orphan explanatory texts were
removed through the local Whimsical MCP. A post-cleanup `board_read` showed only
the three official flowcharts above. F38 was added with `flowchart_edit`, then
the whole F27-F38 flowchart was repositioned with `board_repl` to avoid overlap.
The main F0-F19 spine was later color-coded with `flowchart_edit`, preserving
node IDs and connectors while making phases, explanations, workers and warnings
visually distinguishable. A separate map-reading legend was then added with
`flowchart_create` so users can understand colors, side explanations and
primary/lateral arrows without chat context. The F27-F38 hardening block was
then extended to F41 with `flowchart_edit` after product-like Quasar/Auditor,
updated Product Face and Crabbox static-SSH evidence passed.

Latest MCP validation:

- `python scripts/whimsical_mcp.py health` returned `PASS` with 34 tools.
- The live Desktop MCP accepted direct JSON-RPC calls even when native Codex
  tool namespaces were not exposed.
- The editable board was updated through `flowchart_edit` and verified with
  `board-read --grep "F39" --grep "F40"` and `board-read --grep "F41"`.
- The public snapshot was refreshed through the MCP after the F39/F40/F41 update.
- A dedicated F27-F41 hardening snapshot was generated through the MCP because
  the full-board snapshot is useful for orientation but too compressed for
  detailed review.

## Durable MCP Fallback

Some Codex sessions may not expose Whimsical as native callable tools even when
the desktop MCP is healthy. Use the repo wrapper instead of relying on chat
memory:

```bash
python scripts/whimsical_mcp.py health
python scripts/whimsical_mcp.py inspect-state
python scripts/whimsical_mcp.py board-read --grep "Factory 10" --format simple
python scripts/whimsical_mcp.py snapshot --board-id XVvfzk --scale 2 --out docs/maps/overkill-factory-factory-10-readable-flow-snapshot.png
```

Use `tool-call` for precise edits after inspecting the current board:

```bash
python scripts/whimsical_mcp.py tool-call --name board_read --args-json "{\"format\":\"simple\",\"limit\":50}"
```

The wrapper redacts private Whimsical URLs, local paths and maintainer identity
by default. Use `--no-redact` only for local interactive operation when the
output will not be committed.
