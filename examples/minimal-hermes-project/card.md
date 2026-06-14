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
  "product_face_packet": {
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
    ]
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
        "templates/reference-source-registry.json#refero-styles"
      ],
      "selection_rationale": "Use public component and product-tool references for structure and density only; no copied code, copy, or assets.",
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
          "public_safety_notes": "Reference only; no source code, text, or assets copied."
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
          "public_safety_notes": "Reference only; no source code, text, or assets copied."
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
          "public_safety_notes": "Reference only; no source code, text, or assets copied."
        }
      ]
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
      "reviewer_role": "product-face",
      "must_compare_to_reference_packet": true,
      "basis": "The minimal Product Face reviewer must compare the surface against the design packet and block generic dashboard symptoms.",
      "block_when": [
        "The result hides receipt state or evidence requirements.",
        "Reference research does not affect hierarchy, controls, or state treatment.",
        "Mechanical screenshots pass while the surface remains generic or misleading."
      ]
    }
  }
}
```
