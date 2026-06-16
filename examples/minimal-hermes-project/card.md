```json
{
  "card_id": "MIN-HERMES-RECEIPT-PASS",
  "slice_id": "PUBLIC_MINIMAL_HERMES_PROJECT",
  "owner_profile": "product-face",
  "source_refs": [
    "examples/minimal-hermes-project/input-paper.md"
  ],
  "source_state": "compiled",
  "outcome": "Create a public-safe Product Face and receipt walkthrough for a tiny read-only product.",
  "acceptance_criteria": [
    "gate report can be generated",
    "required worker packets can be generated",
    "completion remains blocked until Product Face evidence and Receipt Five exist"
  ],
  "scope_in": [
    "local validation",
    "Product Face evidence plan",
    "Receipt Five example"
  ],
  "scope_out": [
    "production deploy",
    "secrets",
    "wallet signing",
    "funds movement",
    "real customer data",
    "Discord dependency"
  ],
  "target_repo_paths": [
    "examples/minimal-hermes-project"
  ],
  "conflict_set": [
    "A worker packet is not evidence; completion needs current worker results and Receipt Five."
  ],
  "risk_class": "R1-public-docs",
  "why_this_class": "The example is local, public-safe, documentation-first and does not mutate any external system.",
  "codex_mode": "advisory",
  "why_codex_mode": "Codex can inspect and validate the repository but does not approve completion.",
  "product_security_checks": [
    "public-safe fixture",
    "no real user data"
  ],
  "code_security_checks": [
    "no production code execution required"
  ],
  "system_security_checks": [
    "no external system mutation"
  ],
  "process_security_checks": [
    "Receipt Five required before done",
    "Product Face evidence required before visible completion"
  ],
  "verify_commands": [
    "python scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md",
    "python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md",
    "python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets"
  ],
  "evidence_expected": [
    "valid card result",
    "gate report",
    "required worker packets",
    "Receipt Five example"
  ],
  "reviewer_selection_plan": {
    "record_type": "reviewer_selection_plan",
    "changed_surfaces": [
      "frontend",
      "product-face",
      "public-docs"
    ],
    "risk_effective": "R1",
    "executor_identity": "product-face",
    "forbidden_reviewers": [
      "product-face"
    ],
    "required_reviewers": [
      "independent-reviewer"
    ],
    "reviewer_matrix": [
      {
        "reviewer_worker": "independent-reviewer",
        "covers": [
          "done evidence",
          "scope discipline",
          "Receipt Five shape"
        ],
        "reason": "The Product Face executor cannot be the sole reviewer of its own visible-surface evidence.",
        "mandatory": true
      }
    ],
    "selection_rule": "Use the smallest reviewer set that blocks self-review and covers visible-surface evidence for this local public-safe example.",
    "evidence_refs": [
      "examples/minimal-hermes-project/expected-flow.md"
    ]
  },
  "review": {
    "QA_required": true,
    "independent_review_required": true,
    "security_review_required": false,
    "cybersecurity_review_required": false,
    "CTO_gate_required": false,
    "human_gate_required": false
  },
  "factory_method_version": "OVERKILL_V3_5_FACTORY_10",
  "phase": "F5",
  "surfaces": [
    "ux",
    "frontend",
    "product-face"
  ],
  "risk_initial": "R1",
  "risk_effective": "R1",
  "authority_max": "local_validation_only",
  "owner_worker": "product-face",
  "executor_identity": "product-face",
  "reviewer_identity": "independent-reviewer",
  "runtime_decision": "hermes_default",
  "runtime_contract": {
    "mode": "local_validation",
    "hermes_required_for_real_run": true
  },
  "security_contract": {
    "security_boundary": "public_safe_local_fixture",
    "secret_access": "forbidden"
  },
  "security_scan_packet": {
    "security_owner": "security-orchestrator",
    "scanner_agent": "appsec-owasp-specialist",
    "scan_timing": "before_done",
    "scan_scope": [
      "read-only frontend fixture",
      "public example docs"
    ],
    "required_tools": [
      "appsec-owasp-specialist"
    ],
    "acceptance_policy": {
      "blocking_findings": "must_fix_or_human_waiver"
    }
  },
  "forbidden_actions": [
    "production_deploy",
    "secret_access",
    "wallet_signing",
    "funds_movement",
    "external_system_mutation"
  ],
  "done_definition": "The minimal example is documented, gate-reportable, packet-generating and clear that Product Face evidence plus Receipt Five are required before done.",
  "transition_event_required": true,
  "kanban_transition_event_ref": "required_before_done",
  "product_experience_plan": {
    "$schema": "https://overkill-factory.dev/schemas/product-experience-plan.schema.json",
    "surface_type": "web app",
    "surface_pack": "minimal-public-receipt-surface-pack",
    "product_delivery_quality_profile_ref": "templates/product-delivery-quality-profile.json",
    "surface_evidence_profile": "web_visual_ui",
    "experience_sot": "A first-time operator can see whether the minimal example is ready, blocked or missing Product Face and Receipt Five evidence.",
    "user": "external open-source factory operator",
    "job_to_be_done": "Understand the minimal factory flow and the exact evidence still required before done.",
    "main_flows": ["review receipt status", "find missing evidence", "inspect validation commands"],
    "required_states": ["loading", "empty", "success", "blocked"],
    "design_direction": {
      "visual_tone": "quiet public validation surface",
      "product_fit": "The surface must teach the factory proof boundary without looking like product completion.",
      "density": "compact and readable for first-run onboarding",
      "interaction_style": "linear inspection with explicit blocked-state guidance"
    },
    "visual_quality_bar": {
      "reference_quality_bar": "A quiet, inspectable operator receipt/status surface; not a generic marketing dashboard.",
      "anti_generic_criteria": [
        "no generic AI dashboard composition",
        "no excessive explanatory copy where status structure should carry meaning",
        "no decorative visual treatment that hides receipt state or next action"
      ],
      "professional_review_required": true,
      "block_when": [
        "mechanical screenshots pass but hierarchy, density or product fit feels generic",
        "the UI looks like a template rather than a purpose-built factory operator surface"
      ]
    },
    "proof_required": ["desktop screenshot", "mobile screenshot", "state matrix", "visual_quality_result verdict"],
    "reviewers_required": ["product-face", "qa-verification-worker", "independent-reviewer"],
    "done_definition": [
      "Product Face evidence plan exists before generated packets",
      "Receipt status states are checked",
      "visual_quality_result is PASS or PASS_WITH_RESIDUALS with reviewer basis"
    ],
    "human_gate": {
      "required": false,
      "approver": "",
      "reason": "Public minimal example has no material visual direction decision."
    },
    "prototype_decision": "prototype_not_required because the minimal flow is documented",
    "device_or_viewport_scope": ["desktop 1440x900", "mobile 390x844"],
    "accessibility_scope": ["keyboard", "focus", "contrast", "labels"],
    "performance_scope": ["local static receipt/status render"],
    "data_context": "Fixture states cover loading, empty, success and blocked evidence.",
    "docs_onboarding": ["first-run operator guidance stays in the example README and expected flow"],
    "experience_qa": ["responsive proof", "state coverage", "a11y basics"],
    "product_face_result_required": true,
    "evidence_refs": ["examples/minimal-hermes-project/card.md#product_experience_plan"],
    "reference_quality_waiver": {
      "owner": "product-face",
      "reason": "This minimal public fixture proves the Product Experience gate and first-run flow, not a production visual benchmark decision."
    }
  },
  "product_face_packet": {
    "$schema": "https://overkill-factory.dev/schemas/product-face-packet.schema.json",
    "surface": "web_app",
    "mode": "greenfield",
    "product_delivery_quality_profile_ref": "templates/product-delivery-quality-profile.json",
    "surface_evidence_profile": "web_visual_ui",
    "user": "external open-source factory operator",
    "job_to_be_done": "Understand the minimal factory flow and the exact evidence still required before done.",
    "main_flows": ["review receipt status", "find missing evidence", "inspect validation commands"],
    "required_states": ["loading", "empty", "success", "blocked"],
    "design_direction": {
      "visual_tone": "quiet public validation surface",
      "product_fit": "The surface must teach the factory proof boundary without looking like product completion.",
      "density": "compact and readable for first-run onboarding",
      "interaction_style": "linear inspection with explicit blocked-state guidance"
    },
    "screen_inventory": [
      "receipt status screen"
    ],
    "state_matrix": {
      "loading": "shown",
      "empty": "shown",
      "success": "shown",
      "blocked": "shown"
    },
    "design_contract_ref": "examples/minimal-hermes-project/input-paper.md",
    "mobile_breakpoints": [
      "375",
      "768",
      "1440"
    ],
    "wallet_flow_matrix": {
      "sign": "not_applicable",
      "reject": "not_applicable"
    },
    "a11y_acceptance": [
      "keyboard",
      "focus",
      "contrast",
      "labels"
    ],
    "performance_budget": {
      "bundle": "not_applicable",
      "render": "local_static_page"
    },
    "visual_quality_bar": {
      "reference_quality_bar": "A quiet, inspectable operator receipt/status surface; not a generic marketing dashboard.",
      "anti_generic_criteria": [
        "no generic AI dashboard composition",
        "no excessive explanatory copy where status structure should carry meaning",
        "no decorative visual treatment that hides receipt state or next action"
      ],
      "professional_review_required": true,
      "block_when": [
        "mechanical screenshots pass but hierarchy, density or product fit feels generic",
        "the UI looks like a template rather than a purpose-built factory operator surface"
      ]
    },
    "visual_evidence_plan": [
      "desktop screenshot",
      "mobile screenshot",
      "state matrix"
    ],
    "proof_required": ["desktop screenshot", "mobile screenshot", "state matrix", "visual_quality_result verdict"],
    "reviewers_required": ["product-face", "qa-verification-worker", "independent-reviewer"],
    "done_definition": [
      "result covers required flows and states",
      "result includes evidence for required viewports",
      "review confirms result fits the public minimal example promise",
      "visual_quality_result is PASS or PASS_WITH_RESIDUALS with reviewer basis"
    ],
    "human_gate": {
      "required": false,
      "approver": "",
      "reason": "Public minimal example has no material visual direction decision."
    }
  },
  "professional_design_process": {
    "record_type": "professional_design_process",
    "surface_type": "web_app",
    "mode": "greenfield",
    "design_brief": {
      "user": "External operator trying the public minimal factory example.",
      "job_to_be_done": "Understand whether a tiny Product Face/Receipt Five run is ready, blocked, or still missing evidence.",
      "decision_surface": "Receipt status screen for the minimal local example.",
      "success_signal": "A first-time operator can see state, missing evidence, and next safe action without private context.",
      "failure_risks": [
        "The example looks like a generic dashboard rather than a receipt/status walkthrough.",
        "The UI implies completion before Product Face evidence and Receipt Five exist."
      ]
    },
    "task_map": [
      {
        "task_id": "T1",
        "user_goal": "Confirm the current example state.",
        "trigger": "Operator opens the minimal receipt/status surface.",
        "success_signal": "State, source paper, and evidence requirement are visible immediately.",
        "failure_state": "The operator confuses a generated packet with completed evidence."
      },
      {
        "task_id": "T2",
        "user_goal": "Find the next safe action.",
        "trigger": "Receipt Five or Product Face proof is missing.",
        "success_signal": "The surface points to the exact missing proof without suggesting release.",
        "failure_state": "The UI offers a vague continue action or hides the blocker."
      },
      {
        "task_id": "T3",
        "user_goal": "Review whether the visual result fits the example.",
        "trigger": "Product Face validation runs before done.",
        "success_signal": "Reviewer compares screenshots, state coverage, and receipt clarity to the design packet.",
        "failure_state": "Browser checks pass while the example still looks template-like or misleading."
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
          "use_type": "accessibility-and-token-reference",
          "what_to_learn": [
            "Accessible primitive behavior",
            "Neutral token systems for dense tools"
          ],
          "extracted_patterns": [
            "Use semantic state colors instead of decorative gradients.",
            "Keep controls compact and predictable."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "public_safety_notes": "Reference only; no source code, text, or assets copied.",
          "source_type": "design_system",
          "library_source": "Radix Themes",
          "visual_dimensions_covered": [
            "visual_language",
            "density_spacing",
            "interaction_model"
          ],
          "candidate_reason": "Selected for Radix Themes patterns relevant to professional Product Face quality.",
          "selected_patterns": [
            "Use semantic state colors instead of decorative gradients.",
            "Keep controls compact and predictable."
          ]
        },
        {
          "source_id": "shadcn-data-table",
          "source_url_or_ref": "https://ui.shadcn.com/docs/components/data-table",
          "use_type": "structured-status-reference",
          "what_to_learn": [
            "Dense rows for inspectable operational data",
            "Search and filtering close to the data they affect"
          ],
          "extracted_patterns": [
            "Use rows and status chips when the user needs comparison.",
            "Avoid large isolated metric cards for small operational examples."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "public_safety_notes": "Reference only; no source code, text, or assets copied.",
          "source_type": "component_registry",
          "library_source": "shadcn/ui",
          "visual_dimensions_covered": [
            "layout_hierarchy",
            "interaction_model",
            "density_spacing"
          ],
          "candidate_reason": "Selected for shadcn/ui patterns relevant to professional Product Face quality.",
          "selected_patterns": [
            "Use rows and status chips when the user needs comparison.",
            "Avoid large isolated metric cards for small operational examples."
          ]
        },
        {
          "source_id": "linear-product-workflow",
          "source_url_or_ref": "https://linear.app",
          "use_type": "workflow-state-reference",
          "what_to_learn": [
            "Fast state scanning",
            "Clear distinction between issue status, owner, and next action"
          ],
          "extracted_patterns": [
            "Operational tools should be state-first and compact.",
            "Important blockers should be visible without a hero section."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied",
          "public_safety_notes": "Reference only; no source code, text, or assets copied.",
          "source_type": "product_reference",
          "library_source": "Linear public product reference",
          "visual_dimensions_covered": [
            "layout_hierarchy",
            "state_coverage",
            "density_spacing"
          ],
          "candidate_reason": "Selected for Linear public product reference patterns relevant to professional Product Face quality.",
          "selected_patterns": [
            "Operational tools should be state-first and compact.",
            "Important blockers should be visible without a hero section."
          ]
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
          "hero layout or marketing composition inside an operational cockpit"
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
      "information_hierarchy": [
        "example state",
        "missing Product Face or Receipt Five evidence",
        "next safe action",
        "source and validation refs",
        "review status"
      ],
      "navigation_model": "Single local status view with state summary, evidence checklist, and receipt detail.",
      "state_model": [
        "loading",
        "empty",
        "success",
        "blocked",
        "error"
      ],
      "density_rationale": "Keep the minimal example compact so first-run users see the factory rule without navigating a large dashboard."
    },
    "wireframe_gate": {
      "status": "PASS",
      "reviewer": "product-face",
      "artifact_refs": [
        "examples/minimal-hermes-project/expected-flow.md"
      ],
      "basis": "The public example flow separates generated packets, evidence requirements, and completion status before implementation."
    },
    "visual_direction": {
      "typography": "Compact system UI with clear status labels and no hero-scale display type.",
      "spacing": "Small, stable status rows and checklist spacing.",
      "color_semantics": "Neutral base with distinct blocked, success, and warning states.",
      "component_model": "Status summary, evidence checklist, receipt details, and validation command list.",
      "anti_generic_commitments": [
        "No decorative KPI dashboard for a tiny receipt example.",
        "No generic AI-product wording in place of exact evidence state.",
        "No completion styling while required proof is missing."
      ]
    },
    "prototype_gate": {
      "status": "PASS",
      "reviewer": "product-face",
      "artifact_refs": [
        "examples/minimal-hermes-project/expected-flow.md"
      ],
      "basis": "The prototype path covers ready, blocked, and missing-evidence states before Product Face proof.",
      "real_data_states": [
        "ready for worker execution",
        "missing Product Face result",
        "missing Receipt Five",
        "blocked completion"
      ]
    },
    "design_qa_plan": {
      "viewports": [
        "desktop 1440x900",
        "mobile 390x844"
      ],
      "accessibility_checks": [
        "keyboard focus names",
        "semantic headings",
        "contrast",
        "clear evidence labels"
      ],
      "performance_checks": [
        "local static render remains responsive",
        "no remote fetch",
        "no decorative payload"
      ],
      "screenshot_requirements": [
        "desktop status view",
        "mobile status view",
        "blocked evidence state"
      ],
      "console_check_required": true,
      "overlap_check_required": true
    },
    "comparative_review_gate": {
      "status": "PASS",
      "reviewer_role": "independent-product-face-reviewer",
      "must_compare_to_reference_packet": true,
      "basis": "Independent Product Face reviewer must compare the implemented surface side-by-side against selected references, the pattern synthesis, task model and Product Face packet before approval.",
      "block_when": [
        "The result hides receipt state or evidence requirements.",
        "Reference research does not affect hierarchy, controls, or state treatment.",
        "Mechanical screenshots pass while the surface remains generic or misleading.",
        "Reference research lacks real library searches, selected candidates and rejected candidates.",
        "The result cannot explain, dimension by dimension, how it matches or deliberately differs from the chosen references."
      ]
    },
    "handoff_requirements": {
      "required_before_implementation": [
        "design brief",
        "task map",
        "reference research",
        "library searches",
        "rejected references",
        "pattern synthesis",
        "reference evidence policy",
        "UX architecture",
        "wireframe gate",
        "visual direction",
        "prototype gate",
        "design QA plan",
        "comparative review gate"
      ],
      "product_face_result_must_include": [
        "professional_design_process_ref",
        "professional_design_process_comparison.status=pass",
        "reference_quality_comparison.status=pass"
      ]
    }
  }
}
```
