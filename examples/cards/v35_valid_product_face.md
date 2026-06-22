```json
{
  "card_id": "KFP-V35-POS-PF",
  "slice_id": "OVERKILL_FACTORY_V35_10",
  "owner_profile": "frontend-worker",
  "source_refs": ["Overkill Factory v3.5 agent-workforce methodology"],
  "source_state": "compiled",
  "outcome": "Positive gate test: Product Face card with required packet can pass ready gate.",
  "acceptance_criteria": ["promote dry-run passes", "completion without Receipt Five fails", "completion with Receipt Five passes"],
  "scope_in": ["gate validation only", "Receipt Five completion test"],
  "scope_out": ["code edit", "deploy", "secrets", "funds", "mainnet"],
  "target_repo_paths": ["docs/factory/factory-v35-10"],
  "conflict_set": ["V3.5 must require Product Face details and completion receipts."],
  "risk_class": "R1-dev-safe",
  "why_this_class": "Local blocked-card gate test only; no code, deploy, secrets, funds, custody or public surface.",
  "codex_mode": "advisory",
  "why_codex_mode": "Codex only observes and verifies the gate result.",
  "product_security_checks": ["Product Face Packet fields are present"],
  "code_security_checks": ["no code execution"],
  "system_security_checks": ["no infrastructure mutation"],
  "process_security_checks": ["Receipt Five and kanban_transition_event required before done"],
  "verify_commands": ["hermes kanban promote --dry-run <task_id>", "hermes kanban complete <task_id> --metadata <json>"],
  "evidence_expected": ["promotion accepted by V3.5 ready gate", "completion blocked without metadata", "completion accepted with Receipt Five"],
  "review": {
    "QA_required": false,
    "independent_review_required": false,
    "security_review_required": false,
    "cybersecurity_review_required": false,
    "CTO_gate_required": false,
    "human_gate_required": false
  },
  "factory_method_version": "OVERKILL_V3_5_FACTORY_10",
  "phase": "F5",
  "surfaces": ["ux", "frontend", "wallet-ui"],
  "risk_initial": "R2",
  "risk_effective": "R2",
  "authority_max": "validate_gate_only",
  "owner_worker": "Product Face Designer",
  "executor_identity": "frontend-worker",
  "reviewer_identity": "independent-reviewer",
  "reviewer_selection_plan": {
    "record_type": "reviewer_selection_plan",
    "changed_surfaces": ["ux", "frontend", "wallet-ui"],
    "risk_effective": "R2",
    "executor_identity": "frontend-worker",
    "forbidden_reviewers": ["frontend-worker"],
    "required_reviewers": ["independent-reviewer", "appsec-owasp-specialist"],
    "reviewer_matrix": [
      {
        "reviewer_worker": "independent-reviewer",
        "covers": ["ux", "frontend", "evidence"],
        "reason": "The executor cannot review its own Product Face evidence.",
        "mandatory": true
      },
      {
        "reviewer_worker": "appsec-owasp-specialist",
        "covers": ["wallet-ui", "frontend"],
        "reason": "Wallet-like UI states need AppSec-oriented review even in gate tests.",
        "mandatory": true
      }
    ],
    "selection_rule": "Route review from changed surfaces and exclude the executor.",
    "evidence_refs": ["Overkill Factory v3.5 agent-workforce methodology"]
  },
  "runtime_decision": "hermes_default",
  "runtime_contract": {"mode": "read_only_gate_test"},
  "security_contract": {"security_boundary": "no_sensitive_action"},
  "forbidden_actions": ["code_edit", "deploy", "secret_access", "wallet_signing"],
  "done_definition": "Gate validates Product Face and completion requires Receipt Five.",
  "transition_event_required": true,
  "kanban_transition_event_ref": "required_before_ready",
  "security_scan_packet": {
    "security_owner": "security-orchestrator",
    "scanner_agent": "codex-security",
    "scan_timing": "before_done",
    "scan_scope": ["frontend", "wallet-ui", "AppSec checklist"],
    "required_tools": ["codex-security", "appsec-owasp-specialist"],
    "acceptance_policy": {"blocking_findings": "must_fix_or_human_waiver"}
  },
  "product_experience_plan": {
    "$schema": "https://overkill-factory.dev/schemas/product-experience-plan.schema.json",
    "surface_type": "web app",
    "surface_pack": "web-app-surface-pack",
    "product_delivery_quality_profile_ref": "templates/product-delivery-quality-profile.json",
    "project_design_system_ref": "examples/cards/v35_valid_product_face.md#project_design_system",
    "surface_evidence_profile": "web_visual_ui",
    "experience_sot": "The operator can review pilot status, evidence, blockers and next action without generic dashboard filler.",
    "user": "factory operator",
    "job_to_be_done": "Review pilot status and evidence with clear next action.",
    "main_flows": ["pilot status review", "review evidence inspection"],
    "required_states": ["loading", "error", "success", "pending"],
    "design_direction": {
      "visual_tone": "focused operational validation surface",
      "product_fit": "Status, evidence and review hierarchy must be visible before decorative content.",
      "density": "compact enough for repeated operator review",
      "interaction_style": "direct inspection with explicit blockers and next action"
    },
    "visual_quality_bar": {
      "reference_quality_bar": "A focused operator validation surface with clear status, evidence and review hierarchy.",
      "anti_generic_criteria": [
        "no generic AI dashboard composition",
        "no excessive explanatory copy",
        "no weak hierarchy between status, evidence and next action"
      ],
      "professional_review_required": true,
      "block_when": [
        "screenshots pass mechanically but the surface looks templated or product-agnostic",
        "visual hierarchy does not match the Product Face job"
      ]
    },
    "proof_required": ["desktop screenshot", "mobile screenshot", "state evidence", "visual_quality_result verdict"],
    "reviewers_required": ["product-face", "qa-verification-worker", "independent-reviewer"],
    "done_definition": [
      "Product Face Packet exists before implementation",
      "states are checked against the plan",
      "visual_quality_result is PASS or PASS_WITH_RESIDUALS with reviewer basis"
    ],
    "human_gate": {
      "required": false,
      "approver": "",
      "reason": "No material external visual direction decision in this fixture."
    },
    "prototype_decision": "prototype_not_required because this is a validation fixture",
    "device_or_viewport_scope": ["desktop 1440x900", "mobile 390x844"],
    "accessibility_scope": ["keyboard", "focus", "contrast", "labels"],
    "performance_scope": ["static validation render only"],
    "data_context": "Fixture evidence includes loading, error, success and pending status data.",
    "docs_onboarding": ["operator can read status without private context"],
    "experience_qa": ["responsive proof", "state coverage", "a11y basics"],
    "product_face_result_required": true,
    "evidence_refs": ["examples/cards/v35_valid_product_face.md#product_experience_plan"],
    "reference_quality_waiver": {
      "owner": "product-face",
      "reason": "This public fixture validates Product Experience routing and Product Face Packet shape; it does not claim final visual reference research as production evidence."
    }
  },
  "project_design_system": {
    "$schema": "https://overkill-factory.dev/schemas/project-design-system.schema.json",
    "record_type": "project_design_system",
    "design_system_id": "v35-valid-product-face-design-system",
    "surface_scope": ["web_app", "operator_console", "product_surface"],
    "source_contracts": {
      "product_experience_plan_ref": "examples/cards/v35_valid_product_face.md#product_experience_plan",
      "product_face_packet_ref": "examples/cards/v35_valid_product_face.md#product_face_packet",
      "professional_design_process_ref": "examples/cards/v35_valid_product_face.md#professional_design_process",
      "reference_quality_packet_ref": "templates/reference-quality-packet.json"
    },
    "design_positioning": {
      "product_personality": "quiet, capable and specific to the product job",
      "audience_context": "operators and product users who need to scan state, evidence and next action quickly",
      "trust_posture": "state, consequence and source should be visible before decorative polish",
      "density_posture": "dense but readable product-tool layout for repeated use",
      "interaction_posture": "direct controls with clear hover, focus, disabled, loading and error feedback",
      "anti_generic_position": "reject generic AI-dashboard, marketing hero and decorative card compositions when the surface is operational"
    },
    "tokens": {
      "palette_policy": {
        "semantic_roles_required": true,
        "not_one_hue_theme": true,
        "dark_light_policy": "declare whether the product ships light, dark or both; do not improvise per screen"
      },
      "color_roles": [
        {
          "role": "surface",
          "token": "--color-surface",
          "value_hint": "neutral app background",
          "usage": "primary page and app-shell surface",
          "avoid": "using brand accent as full background"
        },
        {
          "role": "panel",
          "token": "--color-panel",
          "value_hint": "subtle raised surface",
          "usage": "tool panels, inspectors and grouped controls",
          "avoid": "nested decorative cards"
        },
        {
          "role": "text",
          "token": "--color-text",
          "value_hint": "high contrast foreground",
          "usage": "primary labels, data and headings",
          "avoid": "low-contrast muted body text"
        },
        {
          "role": "accent",
          "token": "--color-accent",
          "value_hint": "product-specific action color",
          "usage": "primary action and active state only",
          "avoid": "painting every control with the accent"
        },
        {
          "role": "danger",
          "token": "--color-danger",
          "value_hint": "destructive or irreversible risk",
          "usage": "destructive action, failure and risk states",
          "avoid": "using danger color for neutral warnings"
        },
        {
          "role": "warning",
          "token": "--color-warning",
          "value_hint": "attention without destructive meaning",
          "usage": "stale, pending or degraded states",
          "avoid": "hiding warnings behind neutral gray"
        },
        {
          "role": "success",
          "token": "--color-success",
          "value_hint": "verified or completed state",
          "usage": "pass, verified and complete states",
          "avoid": "success color before evidence exists"
        }
      ],
      "typography_roles": [
        {
          "role": "screen-title",
          "token": "--font-title",
          "usage": "compact screen title that names the surface",
          "constraints": "no hero-scale type inside product tools"
        },
        {
          "role": "section-label",
          "token": "--font-section",
          "usage": "small section labels and panel headings",
          "constraints": "must not wrap awkwardly in compact panels"
        },
        {
          "role": "body",
          "token": "--font-body",
          "usage": "primary readable content, rows and descriptions",
          "constraints": "line height must preserve scan speed"
        },
        {
          "role": "data",
          "token": "--font-data",
          "usage": "ids, timestamps, balances, counts and evidence refs",
          "constraints": "use tabular or monospace treatment only where it improves comparison"
        }
      ],
      "spacing_scale": ["4px", "8px", "12px", "16px", "24px", "32px"],
      "radius_scale": ["4px", "8px"],
      "elevation_scale": ["none", "subtle-border", "focused-overlay"]
    },
    "layout_contract": {
      "grid": "app-shell with command area, primary work region and contextual inspector when density requires it",
      "responsive_rules": [
        "mobile keeps the primary task first and moves inspector/detail below it",
        "desktop may use multi-column layout only when columns stay readable"
      ],
      "density_rules": [
        "operational surfaces should prefer compact rows, controls and inspectors",
        "marketing-scale sections are forbidden unless the card is explicitly a public landing page"
      ],
      "stable_dimensions": [
        "toolbars, icon buttons, counters and board/grid cells need stable dimensions",
        "dynamic status text must wrap or truncate without resizing core controls"
      ],
      "forbidden_layouts": [
        "card inside card composition",
        "decorative KPI blocks disconnected from product objects",
        "split hero text/media layout for app tools"
      ]
    },
    "component_contracts": [
      {
        "component_id": "command-bar",
        "purpose": "Expose primary commands, filters and mode switches close to the work surface.",
        "anatomy": ["primary command", "secondary icon controls", "filter or segmented mode"],
        "states": ["default", "hover", "focus", "disabled", "loading"],
        "interaction_rules": ["icons should be used for familiar tool actions with tooltip labels"],
        "accessibility_notes": ["controls require names and visible focus"],
        "implementation_notes": ["keep height stable across modes"]
      },
      {
        "component_id": "status-row",
        "purpose": "Show object state, source, freshness and next action in one scannable row.",
        "anatomy": ["state marker", "object label", "source/freshness", "next action"],
        "states": ["ready", "blocked", "stale", "error", "success"],
        "interaction_rules": ["row focus should reveal detail without losing list context"],
        "accessibility_notes": ["state cannot be color-only"],
        "implementation_notes": ["long labels must not shift action controls"]
      },
      {
        "component_id": "evidence-inspector",
        "purpose": "Show proof, gaps and review state for the selected object.",
        "anatomy": ["summary", "evidence refs", "blocking findings", "review state"],
        "states": ["empty", "loading", "populated", "blocked", "error"],
        "interaction_rules": ["evidence refs must be copyable or inspectable when safe"],
        "accessibility_notes": ["headings and regions must support keyboard navigation"],
        "implementation_notes": ["private evidence unavailable must be a real state, not an error-looking crash"]
      }
    ],
    "state_contract": {
      "required_states": ["empty", "loading", "success", "error", "blocked", "stale"],
      "feedback_rules": [
        "state changes must be visible in text and structure, not only color",
        "dangerous or irreversible actions must show consequence before execution"
      ],
      "empty_loading_error_rules": [
        "empty state names what is missing and the next safe action",
        "loading state preserves layout stability",
        "error state preserves orientation and offers a bounded recovery path"
      ],
      "risk_or_destructive_action_rules": [
        "risk actions need explicit label, consequence, disabled state and review path"
      ]
    },
    "implementation_contract": {
      "tailwind_or_css_variables": "both",
      "style_entrypoints": ["src/styles/tokens.css", "tailwind.config.ts", "DESIGN.md"],
      "component_entrypoints": ["src/components", "src/app"],
      "forbidden_shortcuts": [
        "inventing one-off colors outside the token contract",
        "using screenshots or private captures as committed design source",
        "treating component library defaults as product design approval"
      ]
    },
    "quality_bar": {
      "reference_refs": [
        "templates/reference-source-registry.json#refero-styles",
        "templates/reference-source-registry.json#21st-dev",
        "templates/reference-source-registry.json#mobbin"
      ],
      "do_rules": [
        "translate references into original tokens and components",
        "explain why density, state and layout match the product job",
        "keep product controls close to the data or state they affect"
      ],
      "dont_rules": [
        "copy protected layouts, assets or product-specific text",
        "ship generic dashboard polish as Product Face quality",
        "hide blockers, stale data or missing evidence behind positive styling"
      ],
      "review_checklist": [
        "tokens are named and mapped to implementation",
        "components include required states and accessibility notes",
        "layout rules cover mobile and desktop",
        "Product Face proof can compare screenshots against this contract"
      ]
    },
    "proof_contract": {
      "consumed_by": ["frontend-builder", "product-face", "qa-verification-worker"],
      "must_be_compared_in_product_face_result": true,
      "screenshot_and_state_requirements": [
        "screenshots must show states named by this contract",
        "review must compare visible tokens/components/layout against this contract"
      ],
      "product_face_result_must_include": [
        "project_design_system_ref",
        "project_design_system_comparison.status=pass"
      ]
    },
    "design_md_export": {
      "required": true,
      "path": "DESIGN.md",
      "must_match_contract": true,
      "audience": "AI coding agents, frontend implementers and Product Face reviewers"
    },
    "public_private_boundary": {
      "public_safe_refs_only": true,
      "raw_private_evidence_embedded": false,
      "no_private_screenshots_in_repo": true
    },
    "human_gate": {
      "required": false,
      "approver": "",
      "reason": "A human gate is required only when the design system changes the product promise, brand direction or risk messaging."
    }
  },
  "product_face_packet": {
    "$schema": "https://overkill-factory.dev/schemas/product-face-packet.schema.json",
    "surface": "web_app",
    "mode": "greenfield",
    "product_delivery_quality_profile_ref": "templates/product-delivery-quality-profile.json",
    "project_design_system_ref": "examples/cards/v35_valid_product_face.md#project_design_system",
    "surface_evidence_profile": "web_visual_ui",
    "user": "factory operator",
    "job_to_be_done": "Review pilot status and evidence with clear next action.",
    "main_flows": ["pilot status review", "review evidence inspection"],
    "required_states": ["loading", "error", "success", "pending"],
    "design_direction": {
      "visual_tone": "focused operational validation surface",
      "product_fit": "Status, evidence and review hierarchy must be visible before decorative content.",
      "density": "compact enough for repeated operator review",
      "interaction_style": "direct inspection with explicit blockers and next action"
    },
    "screen_inventory": ["pilot status screen", "review evidence screen"],
    "state_matrix": {"loading": "shown", "error": "shown", "success": "shown", "pending": "shown"},
    "design_contract_ref": "design_contract_candidate_v1",
    "mobile_breakpoints": ["375", "768", "1440"],
    "wallet_flow_matrix": {"sign": "not_applicable_docs_only", "reject": "not_applicable_docs_only"},
    "a11y_acceptance": ["keyboard", "focus", "contrast", "labels"],
    "performance_budget": {"bundle": "not_applicable_docs_only", "render": "not_applicable_docs_only"},
    "visual_quality_bar": {
      "reference_quality_bar": "A focused operator validation surface with clear status, evidence and review hierarchy.",
      "anti_generic_criteria": [
        "no generic AI dashboard composition",
        "no excessive explanatory copy",
        "no weak hierarchy between status, evidence and next action"
      ],
      "professional_review_required": true,
      "block_when": [
        "screenshots pass mechanically but the surface looks templated or product-agnostic",
        "visual hierarchy does not match the Product Face job"
      ]
    },
    "visual_evidence_plan": ["desktop screenshot", "mobile screenshot"],
    "proof_required": ["desktop screenshot", "mobile screenshot", "state evidence", "visual_quality_result verdict"],
    "reviewers_required": ["product-face", "qa-verification-worker", "independent-reviewer"],
    "done_definition": [
      "result covers required flows and states",
      "result includes evidence for required viewports",
      "review confirms result fits the product promise and visual direction",
      "visual_quality_result is PASS or PASS_WITH_RESIDUALS with reviewer basis"
    ],
    "human_gate": {
      "required": false,
      "approver": "",
      "reason": "No material external visual direction decision in this fixture."
    }
  },
  "professional_design_process": {
    "$schema": "https://overkill-factory.dev/schemas/professional-design-process.schema.json",
    "record_type": "professional_design_process",
    "surface_type": "operator validation surface",
    "mode": "greenfield",
    "design_brief": {
      "user": "factory operator",
      "job_to_be_done": "Review pilot status and evidence with clear next action.",
      "decision_surface": "Pilot status and review evidence screens.",
      "success_signal": "State, evidence and review outcome are visible without generic dashboard filler.",
      "failure_risks": [
        "The UI looks like a generated dashboard.",
        "Review evidence and status hierarchy are unclear."
      ]
    },
    "task_map": [
      {
        "task_id": "T1",
        "user_goal": "Read pilot status.",
        "trigger": "Operator opens the status screen.",
        "success_signal": "Status and evidence are visible.",
        "failure_state": "Status is hidden behind decorative metrics."
      },
      {
        "task_id": "T2",
        "user_goal": "Inspect review evidence.",
        "trigger": "Operator opens evidence screen.",
        "success_signal": "Evidence refs and review state are clear.",
        "failure_state": "Evidence is ambiguous or missing."
      },
      {
        "task_id": "T3",
        "user_goal": "Confirm visual quality.",
        "trigger": "Product Face review runs.",
        "success_signal": "Reviewer compares result to reference quality bar.",
        "failure_state": "Mechanical screenshot proof hides generic visual quality."
      }
    ],
    "reference_research": {
      "registry_refs": [
        "templates/reference-source-registry.json#21st-dev",
        "templates/reference-source-registry.json#refero-styles",
        "templates/reference-source-registry.json#mobbin",
        "templates/reference-source-registry.json#pageflows"
      ],
      "selection_rationale": "Search professional component libraries, product-flow libraries and public product references before implementation; select and reject candidates explicitly, synthesize reusable patterns, and copy no code, text, screenshots or assets without license review.",
      "sources": [
        {
          "source_id": "radix-ui-themes",
          "source_url_or_ref": "https://www.radix-ui.com/themes",
          "use_type": "accessibility-reference",
          "what_to_learn": [
            "semantic tokens",
            "accessible controls"
          ],
          "extracted_patterns": [
            "Use state semantics over decoration.",
            "Keep controls compact and named."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "source_type": "design_system",
          "library_source": "Radix Themes",
          "candidate_reason": "Selected for accessibility, semantic token and component density discipline.",
          "selected_patterns": [
            "Semantic color roles must drive product states instead of decorative palettes.",
            "Composable, named controls should replace oversized explanatory blocks."
          ],
          "visual_dimensions_covered": [
            "visual_language",
            "density_spacing",
            "interaction_model"
          ],
          "public_safety_notes": "Reference only; no code, text or assets copied."
        },
        {
          "source_id": "shadcn-data-table",
          "source_url_or_ref": "https://ui.shadcn.com/docs/components/data-table",
          "use_type": "dense-data-reference",
          "what_to_learn": [
            "row scanning",
            "filters"
          ],
          "extracted_patterns": [
            "Dense lists need stable row focus.",
            "Controls should stay near affected data."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "source_type": "component_registry",
          "library_source": "shadcn/ui",
          "candidate_reason": "Selected for dense data-table ergonomics, filtering, sorting and row action patterns.",
          "selected_patterns": [
            "Dense operational data needs search, filters, sort and visible row focus.",
            "Controls belong close to the data or state they affect."
          ],
          "visual_dimensions_covered": [
            "layout_hierarchy",
            "interaction_model",
            "density_spacing"
          ],
          "public_safety_notes": "Reference only; no code, text or assets copied."
        },
        {
          "source_id": "linear-product-workflow",
          "source_url_or_ref": "https://linear.app",
          "use_type": "workflow-reference",
          "what_to_learn": [
            "state-first workflow",
            "quiet product-tool hierarchy"
          ],
          "extracted_patterns": [
            "Work context should be visible without a hero.",
            "Status hierarchy should be compact and scannable."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "source_type": "product_reference",
          "library_source": "Linear public product reference",
          "candidate_reason": "Selected for compact work management hierarchy, state clarity and low-friction navigation.",
          "selected_patterns": [
            "Operational product tools should be compact, scannable and state-first.",
            "Primary work context should be visible without a marketing-style hero."
          ],
          "visual_dimensions_covered": [
            "layout_hierarchy",
            "state_coverage",
            "density_spacing"
          ],
          "public_safety_notes": "Reference only; no code, text or assets copied."
        },
        {
          "source_id": "21st-dev-components",
          "source_url_or_ref": "https://21st.dev/",
          "source_type": "component_registry",
          "library_source": "21st.dev",
          "use_type": "component-library-and-craft-benchmark",
          "candidate_reason": "Selected to compare component polish, hierarchy, spacing and interaction finish against modern React/Tailwind component references.",
          "what_to_learn": [
            "How modern component libraries compose dense command surfaces without looking generic.",
            "How spacing, state affordances and micro-interactions make controls feel deliberate."
          ],
          "extracted_patterns": [
            "Reusable components need explicit state, focus, hover and disabled behavior before visual approval.",
            "Component density should be tuned to the operator task instead of stretched into marketing cards."
          ],
          "selected_patterns": [
            "Require explicit states for controls and rows before Product Face PASS.",
            "Use compact component groups with clear hierarchy instead of decorative dashboard blocks."
          ],
          "visual_dimensions_covered": [
            "interaction_model",
            "visual_language",
            "density_spacing"
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "public_safety_notes": "Reference only; no source code, text or assets copied."
        },
        {
          "source_id": "mobbin-workflow-patterns",
          "source_url_or_ref": "https://mobbin.com/",
          "source_type": "user_flow_library",
          "library_source": "Mobbin",
          "use_type": "real-product-flow-and-screen-benchmark",
          "candidate_reason": "Selected because real product flows expose navigation, density and state decisions that isolated mockups hide.",
          "what_to_learn": [
            "How professional products sequence navigation, detail inspection and recovery states.",
            "How repeated-use workflows avoid decorative elements that slow scanning."
          ],
          "extracted_patterns": [
            "A serious workflow needs visible current state, selected object, next action and recovery path.",
            "Reference study must cover multiple screens or states, not a single attractive screenshot."
          ],
          "selected_patterns": [
            "Require current object, state and next action to be visible together.",
            "Reject single-screen inspiration that does not explain workflow behavior."
          ],
          "visual_dimensions_covered": [
            "layout_hierarchy",
            "interaction_model",
            "state_coverage"
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "public_safety_notes": "Use synthesized observations only; do not commit screenshots or private captures."
        },
        {
          "source_id": "pageflows-review-approval",
          "source_url_or_ref": "https://pageflows.com/",
          "source_type": "user_flow_library",
          "library_source": "Page Flows",
          "use_type": "journey-state-and-approval-flow-benchmark",
          "candidate_reason": "Selected to force journey-level coverage for approval, error, review and onboarding states.",
          "what_to_learn": [
            "How professional products communicate progress, blocking states and fallback paths across a journey.",
            "How approval and review flows preserve confidence without hiding consequences."
          ],
          "extracted_patterns": [
            "Approval surfaces need consequence, evidence and rollback context before the action.",
            "Error and blocked states should preserve orientation and show the next safe action."
          ],
          "selected_patterns": [
            "Require consequence, evidence and fallback context for approval surfaces.",
            "Treat blocked/error states as first-class Product Face screenshots."
          ],
          "visual_dimensions_covered": [
            "interaction_model",
            "state_coverage",
            "layout_hierarchy"
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "public_safety_notes": "Use journey-level learning only; no copied videos, screenshots or private material."
        }
      ],
      "library_searches": [
        {
          "library": "21st.dev",
          "library_url": "https://21st.dev/",
          "query_or_category": "operations dashboard, command surface, data table and review components",
          "searched_at": "2026-06-14",
          "selection_criteria": [
            "component craft supports dense repeated operator use",
            "states and controls can be adapted without copying code or assets"
          ],
          "candidate_count": 6,
          "selected_source_ids": [
            "21st-dev-components",
            "shadcn-data-table"
          ],
          "rejected_candidate_ids": [
            "decorative-dashboard-template",
            "oversized-hero-block"
          ]
        },
        {
          "library": "Mobbin",
          "library_url": "https://mobbin.com/",
          "query_or_category": "workflow, status, review, incident and project operations flows",
          "searched_at": "2026-06-14",
          "selection_criteria": [
            "real product flow exposes navigation and state transitions",
            "patterns improve operator speed instead of presentation aesthetics"
          ],
          "candidate_count": 6,
          "selected_source_ids": [
            "mobbin-workflow-patterns",
            "linear-product-workflow"
          ],
          "rejected_candidate_ids": [
            "marketing-dashboard-gallery",
            "single-screenshot-flow"
          ]
        },
        {
          "library": "Page Flows",
          "library_url": "https://pageflows.com/",
          "query_or_category": "approval, review, onboarding, error and blocked-state journeys",
          "searched_at": "2026-06-14",
          "selection_criteria": [
            "journey shows consequences and recovery states",
            "flow can be compared dimension-by-dimension against the product task model"
          ],
          "candidate_count": 5,
          "selected_source_ids": [
            "pageflows-review-approval"
          ],
          "rejected_candidate_ids": [
            "happy-path-only-flow"
          ]
        }
      ],
      "rejected_references": [
        {
          "source_id": "decorative-dashboard-template",
          "source_url_or_ref": "external:generic-dashboard-gallery",
          "rejection_reason": "Rejected because decorative metrics and large cards do not prove gate, evidence or next-action clarity."
        },
        {
          "source_id": "oversized-hero-block",
          "source_url_or_ref": "external:oversized-hero-block",
          "rejection_reason": "Rejected because hero-style presentation blocks are not suitable for dense product-operation surfaces."
        },
        {
          "source_id": "marketing-dashboard-gallery",
          "source_url_or_ref": "external:marketing-dashboard-gallery",
          "rejection_reason": "Rejected because the surface optimizes for presentation, not repeated operator decisions and recovery states."
        },
        {
          "source_id": "single-screenshot-flow",
          "source_url_or_ref": "external:single-screenshot-flow",
          "rejection_reason": "Rejected because a single static screenshot cannot prove state transitions, recovery paths or interaction quality."
        },
        {
          "source_id": "happy-path-only-flow",
          "source_url_or_ref": "external:single-happy-path-flow",
          "rejection_reason": "Rejected because it does not show blocked, error, review or approval consequences."
        }
      ],
      "pattern_synthesis": {
        "layout_hierarchy": "Lead with source freshness, current state, blocker/next action and selected object before secondary metrics or explanation.",
        "interaction_model": "Use command strips, segmented state filters, searchable lists, adjacent inspectors and explicit approval/recovery actions.",
        "state_coverage": "Design and capture loading, empty, success, blocked, stale, contradictory, private-unavailable and visual-quality-fail states before PASS.",
        "visual_language": "Use a restrained professional product-tool language with semantic status color, crisp typography and no generic AI-dashboard decoration.",
        "density_spacing": "Keep dense but readable rows, fixed tool dimensions and compact panels so repeated operation is fast and stable.",
        "anti_patterns": [
          "single attractive screenshot without workflow proof",
          "decorative KPI cards disconnected from factory objects",
          "hero layout or marketing composition inside an operational operator console"
        ]
      },
      "reference_evidence_policy": {
        "capture_required_before_implementation": true,
        "side_by_side_comparison_required_before_pass": true,
        "public_refs_only": true,
        "no_private_screenshots_in_repo": true,
        "public_safe_evidence_refs": [
          "professional_design_process.reference_research.sources"
        ]
      }
    },
    "ux_architecture": {
      "information_hierarchy": ["status", "evidence", "review", "next action"],
      "navigation_model": "Two-screen operator flow with status overview and evidence detail.",
      "state_model": ["loading", "pending", "success", "error"],
      "density_rationale": "Operational review surface should be compact and state-first."
    },
    "wireframe_gate": {
      "status": "PASS",
      "reviewer": "product-face",
      "artifact_refs": ["examples/cards/v35_valid_product_face.md#product_face_packet"],
      "basis": "Wireframe separates status, evidence and review before styling."
    },
    "visual_direction": {
      "typography": "Compact system UI.",
      "spacing": "Stable rows and evidence groups.",
      "color_semantics": "Distinct state colors for pending, success and error.",
      "component_model": "Status summary, evidence list, review state and next action.",
      "anti_generic_commitments": [
        "No generic dashboard composition.",
        "No decorative metrics detached from evidence."
      ]
    },
    "prototype_gate": {
      "status": "PASS",
      "reviewer": "product-face",
      "artifact_refs": ["examples/cards/v35_valid_product_face.md#product_face_packet"],
      "basis": "Prototype scope covers status, evidence and review states.",
      "real_data_states": ["loading", "pending", "success", "error"]
    },
    "design_qa_plan": {
      "viewports": ["desktop 1440x900", "mobile 390x844"],
      "accessibility_checks": ["keyboard", "labels", "contrast"],
      "performance_checks": ["static render responsiveness"],
      "screenshot_requirements": ["desktop", "mobile"],
      "console_check_required": true,
      "overlap_check_required": true
    },
    "comparative_review_gate": {
      "status": "PASS",
      "reviewer_role": "independent-product-face-reviewer",
      "must_compare_to_reference_packet": true,
      "basis": "Independent Product Face reviewer must compare the implemented surface side-by-side against selected references, the pattern synthesis, task model and Product Face packet before approval.",
      "block_when": [
        "Generic dashboard visual quality appears.",
        "Evidence hierarchy is unclear.",
        "Reference research lacks real library searches, selected candidates and rejected candidates.",
        "The result cannot explain, dimension by dimension, how it matches or deliberately differs from the chosen references."
      ]
    },
    "handoff_requirements": {
      "required_before_implementation": [
        "reference research",
        "wireframe gate",
        "prototype gate",
        "design QA plan",
        "library searches",
        "rejected references",
        "pattern synthesis",
        "reference evidence policy"
      ],
      "product_face_result_must_include": [
        "project_design_system_ref",
        "project_design_system_comparison.status=pass",
        "professional_design_process_ref",
        "professional_design_process_comparison.status=pass",
        "reference_quality_comparison.status=pass"
      ]
    }
  }
}
```
