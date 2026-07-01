# Technical model

This page explains the implementation model without pretending that every reader wants to live inside the codebase.

The short version: Hermes owns runtime state. Overkill Factory owns the production contracts around that state. The repository contains the scripts, schemas, templates, registries, tests, and public docs that make the contract checkable.

## Repository shape

The public repository has two important top-level areas:

- `docs/`: the public product manual and public catalogs.
- `factory/`: the implementation, including scripts, schemas, templates, agents, adapters, examples, fixtures, tests, skills, and legacy docs.

Old technical docs live under `factory/legacy-docs/`. They are preserved for history and compatibility, but they are not the canonical public explanation.

## The executable surface

`factoryctl` is the main command surface. It validates cards, builds gate reports, compiles the workflow, prints registries, prepares worker packets, and runs the local public proof path.

The docs should never outrun this executable surface. If the docs claim a capability, the claim should trace to code, schema, test, command output, or a current product decision.

## Runtime state

Hermes owns runtime state: Kanban cards, worker tasks, dependencies, transitions, comments, workspaces, blocked states, and done states. The factory should not recreate that state in prose or in a hidden sidecar.

The factory adds discipline around the runtime. It decides what artifacts are required, which gates apply, which worker profile should handle a task, what evidence must return, and what authority is forbidden.

## Contracts and schemas

The repository currently contains 244 JSON schemas and 156 JSON templates. That is the backbone of the system. The schemas define what valid records look like. The templates give examples or default contracts. The tests keep those contracts from drifting silently.

Important contract families include workflow plans, factory commands, run events, promotion packets, worker authority, Product SOT, method contracts, capability packs, gate reports, Receipt Five, human gates, and runtime proof records.

## Routes, methods, and operating systems

The route registry currently exposes 14 route classes. The method registry exposes 8 method engines. The operating-system registry exposes 17 operating-system areas.

Route classes answer "what kind of work is this?" Method engines answer "how should this kind of work be handled?" Operating-system areas answer "which part of the factory owns this capability?"

This gives the factory a way to adapt without becoming vague. It can handle product creation, bug repair, incidents, releases, security work, analytics, UX, migration, and agent quality changes without pretending they are the same job.

## Workers and profiles

The public registry currently lists 40 public workers. A worker name is not enough. A worker needs a profile, a binding, result expectations, skill refs, evidence policy, and authority limits.

That is why the repository includes worker registries, worker profiles, Hermes profile bindings, readiness ledgers, and validators. A worker should not be a character in a prompt. It should be an operable role with a contract.

## Generated reference

The full generated kernel reference is produced by `factory/scripts/generate_factory_reference_docs.py`. The generated output now lives under `factory/legacy-docs/generated/` because the public manual should stay readable. The generated file is still useful for maintainers and validators.

## Validation stack

The implementation is guarded by public JSON validators, public surface sync checks, promise-to-implementation checks, worker profile validation, public safety scans, secret safety scans, MkDocs strict build, and the Python test suite.

The current public docs are meant to be read by humans, but they are still tied to these checks. That is what keeps the manual from becoming a story detached from the product.

## How a request becomes state

The factory does not trust a request just because it arrived in a chat. First it records source. Then it turns that source into structured artifacts. Those artifacts decide the route, the method, the gates, and the worker packets. Only then should runtime execution begin.

That order is deliberate. If a worker starts from a vague instruction, the system has no stable way to decide whether the answer is right. If the request becomes state first, every later step can point back to the same source. The worker can be wrong, but the factory has something concrete to compare against.

## What should be generated and what should be written by people

Some material is better generated from code: full command catalogs, schema coverage, worker inventories, and large reference tables. Hand-writing those by memory is how documentation goes stale.

Other material should be written for humans: this manual, the operating model, the trust model, and the usage path. A new operator does not need a thousand-line generated reference as the first explanation. They need the story in plain language, then exact commands when they are ready.

The current repository keeps both layers. Generated material still exists for validation and maintainers. The public manual stays readable.

## What can fail

The technical model is strict because the failure modes are subtle. A path can exist but point to legacy documentation. A public manifest can name a file that was moved. A worker profile can look configured while its binding points at stale docs. A local proof can pass while live Hermes has not been checked. A public claim can be true for the kernel and false for a private product run.

The validators are there to catch those mismatches. They are not a replacement for judgment, but they remove a lot of easy ways to fool ourselves.

## How to change the factory safely

A safe change usually touches three layers at once: the human explanation, the executable contract, and the tests or validators. If you change docs only, you may improve communication but not behavior. If you change code only, the public surface may lie. If you change tests only, you may enforce an old model.

For public documentation work, the safest rule is simple: write from current code and command output, not from memory. Then run the validators. If the validators complain, treat that as a product signal, not as an annoyance.

## Hermes bindings and live profiles

A worker is operable only when four layers match: registry role, agent profile, Hermes binding, and card-specific worker packet. A profile name alone is not enough.

The binding defines skill refs, queue policy, result schema, receipt field, and evidence path policy. That prevents a nice prompt persona from being treated as a real worker without a runtime contract.

Readiness also has a boundary. An old smoke, a locally materialized profile, or a degraded ledger does not prove live execution. It says a configuration path exists. Real completion still needs a current worker result and evidence consumed by the gate.

## Phase engine and Kanban graph

The factory uses the phase engine to compute the current frontier from materialized artifacts. The phase declared on a card does not beat reality. If Product SOT, Method Contract, decision package, or readiness is missing, the later phase blocks.

In Hermes, this must become a native graph: cards, dependencies, typed blockers, and linked work units. The factory may reconcile and repair, but it should not maintain a hidden parallel list. Runtime should show operational truth.

## Operator interface

The operator interface is a projection. Telegram, Discord, cockpit, and CLI bridge can receive source, send status, and deliver decision packages. They do not replace Hermes, Receipt Five, or worker results.

The product rule is: the manager speaks to the human; workers and raw events feed internal state. A human gate needs a readable memo and the artifact under review, not a JSON dump or local path.

## Artifact readback and durable attachments

The Hermes integration should not accept “a file exists” as completion. For runtime artifacts and attachments, the factory needs readback: row or blob exists, size and hash match, parsing succeeded when applicable, safety checks passed, and the reference can be consumed later.

References such as `artifact_readback` and `kanban-attachment` live at that boundary. They prevent metadata, local paths, or temporary files from being treated as permanent proof.

## SDLC Feedback Loop

Material autonomous work needs to keep the thread between signal, triage, model/profile choice, execution, evidence, and learnback. That thread is the SDLC Feedback Loop.

Without it, a failure becomes chat memory; a model choice becomes implicit; learnback becomes opinion without a target. With it, the factory knows where the signal came from, why it chose a route, what proof returned, and what rule may change later.
