# Whimsical Board

Primary editable map:

The editable Whimsical board lives in the maintainer's private visual
workspace. Public snapshots and source diagrams are kept in this repository.

Local snapshot:

`docs/maps/overkill-factory-factory-10-readable-flow-snapshot.png`

Hardening block snapshot:

`docs/maps/overkill-factory-hardening-f27-f48-snapshot.png`

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
- F27-F48 operational hardening: real Codex Security, stricter gates, clean
  remote proof, remaining nota-10 gaps, a durable Whimsical MCP fallback,
  stricter Auditor/Quasar contracts, source-pinned Quasar runtime proof and
  dashboard ready/done, worker-style done no-bypass, real profile dispatch and
  official Hermes patch smokes, product-like Quasar/Auditor proof, updated
  Product Face proof, Crabbox static-SSH proof and release/human dry-run gate
  proof, product-like Quasar CU/fuzz/property proof, real supply-chain CI/SBOM
  proof, the completion audit guard that blocks false practical-10 claims and
  the bounded full product worker graph proof, plus managed remote-proof
  readiness probe and a scoped production-like Product Face reusable proof.
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
battery, the F27-F48 hardening block and the same map-reading legend added to
the editable Whimsical board. The editable board was updated through the local
Whimsical MCP and now contains three clean official flowchart blocks plus one
legend block:

- `Lki1eW`: main F0-F19 factory spine;
- `8kQkhJ`: F20-F26 hardening bridge;
- `AyHQAj`: F27-F48 operational hardening block.

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
- F42 node id: `FGTyHX`;
- F42 description id: `QYKicT`.
- F43 node id: `WsFSdS`;
- F43 description id: `KLR2R5`.
- F44 node id: `7LJc4P`;
- F44 description id: `KZ1QBd`.
- F45 node id: `E47LN4`;
- F45 description id: `3Wd8dT`.
- F46 node id: `Wuciiu`;
- F46 description id: `4xtNyM`.
- F47 node id: `8Lox7B`;
- F47 description id: `PAp7vS`.
- F48 node id: `82AtQw`;
- F48 description id: `Przjmg`.
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
updated Product Face and Crabbox static-SSH evidence passed. It was then
extended to F42 after real Hermes `human-gate-clerk` and `release-ops-worker`
dry-run evidence passed while keeping production blocked. The F27-F42 hardening
block and legend were then reflowed with `flexbox_compose` so the new node did
not overlap the map-reading legend. It was then extended to F43 after real
Hermes `solana-quasar-auditor` evidence added source-hash-matched
CU/fuzz/property product-like proof. It was then extended to F44 after real
Hermes `supply-chain-gate` evidence added CI permissions, action pinning,
SPDX SBOM and public scanner/test proof. It was then extended to F45 after real
Hermes `independent-reviewer` evidence confirmed the completion audit remains
`NOT_COMPLETE`, blocks `--require-complete` and preserves the six remaining
product-specific/provider-backed blockers.
It was then extended to F46 after real Hermes `independent-reviewer` evidence
confirmed the QVG full product graph reconciles ten lanes, preserves stale
Receipt Five refs as visible historical refs and keeps `reusable_for_product`
false.
It was then extended to F47 after real Hermes `remote-proof-runner` evidence
confirmed managed Crabbox broker / Blacksmith Testbox readiness remains
`PENDING`, with no credential, lease, cleanup or public leak.
It was then extended to F48 after real Hermes `product-face` evidence confirmed
the QVG public validation product has a scoped production-like Product Face
proof with `PASS`, `evidence_kind=real`, `reusable_for_product=true`, target
artifact hash and completion audit reduced to five remaining blockers.

Latest MCP validation:

- `python scripts/whimsical_mcp.py health` returned `PASS` with 34 tools.
- The live Desktop MCP accepted direct JSON-RPC calls even when native Codex
  tool namespaces were not exposed.
- 2026-06-06 recheck: the Desktop app was listening on the local MCP endpoint,
  `inspect-state` returned the editable Factory 10 board with `readwrite`
  access, and the repo wrapper redacted private URL/user/workspace data.
- 2026-06-06 recheck: `board-read --grep "F48"` returned the F48 node in the
  F27-F48 block, and direct `board_read` on `AyHQAj` + `GBGPXU` showed a
  160px vertical gap with no overlap markers.
- The editable board was updated through `flowchart_edit` and verified with
  `board-read --grep "F39" --grep "F40"`, `board-read --grep "F41"` and
  `board-read --grep "F42"`, `board-read --grep "F43"` and
  `board-read --grep "F44"`, `board-read --grep "F45"` and
  `board-read --grep "F46"`, `board-read --grep "F47"` and
  `board-read --grep "F48"`.
- The public snapshot was refreshed through the MCP after the F48 update.
- A dedicated F27-F48 hardening snapshot was generated through the MCP because
  the full-board snapshot is useful for orientation but too compressed for
  detailed review.
- The F27-F48 hardening block and map legend were reflowed with
  `flexbox_compose` after the F48 insertion to remove overlap.

## Durable MCP Fallback

Some Codex sessions may not expose Whimsical as native callable tools even when
the desktop MCP is healthy. Use the repo wrapper instead of relying on chat
memory:

```bash
python scripts/whimsical_mcp.py health
python scripts/whimsical_mcp.py inspect-state
python scripts/whimsical_mcp.py board-read --grep "Factory 10" --format simple
python scripts/whimsical_mcp.py snapshot --board-id <private-board-id> --scale 2 --out docs/maps/overkill-factory-factory-10-readable-flow-snapshot.png
```

Use `tool-call` for precise edits after inspecting the current board:

```bash
python scripts/whimsical_mcp.py tool-call --name board_read --args-json "{\"format\":\"simple\",\"limit\":50}"
```

The wrapper redacts private Whimsical URLs, local paths and maintainer identity
by default. Use `--no-redact` only for local interactive operation when the
output will not be committed.
