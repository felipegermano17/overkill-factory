# Product Face Proof Runner

Product Face is the proof that the product has a usable face, not only a
backend or architecture.

## When It Runs

Run for any vFinal card with Product Experience surfaces, including:

- web/app UI: `ux`, `frontend`, `web_app`, `website`, `screen`,
  `component`;
- device/app UI: `mobile`, `desktop`, `extension`, `browser-extension`;
- product interaction surfaces: `wallet-ui`, `ai_interface`,
  `agentic_interface`, `design_system`;
- product support surfaces: `docs`, `documentation`, `onboarding`;
- game-like surfaces: `game`, `gameplay`, `2d`, `3d`.

Legacy cards keep their existing narrower Product Face triggers unless they
explicitly set `product_face_result_required=true`.

## Surface Evidence Profiles

Product Face proof is surface-specific. A result must declare the profile it
proves, and completion validation compares that profile to the Product Face
Packet or Product Experience Plan.

- `web_visual_ui`: screenshots, viewports, important state matrix,
  empty/loading/error/success states when applicable, accessibility basics,
  visual overlap check, console status, copy sanity and performance note.
- `cli_tui`: golden path transcript, help output, install/run path, error-state
  transcript and cross-platform terminal evidence.
- `docs_onboarding`: first-success replay, tasks covered, stale-link check,
  public-safety check and reader success criteria.
- `agentic_interface`: task transcript, state transitions, approval boundaries,
  user control boundaries and recovery/error handling evidence.

The repo runner in `scripts/product_face_proof.py` is a `web_visual_ui` runner.
It should not be used to claim CLI/TUI, docs/onboarding or agentic-interface
PASS without the matching profile evidence.

Surface evidence is only the visible/product-face layer. Product completion
also consumes `templates/product-delivery-quality-profile.json` for
surface-specific domain proof. CLI/TUI products need install/run, help, golden
transcript, error-state and cross-platform shell proof. API/data products need
contract, auth, error, migration, fixture, retention and operational safety
proof. User-facing agentic products must be classified separately from internal
agent runtime infrastructure and carry task, control, permission, memory/data,
abuse and recovery proof.

## Surface Taxonomy

Product Experience OS routes surface families before Product Face PASS. The
taxonomy is separate from capability-pack activation: a pack may exist, but the
Product Face evidence profile still has to be supported or explicitly blocked.

Supported routes:

- `web`, `web_app`, `website`, `frontend`, `ux`, `screen`, `component`,
  `browser`, `mobile_web` and local web operator console/app surfaces route to
  `web_visual_ui`.
- `cli`, `tui`, `terminal`, `console` and `command_line` route to `cli_tui`.
- `docs`, `documentation`, `onboarding`, `quickstart` and `guide` route to
  `docs_onboarding`.
- `agentic_interface`, `ai_interface`, `chat_ui`, `assistant` and `copilot`
  route to `agentic_interface`.
- `wallet` and `wallet_ui` route to `web_visual_ui`, but still require the
  separate wallet transaction/signing domain proof before product acceptance.

Fail-closed routes:

- `mobile` is ambiguous. Use `mobile_web` for browser UI, or activate a native
  mobile evidence profile/pack first.
- `native_mobile`, `ios`, `android`, `desktop`, `desktop_app`, `extension`,
  `browser_extension`, `design_system`, `game`, `gameplay`, `2d` and `3d` are
  template-only or blocked until their dedicated evidence profile and pack are
  activated.

Unsupported or template-only surfaces must not fall back to `web_visual_ui`.
The validator reports the blocked reason instead of accepting generic Product
Face proof.

## Output

`product_face_result` with:

- surface evidence profile;
- screenshots;
- checked states;
- viewport list;
- checked user journeys;
- issues found;
- blocking findings;
- accessibility result;
- visual overlap result;
- performance note;
- packet comparison status;
- source-promise coverage status;
- design-fit review status;
- visual-quality verdict;
- evidence refs;
- next action.

The public schema is `schemas/product-face-result.schema.json`.

## Minimal Runner

Use the repo runner for static HTML or a local/public URL:

```bash
python scripts/product_face_proof.py \
  --target examples/minimal-hermes-project \
  --out .tmp/product-face-result.json \
  --card examples/minimal-hermes-project/card.md \
  --force-fallback
```

Useful options:

- `--viewport desktop=1440x900 --viewport mobile=390x844`
- `--state loading --state error --state success` to declare states that must
  be proven before product acceptance.
- `--journey "open target" --journey "inspect mobile viewport"` to declare
  journeys that must be proven before product acceptance.
- `--driver templates/product-face-state-journey-driver.json` to execute named
  browser journeys, setup steps and assertions instead of merely declaring
  coverage.
- `--strict` to treat accessibility and overlap warnings as blocking.
- `--force-fallback` to register bounded static evidence without a browser.
- `--card` to bind the result to the exact factory card/slice that will later
  be reconciled by the Hermes `done` gate.
- `--packet-ref`, `--packet-comparison-basis`,
  `--source-promise-coverage-basis` and `--design-fit-review-basis` to record
  product approval alignment.
- `--visual-quality-status`, `--visual-quality-reviewer` and
  `--visual-quality-basis` to record the professional visual quality verdict.
- `--visual-quality-residual` only when the verdict is
  `PASS_WITH_RESIDUALS`. The value must be
  `ID|SEVERITY|OWNER|EXPIRES_AT|ACCEPTED_SCOPE|PROOF_REF[,PROOF_REF]|DESCRIPTION`.
  Only bounded `low` or `medium` residuals that do not block full acceptance
  are valid for a Product Face PASS.
- `--reference-quality-ref`, `--reference-quality-comparison-basis`,
  `--compared-reference-id`, `--reference-comparison-dimension` and
  `--reference-comparison-artifact` to record the material reference/design
  comparison used by the reviewer. The artifact may be a side-by-side capture,
  reference snapshot, design-system/component ref, comparison manifest or
  bounded equivalent.
- `--reusable-for-product` only after the three alignment fields above are
  recorded as `pass` and `visual_quality_result` is `PASS` or
  `PASS_WITH_RESIDUALS`.

With Python Playwright available, the runner captures screenshots, console
messages, DOM state, accessibility basics, overlap scan and a browser-local
performance note. Without Playwright, it writes a `WAIVED` result with
`blocking_findings=true`, static file metadata, and an explicit note that no
rendered screenshot, console, layout, accessibility tree or performance claim
was captured.

The repo runner can drive named product states and journeys when a
`product_face_state_journey_driver` is supplied with `--driver`. The driver is a
small public-safe contract, not a full E2E framework. It supports bounded
browser actions such as `goto`, `click`, `fill`, `wait_for_selector`,
`assert_visible`, `assert_text` and `screenshot`. The runner records a
`state_journey_driver` summary and a `driver_execution` record in the
`product_face_result`, then uses only successfully executed journeys/states to
populate `checked_states`, `user_journeys_checked`, `visual_artifacts` and
`usage_evidence_matrix`.

Without `--driver`, the runner still records requested states and journeys as
`declared_states` and `declared_journeys`, but only the actually captured
initial render/default browser journey can appear in executable proof fields.
If extra states or journeys are declared without a driver or separate proof
artifact, the result is `WAIVED`, not a reusable Product Face PASS.

Driver values must be public-safe. Do not put secrets, private screenshots,
absolute local paths, raw logs or generated proof history into the public repo.
Keep execution outputs under `.tmp`, a private evidence store or a release
artifact, and reference them through the result emitted by the runner.

For product-facing completion, Receipt Five must include `product_face_result`.
A Product Face Packet is planning; a Product Face Result is proof. Browser
screenshots, no console errors, no overflow, accessibility basics and state
coverage are necessary but insufficient. A reusable product approval also needs
packet comparison, source-promise coverage, design-fit review and
`visual_quality_result` recorded as acceptable by a reviewer empowered to block
visually unacceptable UI. Reference/design comparison cannot be prose-only:
`reference_quality_comparison` must bind the compared source ids to material
comparison artifacts or to a bounded sanitized comparison manifest.
`PASS_WITH_RESIDUALS` is not an informal approval note. Each residual must have
an id, severity, owner, expiry, accepted scope and proof refs. Any warning in
`usage_evidence_matrix` must point to one of those residual ids through
`accepted_residual_ref`, otherwise the result cannot be consumed as a Product
Face PASS. For final product completion, each residual also needs a
`completion_disposition`. `repair_required` and `blocked_with_owner` keep final
completion blocked. `accepted_by_human_gate` needs a public-safe
`human_gate_ref`; `out_of_scope_with_rationale` needs a public-safe rationale.
This lets Product Face record bounded review residuals without letting them
become permanent caveats in a completed product.

If a residual is `repair_required`, final completion also requires a
materialized `repair_loop`: public-safe route ref, Hermes Kanban runtime
authority, no local-state authority, registered nonhuman worker ids and
`fresh_product_face_required=true`. A repair note without a routed worker loop
is still only a blocker, not product completion.

Source binding and scope coverage are separate checks. A Product Face result can
point at the current authorized surface and still under-cover the active Product
SOT. When active Product SOT scope exists, final completion requires
`scope_coverage_matrix` entries for each approved SOT requirement. `covered`
items need public-safe evidence refs. `partial` and `blocked` items fail final
completion. `deferred_by_sot` and `out_of_scope_by_sot` require a public-safe
SOT deferral or human-gate ref.

Source authority is explicit. Final completion must bind the compared candidate
surface to the active Product SOT and source-resolution packet through
`source_authority_binding`. `reference_only`, `superseded`, `unrelated` and
`rejected_stale_surface` candidates fail closed unless they are promoted by the
SOT with a public-safe promotion ref.

`templates/professional-design-process.json` is a starter contract. Its gates
are intentionally `PENDING`; copying that template into a card is not
professional design approval. Product-specific implementation can proceed only
after the card's Professional Design Process gates are `PASS`, or it remains on
the controlled blocker path named by the gate.

Reusable product example:

```bash
python scripts/product_face_proof.py \
  --target http://127.0.0.1:3000 \
  --out .tmp/product-face-result.json \
  --card examples/minimal-hermes-project/card.md \
  --viewport desktop=1440x900 \
  --viewport mobile=390x844 \
  --state initial-render \
  --journey "open target" \
  --driver templates/product-face-state-journey-driver.json \
  --packet-ref examples/minimal-hermes-project/card.md#product_face_packet \
  --packet-comparison-basis "Screens, states and viewports match the Product Face Packet." \
  --source-promise-coverage-basis "The checked journey covers the stated product promise." \
  --design-fit-review-basis "The reviewer confirmed fit to the requested product direction." \
  --professional-design-process-ref examples/minimal-hermes-project/card.md#professional_design_process \
  --professional-design-process-comparison-basis "The checked surface satisfies the professional design process." \
  --reference-quality-ref examples/minimal-hermes-project/card.md#professional_design_process.reference_research \
  --reference-quality-comparison-basis "The reviewer compared the surface against selected professional references." \
  --compared-reference-id 21st-dev-components \
  --compared-reference-id mobbin-workflow-patterns \
  --compared-reference-id pageflows-review-approval \
  --reference-comparison-dimension layout_hierarchy="Hierarchy matches the selected reference patterns." \
  --reference-comparison-dimension interaction_model="Interactions match the selected reference patterns." \
  --reference-comparison-dimension state_coverage="States match the selected reference patterns." \
  --reference-comparison-dimension visual_language="Visual language matches the selected reference patterns." \
  --reference-comparison-dimension density_spacing="Density and spacing match the selected reference patterns." \
  --reference-comparison-artifact side_by_side_capture=external:product-face-reference-comparison \
  --visual-quality-status PASS \
  --visual-quality-reviewer product-face-reviewer \
  --visual-quality-basis "The UI meets the product-specific quality bar and does not show AI-generic symptoms." \
  --reusable-for-product \
  --product-id qvg-public-validation-product \
  --environment-class production-like-static-artifact \
  --approval-scope "Product Face lane for the QVG public validation product only"
```

## Local Runner

Use:

```bash
python scripts/product_face_proof.py \
  --target http://127.0.0.1:3000 \
  --out .tmp/product-face-result.json \
  --card examples/minimal-hermes-project/card.md \
  --strict
```

If Python Playwright and its browser are available, the runner captures rendered
evidence. If they are not available, it writes a bounded `WAIVED` result with
`blocking_findings=true`.

That fallback is intentional. Static HTML metadata is not visual proof. It is a
receipt that the Product Face worker tried to run and that the card must remain
blocked until real browser evidence exists.

Synthetic Product Face evidence is also bounded. It may support fixtures,
smoke checks or validation cards only when `reusable_for_product=false` and the
result carries a `product_acceptance_boundary` stating that it cannot satisfy
product acceptance. Product-facing completion needs real Product Face proof.

## Current Boundary

The repository documents the runner contract. Actual screenshots, state
matrices and proof outputs should be generated for the current product and kept
under `.tmp`, a private evidence store or a release artifact, not committed as
old proof.

Full Product Face PASS requires:

- desktop screenshot;
- mobile screenshot;
- console check;
- important UI-state coverage;
- usage evidence matrix tying journey, state, viewport, data condition,
  accessibility status, performance status and evidence refs together;
- accessibility basics;
- overlap/layout check;
- performance note;
- packet comparison;
- source-promise coverage;
- design-fit review;
- visual-quality verdict distinct from mechanical proof;
- evidence refs attached to Receipt Five.

A mechanically passing UI must still block when it shows clear AI-generic
symptoms: generic dashboard composition, excessive explanatory copy, weak
hierarchy, synthetic visual language, audience mismatch, or controls/states that
pass a checklist but fail a serious product/design review.

## Why This Is Better

A Product Face Packet says what should exist. Product Face proof shows what
actually rendered. Agents often complete backend or component work while the
user-facing product is broken, missing states or unusable on mobile.
