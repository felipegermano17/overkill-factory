# Capability Packs

Capability packs answer one question before a paper becomes execution work:

```text
Do we have the right specialist coverage for this type of product?
```

The Factory must not pretend that one generic implementation agent can build
every kind of product well. A web app, a native mobile app, a game, a Solana
program, a fintech ledger and a hardware product need different proof, risk
controls and specialist executors.

## How It Works

Every Factory card may name its surfaces, such as `frontend`, `api`, `solana`,
`game`, `ios`, `payment` or `hardware`. `factoryctl` also infers effective
surfaces from public card routing text, such as outcome, scope, method
contracts and product/security packets. Worker packets expose this as
`input_contract.surface_router` with declared, inferred and effective surfaces
plus the matched route reasons. Use `responsive` or `mobile-web` for browser UI
that adapts to mobile screens. Use `ios`, `android`, `react-native`, `expo` or
`native-mobile` for native mobile work. The broad surface `mobile` is
intentionally ambiguous and must be refined before execution.

`scripts/factoryctl.py validate-card` checks those surfaces against
`agents/capability-packs.public.json`.

Reusable packs should also state their practical operator contract:

- input contract;
- output contract;
- local smoke path.

This keeps packs executable for external users instead of becoming broad labels.

The result is simple:

| Pack state | Meaning | Execution rule |
| --- | --- | --- |
| `core_ready` | The Factory already has enough workers, bindings and proof path for this area. | The card can continue to normal gates. |
| `pack_ready` | An optional pack has already been installed and proven. | The card can continue if the pack covers the surfaces. |
| `pack_template` | The Factory knows this area exists, but the executable specialists are not installed yet. | The card blocks until a `capability_pack_contract` activates the pack. |
| `blocked_until_installed` | The area is intentionally outside current execution coverage. | The card blocks until a dedicated pack is created and reviewed. |

## Ready Coverage

These packs are ready in the public Factory:

| Pack | Covers |
| --- | --- |
| `web-saas-core` | Web apps, SaaS, APIs, persistence, auth, integrations, tests, docs, release and monitoring. |
| `cli-tui-product-pack` | Executable CLI/TUI products with command contracts, terminal transcripts, help UX and package/release proof. |
| `cloud-native-core` | CI/CD, runtime, deploy wiring, cloud security, observability and rollback planning. |
| `agent-runtime-core` | Hermes, Factory adapter, profiles, skills, tools, memory, MCP and agentic workflow changes. |
| `solana-ai-kit-core` | Solana AI Kit-backed Solana/onchain work, wallet transactions, signer boundaries and onchain QA. |
| `operator-onboarding-pack` | Fresh install, first local smoke, Hermes adapter handoff and first walkthrough. |
| `public-docs-knowledge-pack` | Public-safe docs, examples, guides and repository navigation for external users. |

For Solana/onchain cards, `solana-ai-kit-core` is the domain-brain pack. The
Solana-sensitive planning, architecture, build, wallet, QA, integration and
security workers receive Solana AI Kit from the pinned provider ref in their
worker packet when declared or inferred Solana surfaces are present. A real
`PASS` result from those workers must record a Solana AI Kit usage receipt
before it can satisfy closure. Solana AI Kit guides the domain work; it does
not replace Hermes, Receipt Five, Factory gates, signer rules or human
approval.

Do not read `solana-quasar-*` worker ids as the official Solana brain. Those
ids name the Quasar implementation and proof lane when that lane applies.
Solana AI Kit remains the routing/domain brain above Quasar, Auditor, devnet,
remote proof and security gates.

## Template Packs

These packs are recognized but not executable by default:

| Pack | Why it blocks |
| --- | --- |
| `mobile-app-pack` | Native mobile needs device lifecycle, app-store rules, simulator/device proof and mobile QA. |
| `desktop-app-pack` | Desktop needs packaging, OS permissions, installers, updates and desktop runtime proof. |
| `game-product-pack` | Games need gameplay design, runtime loop, assets, playtests and performance budgets. |
| `ai-ml-product-pack` | AI/ML needs model/data contracts, evals, drift checks and safety proof. |
| `fintech-payments-pack` | Money movement needs ledger invariants, reconciliation, fraud/compliance and human gates. |
| `regulated-domain-pack` | Legal, medical, insurance and similar products need domain and jurisdiction boundaries. |
| `data-analytics-pack` | Analytics needs metric contracts, data quality, lineage and dashboard correctness. |
| `browser-extension-pack` | Extensions need Manifest V3, permission review, content-script safety and packaging proof. |
| `hardware-iot-pack` | Hardware and IoT need device, firmware, safety and physical recovery evidence. |

## Activation Contract

A template pack becomes executable only when the card includes a
`capability_pack_contract` with:

- the pack id;
- `ready` or `activated` status;
- `activated` lifecycle state;
- covered surfaces;
- specialist workers;
- profile binding refs for those workers;
- permission class;
- tool refs;
- local smoke path;
- eval path;
- activation evidence refs;
- smoke and eval evidence refs;
- structured proof ids required by the registry pack;
- missing capabilities, if any;
- an execution rule.

The template lives at `templates/capability-pack-contract.json`.
`templates/capability-pack-activation-example.json` shows a complete
non-core pack activation shape, but it is deliberately blocked until real
public-safe smoke and eval refs replace the placeholders.

`agents/capability-pack-activation-ledger.public.json` is the current activation
ledger for non-core packs. It states whether each specialized pack is
`activated`, `template_only` or `blocked_until_installed`, and names the smoke,
eval, profile-binding and structured-proof requirements that must exist before
material execution can use the pack. If the ledger does not mark a non-core
pack as activated, `factoryctl` requires a bounded human activation gate plus
activation scope/rationale in the `capability_pack_contract`.

Core packs can still require surface-specific proof through
`templates/product-delivery-quality-profile.json`. API/data surfaces must prove
contract, auth, error semantics, migrations, fixtures, retention and operational
data safety. CLI/TUI surfaces must prove command transcripts, help output,
error states, install/run and shell behavior. A user-facing agentic product must
be classified as `user_facing_agentic_product`; internal `agent-runtime-core`
readiness does not satisfy that product proof by itself.

## Activation Flow

1. Pick the exact surfaces. Do not use broad aliases when the product needs a
   native, device, regulated, onchain or domain-specific pack.
2. Copy the activation contract shape into the candidate card.
3. Replace every placeholder with public-safe refs to workers, bindings, tools,
   smoke and eval evidence.
4. Keep `missing_capabilities` non-empty and `lifecycle_state` below
   `activated` until smoke and eval evidence exist.
5. Mirror every `structured_proofs_required` id from the registry pack into the
   activation contract. Once activated, those proof ids become required
   delivery proof: readiness must cover or waive them, and Product Face/product
   completion must pass them before full acceptance.
6. Run `factoryctl validate-card`. Material execution may start only after the
   contract is activated, complete and every requested surface is covered.

## Important Boundary

Capability packs do not replace worker packets, reviewers or gates. They run
before execution to decide whether the Factory is allowed to route the work at
all.

When a pack is not ready, the right behavior is to block, create the missing
specialist pack, evaluate it, bind it to Hermes and only then continue.

This is what keeps the Factory modular without pretending it has infinite
specialist competence.
