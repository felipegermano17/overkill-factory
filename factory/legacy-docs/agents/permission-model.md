# Worker Permission Model

The Factory is modular, but modular does not mean every agent can do
everything.

Hermes Kanban remains the durable source of truth. Telegram, Discord and Cockpit
are operator interfaces, not source-of-truth layers. Workers produce bounded
results. State changes, release decisions and human gates must go through
explicit runtime contracts.

Machine-readable matrix:

- `agents/worker-permission-classes.public.json`

## Simple Rule

Each worker has a class. The class says what the worker can do, what it must
not do, and what evidence it must leave behind.

No public worker may directly approve its own work or directly mutate final card
state. The adapter and Hermes gates own durable state transitions.

## Classes

| Class | Plain purpose |
|---|---|
| `orchestrator` | Keeps phase, risk and routing coherent. |
| `memory_context` | Organizes sources, memory and context. |
| `planner` | Creates plans, architecture, docs or work graphs. |
| `builder` | Implements approved scoped work. |
| `reviewer` | Reviews evidence independently. |
| `security_reviewer` | Reviews security, privacy, supply chain, cloud, keys and agent boundaries. |
| `remote_proof` | Runs bounded proof in controlled environments. |
| `release_operator` | Prepares release, rollback and production readiness. |
| `human_record` | Records explicit human decisions. |
| `operator_interface` | Talks to the human operator through the selected primary interface. |
| `bridge` | Maps Hermes and operator-interface events without deciding product direction. |
| `read_only_projection` | Projects runtime state into a human-readable operator console. |

## Boundary

This matrix is a public contract. It is not a credential file and it does not
grant runtime authority by itself. Runtime authority still has to be enforced by
Hermes profile configuration, worker packets, adapter gates and human approvals.
