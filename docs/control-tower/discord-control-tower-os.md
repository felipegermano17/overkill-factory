# Discord Control Tower OS

Discord Control Tower OS is the owner-facing control layer for Overkill
Factory.

It makes the factory understandable and operable without turning Discord into
the source of truth.

For the practical Portuguese production setup guide, see:

```text
docs/control-tower/discord-control-tower-setup-pt-br.md
```

For the study on making Discord dynamic instead of a plain chat feed, see:

```text
docs/control-tower/discord-dynamic-control-tower-study-pt-br.md
```

## Decision

```text
Discord = human cockpit
Hermes or selected runtime = durable source of truth
Overkill Factory = method, gates, workers and evidence
Factory Concierge = official owner-facing voice
```

The owner creates or grants the Discord server. The factory owns everything
after that: event contracts, bridge behavior, structured approvals, health
checks, anti-spam, evidence links, and runtime registration.

## What This Layer Does

It shows:

- project status;
- current phase;
- blockers;
- pending access;
- pending approvals;
- forecast and next steps;
- forecast confidence;
- evidence links;
- release decisions;
- incident alerts;
- bot and bridge health.

It asks for:

- understanding approval;
- plan approval;
- access approval;
- budget approval;
- risk approval;
- scope-change approval;
- release approval;
- production approval.

## Project Intake UX Contract

The owner can start from `#falar-com-gerente`, but a project must not live as a
loose chat transcript.

The bridge must separate two cases:

```text
short operational question -> answer in the same chat
paper, long brief, new product or pilot -> create project thread and forum card
```

For a project intake, the Discord layer should create:

- a project conversation thread tied to the intake message or intake channel;
- a `kanban-da-fabrica` forum post with the initial phase tag;
- a short pointer message in `#falar-com-gerente`;
- a runtime mapping record once Hermes creates or updates the durable card.

Hermes native Discord free-response channels are useful for low-friction chat,
but they are not enough for factory intake. They can answer inline. The factory
needs the Concierge bridge to create the project surface deliberately.

## Complete UX Contract

The Discord layer is good only when the owner understands the system without
asking which channel to use.

The practical contract is:

- `#falar-com-gerente` is the main door;
- `#torre-de-controle` is the global portfolio view, not a message dump;
- `kanban-da-fabrica` is the project index, not the place for every detail;
- each project topic is the project cockpit;
- `#projetos-recebidos` is an operational registry, not a second owner intake
  door;
- approvals, access, blockers, evidence and releases each have their own lane;
- every operational channel has a short pinned Portuguese guide;
- the Kanban forum has guide/status tags that distinguish a real project from
  help content;
- every project cockpit shows the factory pipeline, progress, blockers,
  missing gates, next action and forecast;
- retries must not create duplicate project threads, forum cards, approvals or
  blocker messages.

The owner should not need to remember commands, English words or Hermes
internals. The GERENTE explains, routes and points to the visual surface.

## Channel UX Map

| Surface | Owner meaning | Required behavior |
| --- | --- | --- |
| `#torre-de-controle` | "What is happening across the factory?" | Portfolio dashboard with active projects, stage, progress and alerts. |
| `#falar-com-gerente` | "Talk to the factory" | Short questions stay inline; project intake gets project surface. |
| `#projetos-recebidos` | "What entered?" | Registry of received projects; points to the project thread/card. |
| `kanban-da-fabrica` | "Which projects exist?" | One topic per project; it is an index, not a detailed task board. |
| project topic | "Where is this project, exactly?" | Project cockpit with pipeline, percent, blockers and next action. |
| `#aprovacoes-formais` | "My decisions" | Approvals must carry scope, risk, deadline and runtime registration. |
| `#acessos-pendentes` | "What do I need to grant?" | Shows missing accounts, permissions and impact without exposing secrets. |
| `#bloqueios-reais` | "Why did it stop?" | Shows only blockers that materially stop or limit progress. |
| `#provas-e-evidencias` | "What was proven?" | Mirrors receipts, tests and validation references without becoming canonical. |
| `#producao-e-releases` | "Can this go live?" | Shows readiness, rollback and production decision state. |
| `#saude-do-bot` | "Is the cockpit alive?" | Shows bot, Hermes, gateway and bridge health. |

## Thread Rule

The owner is right to expect active bot messages to create a conversation
surface.

Rule:

```text
notification, health ping or dashboard update -> no thread required
question, decision, access, blocker, evidence discussion, review or project
conversation -> thread required
```

For active work, the bot should either:

- create the thread;
- post inside the existing thread; or
- point clearly to the existing thread.

This keeps `#falar-com-gerente` useful without letting it become a long,
unsearchable transcript.

## Multi-Project Kanban Rule

The Discord Kanban can support multiple projects if the bridge treats the forum
as a project index, not as the full project workspace:

- one forum topic per project;
- one stable project mapping per topic;
- phase tags updated from runtime state;
- guide/help topics tagged as `Guia`, not as blocked projects;
- retries update the existing topic instead of creating duplicates.

Without idempotent project mapping, the Kanban is only a manual visual aid, not
a production-ready multi-project cockpit.

The current public implementation for that mapping is:

```text
scripts/factory_concierge_discord_bridge.py
```

It receives a `project-projection.json`, updates the global dashboard, the
project registry, the project forum topic and the project cockpit, then stores
real Discord ids only in a private state file outside the public repository.

The forum must stay clean. It should answer:

```text
which projects exist?
which phase is each project in?
which project needs attention?
```

It should not show every microtask from every project at once.

## Project Cockpit and Predictability

The project topic is the detailed cockpit for one project.

Every active project topic must have a pinned or easily findable pipeline panel
that shows:

- project name;
- current factory stage;
- estimated completion percentage;
- completed stages;
- current stage;
- remaining stages;
- next action;
- missing access;
- pending approvals;
- real blockers;
- latest evidence;
- forecast confidence;
- source/runtime freshness note.

The factory pipeline is predictable, so the cockpit must make that visible. The
owner should never need to infer progress from scattered messages.

Recommended pipeline display:

```text
Entrada -> Fonte/SOT -> Metodo/planejamento -> Arquitetura/UX/seguranca
-> Acessos/gates -> Execucao -> Revisao/provas -> Producao
-> Operacao/aprendizado
```

Each stage should be one of:

```text
done | current | pending | blocked | skipped
```

The percentage is an operator forecast, not proof by itself. It becomes
trustworthy only when the bridge computes it from runtime state and labels stale
or manual projections clearly.

The bridge projector treats `project-projection.schema.json` as the boundary.
If the projection says `runtime_fresh`, it can show fresh state. If the upstream
runtime export is stale or manual, the projection must say so; the Discord layer
must not hide that from the owner.

## View Hierarchy

The Discord UX follows this hierarchy:

```text
#falar-com-gerente = one human door
#torre-de-controle = global portfolio dashboard
kanban-da-fabrica = project index
project topic = project cockpit and pipeline progress
decision/access/blocker/evidence/release channels = alert lanes with links back
```

## What This Layer Must Not Do

It must not:

- store secrets;
- replace Hermes or the selected runtime;
- approve risk on behalf of the owner;
- let free-form chat become sensitive approval;
- let specialist workers interrupt the owner by default;
- treat Discord message history as canonical evidence;
- bypass ready, done, release or human gates.

## Factory Concierge

The Factory Concierge is the owner-facing agent.

It:

- explains the state in plain language;
- consolidates worker outputs;
- asks structured questions;
- records owner decisions back into the runtime;
- protects the owner from noisy worker updates;
- makes blockers and next steps visible.

It cannot:

- approve for the owner;
- hide risk;
- invent runtime status;
- mark work complete without evidence.

## Bridge

The Discord Control Tower Bridge maps runtime events to Discord messages and
maps structured owner responses back to durable runtime events.

It must be idempotent.

Retrying an event must not duplicate approvals, blockers or worker tasks.
Retrying a project-intake event must not create duplicate project threads or
duplicate forum cards.

The bridge has no authority to mark factory work `ready`, `done`, released, or
approved by itself. It can only request that the runtime records a structured
event. The runtime and Overkill gates decide whether that event is valid.

The practical project projection command is:

```bash
python scripts/factory_concierge_discord_bridge.py \
  --projection /private/path/to/project-projection.json \
  --state /private/path/to/discord-bridge-state.json \
  --env /private/path/to/hermes.env \
  --apply \
  --out /private/path/to/bridge-health.json
```

Use `--dry-run` first when wiring a new server. The state file is private
because it contains Discord ids. The output receipt must follow
`schemas/operator-control-tower-bridge-health.schema.json` and the public copy
must redact ids, paths, tokens, URLs and logs.

## Minimum Contracts

The control layer uses:

- `control-tower-event.schema.json`;
- `project-projection.schema.json`;
- `approval-request.schema.json`;
- `discord-control-tower-mapping.schema.json`;
- `operator-control-tower-bridge-health.schema.json`.

The production gate also uses:

- `operator-control-tower-production-readiness.schema.json`;
- `hermes-production-proof.schema.json`.

## Rollout Order

1. Read-only status and health.
2. Project projection.
3. Blocker and forecast messages.
4. Evidence links.
5. Structured approval requests.
6. Approval response registration in the runtime.
7. Bypass and permission tests.

Structured approvals must not ship before runtime registration is proven.

The first useful milestone is not "a bot can post messages". The first useful
milestone is "the owner can see the real runtime state without the Discord layer
being able to mutate it".

The second useful milestone is "a structured owner approval can travel from
Discord back into the runtime and be rejected when the approval is malformed,
expired, sent by the wrong role, or outside the requested scope".

The public contract smoke for this rule is:

```text
validation/control-tower/control-tower-approval-registration-smoke.json
```

## Production Proof Harness

The production gate is stricter than the local contract smokes.

The local smokes prove:

- a read-only owner projection can be derived without mutating runtime state;
- a structured approval can become a runtime-registerable event;
- malformed, expired, wrong-role, unknown or scope-expanded approvals are
  rejected.

They do not prove that the owner's real Discord server, channels, roles, bridge
and runtime registration path exist.

Use the harness below after the real server/mapping exists:

```bash
python scripts/operator_control_tower_proof.py \
  --mapping /private/path/to/discord-control-tower-mapping.json \
  --runtime-registration-event /private/path/to/runtime-approval-event.json \
  --bridge-health /private/path/to/bridge-health.json
```

The `--bridge-health` file must follow
`schemas/operator-control-tower-bridge-health.schema.json`. A generic JSON file
with only `result: PASS` is not enough.

The harness also checks that the mapping and runtime approval event refer to
the same project, that the mapping contains a real board reference, that the
approval event has a real event id, and that bridge health carries non-empty
external evidence refs.

Use this public-safe helper when preparing the private evidence:

```text
docs/control-tower/operator-control-tower-private-evidence-kit.md
```

The script writes:

```text
validation/control-tower/operator-control-tower-production-readiness.json
```

If all checks pass, it also writes:

```text
validation/hermes-production-proof/operator-control-tower.json
```

The public output must stay redacted. Real Discord ids, private runtime ids,
URLs, tokens, webhooks and logs belong only in private operator evidence.

## Gate Rule

The Control Tower Gate blocks material execution from being invisible to the
owner when the work needs human tracking, approval, access, cost visibility,
material risk handling or release control.

When this layer is active, the factory needs:

- fresh project projection;
- correct approval channel;
- visible blockers;
- runtime registration path;
- bot/bridge health signal.

## Minimum Practical Server Shape

The recommended Discord setup is intentionally small, but it should be clear
and Portuguese-first for the owner:

- `01 COMECE AQUI`
  - `#torre-de-controle`
  - `#falar-com-gerente`
  - `#saude-do-bot`
  - `sala-de-voz-gerente`
- `02 PROJETOS E KANBAN`
  - `#projetos-recebidos`
  - `kanban-da-fabrica`
- `03 DECISOES E PENDENCIAS`
  - `#aprovacoes-formais`
  - `#acessos-pendentes`
  - `#bloqueios-reais`
- `04 PROVAS E PRODUCAO`
  - `#provas-e-evidencias`
  - `#producao-e-releases`
- `99 ARQUIVO`
  - canais antigos ou migrados.

The server can become richer later, but the factory should not require a large
Discord bureaucracy to start.

The dashboard should be updated in place when possible. The Control Tower is a
human cockpit over runtime state, not a message dump.

## Human Setup Boundary

The only required owner-side action is to create or grant a Discord server with
the agreed channels and roles.

After that, the factory should be able to continue through:

- server mapping;
- channel mapping;
- role mapping;
- bot or webhook configuration;
- read-only projection;
- structured approval registration;
- health checks;
- negative tests.

The factory must block instead of improvising if the server, channel, role, or
runtime registration path is missing.
