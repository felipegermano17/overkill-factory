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
  "product_face_packet": {
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
    "visual_evidence_plan": ["desktop screenshot", "mobile screenshot"]
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
        "templates/reference-source-registry.json#refero-styles"
      ],
      "selection_rationale": "Use professional product-tool references to avoid generic generated UI.",
      "sources": [
        {
          "source_id": "radix-ui-themes",
          "source_url_or_ref": "https://www.radix-ui.com/themes",
          "use_type": "accessibility-reference",
          "what_to_learn": ["semantic tokens", "accessible controls"],
          "extracted_patterns": [
            "Use state semantics over decoration.",
            "Keep controls compact and named."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied"
        },
        {
          "source_id": "shadcn-data-table",
          "source_url_or_ref": "https://ui.shadcn.com/docs/components/data-table",
          "use_type": "dense-data-reference",
          "what_to_learn": ["row scanning", "filters"],
          "extracted_patterns": [
            "Dense lists need stable row focus.",
            "Controls should stay near affected data."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied"
        },
        {
          "source_id": "linear-product-workflow",
          "source_url_or_ref": "https://linear.app",
          "use_type": "workflow-reference",
          "what_to_learn": ["state-first workflow", "quiet product-tool hierarchy"],
          "extracted_patterns": [
            "Work context should be visible without a hero.",
            "Status hierarchy should be compact and scannable."
          ],
          "copy_policy": "do_not_copy",
          "license_or_terms_ref": "benchmark_only_no_code_or_assets_copied"
        }
      ]
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
      "reviewer_role": "product-face",
      "must_compare_to_reference_packet": true,
      "basis": "Product Face reviewer compares result to packet and reference quality bar.",
      "block_when": [
        "Generic dashboard visual quality appears.",
        "Evidence hierarchy is unclear."
      ]
    },
    "handoff_requirements": {
      "required_before_implementation": ["reference research", "wireframe gate", "prototype gate", "design QA plan"],
      "product_face_result_must_include": ["professional_design_process_ref", "professional_design_process_comparison.status=pass"]
    }
  }
}
```
