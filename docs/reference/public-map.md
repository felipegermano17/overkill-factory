# Public Map

This is the simple public map for Overkill Factory V3.

Use it to understand the repository quickly. It is not a runtime proof and not a
replacement for Hermes Kanban state.

## One Sentence

Overkill Factory is a method, gate and contract layer for Hermes-powered agentic
product work.

Hermes runs the factory floor. Overkill Factory defines the production method
and checks.

## The Five Layers

```text
1. Operator
   The human talks to the gerente.

2. Gerente
   The gerente is the single human bridge. It starts the run, reports progress
   and delivers human gates.

3. Hermes Kanban
   Hermes owns runtime state: boards, cards, dependencies, typed blocks,
   dispatch, workers, logs and task lifecycle.

4. Factory Kernel
   Overkill Factory owns method: phases, schemas, contracts, gates, audits,
   evidence rules, capability routing and release checks.

5. Workers
   Specialist agents execute bounded cards and return evidence-backed results.
```

## First Value Path

If you are new, do this first:

```bash
python scripts/factoryctl.py doctor
python scripts/factoryctl.py run minimal
python -m unittest discover -s tests -q
```

Expected result:

- doctor passes;
- a minimal factory card reaches the correct gate state;
- tests validate the public contracts.

## What To Read First

1. `README.md`
   What the project is.

2. `docs/getting-started/quickstart-hermes.md`
   How to run the first useful path.

3. `docs/concepts/operator-journey.md`
   What the operator experiences.

4. `docs/concepts/factory-flow.md`
   How work moves through the factory.

5. `docs/reference/factory-kernel-reference.md`
   Generated source of truth for schemas, templates and public contracts.

## What The Repo Contains

```text
agents/      public worker contracts and Hermes profile bindings
schemas/     JSON schemas for factory artifacts
templates/   public example contracts and policies
scripts/     validators, audits and factoryctl
docs/        public docs and generated references
tests/       executable regression guards
examples/    minimal cards and operator examples
```

## What The Repo Does Not Contain

- private run evidence;
- private prompts;
- local board links;
- secrets;
- raw product studies;
- live operator data;
- a replacement runtime for Hermes.

## Golden Rules

- Hermes-first.
- Kanban-first.
- No mini-Hermes.
- Factory code stays in method, gates, rules, processes, audits and contracts.
- Gerente and agent skills/configs/bindings must be current with the factory.
- Done requires evidence, readback and the right authority.

## V3 Readiness Bar

V3 is ready only when all of these are true:

1. runtime truth spine is valid;
2. canonical frontier/no-idle guard is valid;
3. gerente and agents pass freshness checks;
4. human gates are artifact-first;
5. Receipt Five blocks overclaim;
6. Product SOT, method and architecture gates are distinct;
7. security, release and Solana authority are explicit;
8. public GitHub surface is simple and first-value oriented;
9. Factory Perfect Run can be proven end to end.

Run the V3 guard:

```bash
python scripts/factory_v3_release_readiness_audit.py --out .tmp/factory-v3-release-readiness-audit.json --markdown .tmp/factory-v3-release-readiness-audit.md
```

## Visual Map

The older visual map is still a supporting artifact:

https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html

Use this page first. Use the visual map only after you understand the simple
five-layer model above.
