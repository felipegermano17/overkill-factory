# Promise To Implementation Audit

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `docs/promise-implementation-map.public.json`,
> `scripts/validate_promise_implementation_map.py`, schemas, tests and the
> runtime evidence named by each claim.
> Runtime boundary: This audit does not replace Hermes runtime evidence,
> worker results, Receipt Five, release receipts or human gate records.

This page closes the public promise gap: what Overkill Factory says it can do
must map to implementation, proof and a plain boundary.

Every public promise must map to implementation, proof and boundary. If a claim
cannot do that, either weaken the wording, add the missing implementation, add
the missing proof, or mark the capability as blocked/deferred.

## What Was Weak

The factory already had many real contracts, scripts and tests, but the
operator-facing explanation did not have one mechanical index tying promises to
proof. That made these gaps possible:

- release text could drift between English README, Portuguese README, tests and
  changelog;
- local validation could be accidentally read as live Hermes proof;
- broad phrases such as "autonomous", "complete production line" or "Solana
  route" could be stronger than the implementation if no boundary was nearby;
- Solana public wording could make Quasar look like the domain brain, even
  though `solana-ai-kit-core` is the intended brain and Quasar/Auditor are
  implementation or proof lanes;
- bridge docs could be mistaken for runtime ownership unless the inbox/hook
  boundary was repeated;
- self-improvement could sound like self-mutation unless the proposal/review
  gate was explicit.

## Contract

The canonical map is `docs/promise-implementation-map.public.json`.

For each claim it records:

| Field | Meaning |
| --- | --- |
| `claim_id` | Stable id for tests, release review and README changes. |
| `public_promise` | The reader-facing promise in bounded language. |
| `claim_level` | Whether proof is local, runtime integration, release, capability routing, bridge or bounded process proof. |
| `documentation_refs` | Public docs where the promise appears. |
| `implementation_refs` | Code, schemas, templates or registries that implement it. |
| `proof_refs` | Tests or validators that prove the implementation contract. |
| `boundary` | What the claim does not prove. |
| `boundary_refs` | Docs or contracts where the boundary is explained. |

The validator is:

```bash
python scripts/validate_promise_implementation_map.py
```

It checks schema shape, duplicate claims, required claim coverage, file refs,
proof refs and overclaim patterns. It also fails if a boundary does not plainly
state a limit.

## Current Claim Classes

| Class | Examples | What It Proves | What It Does Not Prove |
| --- | --- | --- | --- |
| Local contract proof | first run, human gate packet, Product Face contract | The public repo can validate the shape and local command path. | A live product was built or approved. |
| Runtime integration proof | Hermes runtime floor, no-idle watchdog | The adapter/proof path is implemented and test-covered. | The operator's current Hermes is healthy unless current runtime evidence is supplied. |
| Capability routing proof | modular packs, Solana AI Kit routing | The router selects packs/workers/proof requirements deterministically. | A missing pack is magically executable. |
| Operator bridge proof | Codex Bridge plugin and durable inbox | The bridge can forward operator context and decisions. | Codex becomes a worker, watcher, approver or source of truth. |
| Public release proof | release preflight and Factory v1 Completion Gate | The public kernel can be released when checks pass. | Product-specific production or mainnet readiness. |
| Bounded process proof | start conversation, fast autonomy, learnback | The factory has safe process rails. | Unlimited autonomous execution or self-mutation. |

## Solana Boundary

Solana AI Kit is the Solana domain brain; Quasar and Auditor are
implementation or proof lanes.

That means:

- `solana-ai-kit-core` must activate for Solana/onchain signals before
  execution;
- relevant worker packets must carry the Solana AI Kit provider and usage
  receipt requirement;
- Quasar-specific builders, QA and Auditor paths may be required for program
  implementation and proof;
- Solana AI Kit does not replace signer boundaries, remote proof, security
  review, Hermes gates, Receipt Five or human approval.

## How To Change A Public Promise

Before editing README, docs, release notes or a public visual surface:

1. Add or update the claim in `docs/promise-implementation-map.public.json`.
2. Point it to at least one documentation ref, implementation ref, proof ref
   and boundary ref.
3. If the claim has no implementation, do not ship it as a promise. Create an
   issue or describe it as deferred.
4. If the claim depends on live Hermes, say that public validation is not live
   runtime proof unless a current runtime evidence file is supplied.
5. Run:

```bash
python scripts/validate_promise_implementation_map.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_public_surface_sync.py
python -m unittest tests.test_promise_implementation_map tests.test_open_source_docs -q
```

## Done Standard

A public promise is acceptable only when:

- the claim exists in the promise map;
- all referenced files exist;
- at least one proof ref is a test or validator;
- the boundary is explicit and reader-facing;
- README and public docs point to the same current release state;
- public validation includes the promise map check.

No single chat answer, README sentence, dashboard status, worker packet or
visual map is proof by itself.
