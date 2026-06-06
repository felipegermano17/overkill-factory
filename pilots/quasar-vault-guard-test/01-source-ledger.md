# F0-F1 Source Ledger And Resolution

## Source Ledger

| ID | Source | Type | Status | Notes |
| --- | --- | --- | --- | --- |
| S1 | `00-raw-paper.md` | raw product paper | promoted | Primary test input. Messy by design. |
| S2 | User instruction in Codex chat on 2026-06-05 | human authorization | promoted for test only | Authorizes this pilot, not production deploys or fund movement. |
| S3 | Overkill Factory V0 methodology | internal method | promoted | Governs F0-F18 flow. |
| S4 | Hermes adapter patch evidence | runtime evidence | promoted | Proves gate model and exit-code enforcement. |
| S5 | solanabr/Auditor repository HEAD `38ceb3fabc811d62e1d6172bd23e110af502d8e6` | external tool reference | promoted as required path | Used as mandatory onchain audit route reference. |
| S6 | solanabr/solana-claude repository HEAD `d653daceb005fc7568bfe0f33e4195afbfb2f7c1` | external agent reference | promoted as methodology input | Confirms Solana specialist-agent pattern remains relevant. |

## Resolved Claims

| Claim | Resolution | Why |
| --- | --- | --- |
| The first slice must include a visible product face. | Promoted. | Backend-only work would not prove Product Face gates. |
| Quasar is required; Anchor assumptions are forbidden. | Promoted. | This is a hard Overkill constraint from the raw paper and prior factory rules. |
| Auditor is required for onchain work. | Promoted. | The pilot includes onchain risk surface, so Auditor path must be present. |
| Production/devnet/mainnet writes are authorized. | Rejected. | User authorized this test goal, not key/funds/network actions. |
| Human approval can be simulated silently. | Rejected. | The record must cite the real chat authorization and remain scoped to test pilot only. |
| Security review prose is enough. | Rejected. | The factory requires structured scan evidence and blocking policy. |

## Conflict Matrix

| Conflict | Decision | Why This Is Better |
| --- | --- | --- |
| Need onchain proof vs no real program yet. | Run Auditor preflight against the onchain package, not a fake pass. | Preserves the mandatory Auditor path without inventing results. |
| Need Product Face evidence vs no full app. | Build a static prototype and screenshot it. | Gives real visual evidence without expanding scope into full product build. |
| Need human gate vs no separate approval meeting. | Record the current user authorization as test-only human gate evidence. | Honest and traceable; avoids fake approval while unblocking a dry pilot. |
