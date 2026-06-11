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
    "visual_evidence_plan": [
      "desktop screenshot",
      "mobile screenshot",
      "state matrix"
    ]
  }
}
```
