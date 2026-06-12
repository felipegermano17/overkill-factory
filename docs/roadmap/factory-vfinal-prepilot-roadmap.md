# Factory vFinal Prepilot Roadmap

> Document status: ACTIVE BACKLOG.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This is not a runtime gate; backlog items become binding only after they are implemented as schema, script, test, worker, adapter rule or receipt.

This roadmap is not the canonical factory document.

It is the public operational backlog for the prepilot line: what is already
ready, what is deliberately kept out of the canonical document, and what must be
proved again before a real product paper starts.

## Source Of Truth

Use these artifacts as the current prepilot truth:

- `validation/prepilot/master-task-readiness.json`
- `validation/factory-production-readiness/current-readiness.json`
- `validation/canonical-stage-coverage/canonical-stage-implementation-coverage.json`
- `docs/agents/factory-stage-agent-map.md`
- `agents/worker-roster.md`
- `agents/worker-permission-classes.public.json`
- `validation/battery/factory-battery-results.json`

The canonical narrative stays clean. Doubts, future work, reference studies and
implementation notes belong here, in validation receipts, or in research docs.

## Prepilot Status

| Area | Status | What This Means |
| --- | --- | --- |
| Master task list | Ready | The 9 agreed prepilot tasks are now tracked by `validation/prepilot/master-task-readiness.json`. |
| Canonical stage coverage | Ready | The 32 canonical stages are mapped to schemas, scripts, tests, worker profiles or validation artifacts. |
| Agent classification | Ready | Core workers, optional packs, bridge roles and permission classes are separated in public artifacts. |
| GERENTE and Discord | Ready with private proof | The GERENTE is a gateway/interface profile, not a worker executor. Raw Discord/runtime evidence stays private. |
| Discord Control Tower Bridge | Ready with private proof | The bridge has registry, binding, schema, tests and public-safe production readiness receipt. |
| Provider/model/auth | Ready with live-proof boundary | Current public-safe receipts show canonical provider/model and auth presence; rerun after model/profile changes. |
| Public repo alignment | Ready | Open-source docs, examples, schemas, tests and receipts are aligned enough for a first real pilot. |
| Permissions | Ready | Worker permission classes separate interface, bridge, builders, reviewers, security, release and human record. |
| Reference agent/skill study | Ready for this pass | The study resulted in contracts and profile changes. Future agent additions must use eval and permission gates. |
| Prepilot battery | Ready | The battery passes locally and is included in the readiness chain. |

## Backlog That Must Not Pollute The Canonical Document

Keep these outside the canonical document until they become proven factory
contracts:

- richer Discord cockpit UX after real operator use;
- more product-type capability packs, especially mobile, desktop, game, data,
  browser extension and regulated-product packs;
- additional specialist workers only after an agent eval plan, permission class,
  profile binding and reviewer separation exist;
- real pilot learnings from the first product paper;
- model/provider drift notes after future profile changes;
- optional hosted front end or game-like cockpit work;
- new reference-repo findings that have not yet become contracts or tests.

## Before Starting A Real Pilot

Run the public checks:

```bash
python scripts/factory_battery.py
python scripts/factory_production_readiness.py
python scripts/validate_worker_profiles.py
python scripts/validate_public_json_artifacts.py
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
python -m unittest discover -s tests -p "test*.py" -q
```

Then rerun any private runtime checks that can drift:

- Hermes profile/provider/model probe;
- Discord gateway health;
- Control Tower bridge health;
- runtime approval registration path;
- real access readiness for the pilot product.

## Pilot Entry Rule

A real product paper can start only when:

1. the owner supplies the paper or brief;
2. required access is either granted or explicitly blocked before execution;
3. Hermes is treated as the source of truth;
4. Discord is used as the cockpit, not as the durable evidence store;
5. the first card produces Product SOT, Method Contract, Spec Graph, Loop Plan
   and Autonomy Readiness before material execution.

## How To Add New Agents Or Packs

Do not copy another project's agent soul directly.

For each new worker or pack:

1. state the product area it covers;
2. define what it receives and what it returns;
3. assign a permission class;
4. define reviewer separation;
5. add an eval plan and expected evidence;
6. add profile binding only after the contract is stable;
7. prove it with a public-safe test or validation receipt.

If those steps are not possible yet, keep the idea in this roadmap instead of
promoting it into the canonical factory.
