# Reference

This page collects the short-form facts a reader normally needs after the manual. It does not replace registries or the generated reference. It translates the most important names for someone operating or evaluating the factory.

## Where things live

- `README.md` and `README.pt-BR.md`: short public entrypoints.
- `docs/en/` and `docs/pt-BR/`: canonical public manual.
- `docs/factory-workflow.catalog.json`: compiled public workflow.
- `docs/promise-implementation-map.public.json`: public promise-to-implementation map.
- `docs/public-surface.manifest.json`: public surface manifest.
- `factory/scripts/factoryctl.py`: main command surface.
- `factory/schemas/`: JSON contracts for valid records.
- `factory/templates/`: base contracts, examples, and registries.
- `factory/agents/`: workers, profiles, Hermes bindings, capability packs, and readiness.
- `factory/tests/`: behavior regression coverage.
- `factory/legacy-docs/`: old docs preserved as technical reference; not the canonical public manual.
- `factory/legacy-docs/generated/`: generated kernel reference for maintainers.

## Short mental path

```text
source
-> understanding
-> Product SOT
-> method
-> packs and gates
-> work units
-> Hermes
-> worker results
-> verification and review
-> Receipt Five
-> release, block, or learnback
```

If a run looks done but cannot point to that path, it is probably missing proof.

## Route classes

The fourteen route classes exist to stop the factory from treating every request the same way.

- `product_creation`: product creation; needs Product SOT, scope coverage, and ready gate.
- `feature_delivery`: feature or slice; needs method, acceptance criteria, and proof proportional to risk.
- `bug_repair`: bug work; needs reproduction or explicit reason, fix, and regression.
- `incident_response`: incident work; needs severity, mitigation, communication, and learnback.
- `brownfield_discovery` / `migration_execution`: brownfield, refactor, integration, or migration; needs baseline, contract, regression, and rollback.
- `release_promotion`: release work; needs production readiness, rollback, owner, and authority.
- `research_validation`: research; must become an operational decision, not just smart commentary.
- `docs_onboarding`: docs/onboarding; must prove reader utility or first success.
- `security_remediation`: security; needs architecture, scans, review, and residual-risk treatment.
- `ux_product_experience`: UX/Product Experience; needs Product Face, states, journeys, design, and review.
- `analytics_data`: analytics/data; needs metric contract, privacy, and quality proof.
- `agent_quality_change`: agent/skill/model; needs eval, profile readiness, and learnback.

## Main methods

The method changes how work is proven.

- Spec-first: useful when the risk is building the wrong thing.
- Test-first: useful when behavior must be locked by regression.
- Behavior-first: useful when journey and acceptance matter more than internals.
- Discovery-first: useful when the question is not mature yet.
- Security-first: required when threat, secret, key, production, onchain, or abuse matters.
- Design-first: required when visible experience is part of the product.
- Legacy-diagnosis: needed when an old system, unknown behavior, or migration exists.
- Incident-first: needed when the product is broken, at risk, or needs operational response.

## Capability packs

A capability pack answers: “do we have specialist coverage for this product type?”.

Core packs currently include web/SaaS, CLI/TUI, cloud-native, agent-runtime, Solana AI Kit, onboarding, and public docs. They still need normal gates, but the factory recognizes basic coverage.

Template packs include native mobile, desktop, games, AI/ML, fintech, regulated domain, data analytics, browser extensions, and hardware/IoT. They should not execute materially just because a card asked for them. They need activation, specialists, bindings, smoke, eval, and evidence.

## Product Face

Product Face proves the face of the product. It changes by surface:

- web visual: screenshots, viewports, states, console, accessibility basics, and overflow;
- CLI/TUI: transcript, help, install, errors, and terminal behavior;
- docs/onboarding: first-success replay, links, and reader criteria;
- agentic interface: user control, permissions, memory/data, recovery, and boundaries;
- wallet/onchain UI: visual proof plus signing, transaction, and key boundary.

Product Face Packet is planning. Product Face Result is proof.

## Workers and authority

A worker is not a prompt character. To be operable it needs four layers:

1. role in the public registry;
2. agent profile;
3. Hermes binding;
4. card-specific worker packet.

The worker executes inside received authority. It does not approve gates, invent evidence, touch production, handle keys, or change scope outside the contract.

Worker accountability is separate from worker identity. Repeated bad output, failures, rework, shallow artifacts, review failures, or repair loops are aggregated into a `worker_accountability_ledger`. That ledger is public-safe and only records sanitized evidence refs. Its routing consequences are deterministic: watch, mandatory independent review, demotion to review queue, or escalation for profile review. It does not mutate Hermes Kanban directly; the factory reducer consumes the consequence and Hermes remains the runtime state authority.

## Core terms

Product SOT is product truth.

Full Product SOT Scope Coverage shows that every important SOT promise is planned, blocked, out of scope, human-owned, or proven.

Method Contract connects route, method, gates, workers, and evidence.

Worker Packet is the bounded task sent to a worker.

Worker Result is the worker return with evidence.

Gate Report explains whether something can move, why it is blocked, and what unlocks it.

Receipt Five is the done receipt: request, change, evidence, review, and next state.

Human Gate is a material operator decision with a readable package.

Readback is real reading of the produced artifact.

No-idle is the guard against silent idle, not a second dispatcher.

Learnback is learning promoted with proof, not loose chat memory.

## Useful commands

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
python3 scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md
python3 scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python3 scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
python3 scripts/factoryctl.py build-worker-accountability-ledger .tmp/worker-accountability-events.json --out .tmp/worker-accountability-ledger.json
python3 scripts/factoryctl.py validate-worker-accountability-ledger .tmp/worker-accountability-ledger.json
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
```

## Public claim boundary

The public repository proves local kernel coherence. It does not prove that a private product was delivered. Real delivery needs a live Hermes runtime, current worker results, product-specific evidence, consumed review, and human approval when risk requires it.
