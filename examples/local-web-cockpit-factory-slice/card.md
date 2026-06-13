```json
{
  "card_id": "LOCAL-WEB-COCKPIT-VFINAL-001",
  "slice_id": "LOCAL_WEB_COCKPIT_FACTORY_SLICE",
  "owner_profile": "factory-orchestrator",
  "request_type": "ux_ui",
  "source_refs": [
    "examples/local-web-cockpit-factory-slice/input-paper.md",
    "docs/operations/parallel-execution-and-status.md",
    "docs/control-tower/discord-cockpit-ux-study-gate.md",
    "templates/factory-status-snapshot.json",
    "templates/discord-control-tower-ux-audit.json"
  ],
  "source_state": "compiled",
  "outcome": "Prepare the factory to create a local-first web cockpit through gated product production, without hand-implementing the UI outside the factory.",
  "acceptance_criteria": [
    "Product SOT and Method Contract define a local-first open-source operator cockpit",
    "factory gate report and required worker packets can be generated",
    "implementation remains blocked until Product Face, security, QA and independent review evidence exist",
    "the cockpit consumes structured status snapshots and safe evidence refs instead of raw logs or chat memory",
    "generic AI-dashboard visual quality is a blocking Product Face defect"
  ],
  "scope_in": [
    "local-first cockpit product slice",
    "Product SOT",
    "Method Contract",
    "Product Experience plan",
    "Product Face Packet",
    "security and public-safety boundaries",
    "worker packet generation",
    "status snapshot projection contract"
  ],
  "scope_out": [
    "manual Codex implementation of the cockpit UI",
    "single-operator hosted infrastructure",
    "private Discord coupling",
    "runtime mutation outside factory gates",
    "raw private evidence rendering",
    "production deploy",
    "secret access"
  ],
  "target_repo_paths": [
    "examples/local-web-cockpit-factory-slice",
    "docs/control-tower",
    "schemas/factory-status-snapshot.schema.json",
    "templates/factory-status-snapshot.json"
  ],
  "risk_class": "R2-product-control-surface",
  "why_this_class": "The cockpit is local-first and public-safe, but it affects operator decisions, approvals, evidence interpretation and release readiness.",
  "codex_mode": "operate_factory_gates_only",
  "why_codex_mode": "Codex may supply the request, observe gate output and fix factory contracts, but must not hand-design or hand-implement the cockpit.",
  "review": {
    "QA_required": true,
    "independent_review_required": true,
    "security_review_required": true,
    "cybersecurity_review_required": false,
    "CTO_gate_required": false,
    "human_gate_required": false
  },
  "factory_method_version": "OVERKILL_VFINAL",
  "phase": "F7",
  "surfaces": [
    "ux",
    "frontend",
    "product-face",
    "control-tower",
    "public-docs",
    "security"
  ],
  "capability_coverage_required": true,
  "risk_initial": "R2",
  "risk_effective": "R2",
  "authority_max": "plan_route_and_generate_worker_packets_only",
  "owner_worker": "factory-orchestrator",
  "executor_identity": "factory-orchestrator",
  "reviewer_identity": "independent-reviewer",
  "runtime_decision": "local_factory_runtime_until_operator_publishes",
  "runtime_contract": {
    "mode": "local_first_factory_execution",
    "source_of_truth": "factory-status-snapshot and runtime cards",
    "parallel_execution_requested": false,
    "status_snapshot_required": true,
    "local_run_required": true,
    "publishing_left_to_operator": true,
    "forbidden_runtime_sources": [
      "chat memory",
      "raw private logs",
      "private Discord state",
      "manual stale screenshots"
    ]
  },
  "security_contract": {
    "security_boundary": "local web cockpit reads structured snapshots and public-safe evidence refs only",
    "secret_access": "forbidden",
    "raw_private_evidence_rendering": "forbidden",
    "local_server_exposure": "localhost by default; remote exposure requires explicit operator deployment decision",
    "request_approval_boundary": "request, approval, blocked, done, released and superseded states must be visually and semantically distinct"
  },
  "security_scan_packet": {
    "security_owner": "security-orchestrator",
    "scanner_agent": "appsec-owasp-specialist",
    "scan_timing": "before_implementation_and_before_done",
    "scan_scope": [
      "local web server boundary",
      "snapshot ingestion",
      "raw evidence redaction",
      "request versus approval confusion",
      "public repo artifacts"
    ],
    "required_tools": [
      "public_safety_scan.py",
      "secret_safety_scan.py",
      "supply_chain_proof.py",
      "appsec review"
    ],
    "acceptance_policy": {
      "blocking_findings": "must_fix_or_explicit_human_waiver",
      "private_data_leak": "block"
    }
  },
  "forbidden_actions": [
    "manual_ui_implementation_outside_factory",
    "production_deploy",
    "secret_access",
    "raw_private_evidence_publication",
    "private_discord_id_publication",
    "treat_discord_as_source_of_truth",
    "approve_generic_ai_dashboard_visual_quality"
  ],
  "done_definition": "This planning slice is done only when factory gates can generate required worker packets and implementation remains blocked until Product Face, security, QA, independent review and Receipt Five evidence exist.",
  "transition_event_required": true,
  "kanban_transition_event_ref": "required_before_ready",
  "outcome_contract": {
    "$schema": "https://overkill-factory.dev/schemas/outcome-contract.schema.json",
    "outcome": "A factory-ready product slice for a local-first web cockpit.",
    "users_or_actors": [
      "external open-source factory operator",
      "factory maintainer",
      "reviewer"
    ],
    "problem": "Operators need a serious local cockpit for state, blockers, evidence and decisions, but the public factory must not assume private infrastructure or accept low-quality generated dashboards.",
    "success_signals": [
      "operator can run gates locally",
      "worker packets are generated under .tmp",
      "implementation is blocked until evidence exists",
      "Product Face visual quality bar names the anti-generic failure mode"
    ],
    "non_goals": [
      "build the UI in this planning card",
      "host a SaaS cockpit",
      "replace runtime state",
      "publish private runtime evidence"
    ],
    "open_questions": [
      "Which implementation stack should the factory select after Method Router and Product Face review?",
      "Which status snapshot fields are mandatory for the first UI slice?"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/input-paper.md",
      "docs/operations/parallel-execution-and-status.md",
      "docs/control-tower/discord-cockpit-ux-study-gate.md"
    ],
    "behavior_change": "The cockpit request is routed through factory gates instead of being manually implemented by the operator.",
    "risk_signals": [
      "UI resembles generic dashboard filler",
      "state freshness is unclear",
      "approval and request states are ambiguous",
      "raw evidence or private ids appear in public artifacts"
    ],
    "assumptions": [
      "The first accepted cockpit should run locally from structured snapshots.",
      "Discord remains secondary until proof demonstrates otherwise."
    ],
    "human_questions": [],
    "discovery_depth": "standard"
  },
  "product_sot": {
    "$schema": "https://overkill-factory.dev/schemas/product-sot.schema.json",
    "what_it_is": "A local-first web cockpit for supervising Overkill Factory runs from structured status snapshots, gates, worker results and safe evidence refs.",
    "target_users": [
      "external open-source operator",
      "factory maintainer",
      "reviewer"
    ],
    "why_it_matters": "Operators need fast, calm, trustworthy visibility into factory state without relying on private Discord, private hosting or chat memory.",
    "outcome": "The factory has a gated, implementation-ready product slice for a local cockpit, with implementation blocked until required worker evidence exists.",
    "scope_in": [
      "portfolio view across projects or runs",
      "pipeline phase and next safe action",
      "gate pass/fail/stale state",
      "blockers with owner and unblock condition",
      "parallel lanes and worktree state",
      "worker activity and review state",
      "safe evidence graph",
      "timeline and audit trail",
      "human decisions required or recorded",
      "release and public-promotion status",
      "local run mode"
    ],
    "scope_out": [
      "private hosted service",
      "private Discord dependency",
      "raw private evidence rendering",
      "source-of-truth replacement",
      "manual implementation before gates",
      "generic generated dashboard style"
    ],
    "risks": [
      "operator trusts stale state",
      "approval is confused with request or chat",
      "UI hides blockers or failed gates",
      "public repo leaks private paths or ids",
      "implementation passes mechanical checks but fails Product Face quality"
    ],
    "authority": "Factory gates own readiness; Product Face owns visual/product proof; the operator owns publishing decisions.",
    "data_and_metrics": [
      "state freshness age",
      "next-action findability",
      "blocked item count",
      "stale or contradictory snapshot count",
      "local render performance"
    ],
    "dependencies": [
      "#80 factory status snapshot protocol",
      "#82 Product Face visual quality gate",
      "#83 Discord UX study boundary",
      "factoryctl worker packets",
      "public-safe evidence refs"
    ],
    "access_and_capabilities": [
      "repo read/write for implementation branch after gates",
      "local test execution",
      "browser screenshot proof",
      "no secrets required for public slice"
    ],
    "compliance_privacy": [
      "no private Discord ids",
      "no local absolute paths",
      "no raw private runtime logs",
      "no secrets",
      "public-safe fixtures only"
    ],
    "cost_relevance": "No material spend for local-first planning or local proof.",
    "operations_expected": [
      "runs locally by default",
      "operator chooses deployment if needed",
      "degrades gracefully when snapshots are stale or missing"
    ],
    "success_criteria": [
      "factory gate report can be generated",
      "required worker packets can be generated",
      "Product Face Packet blocks generic AI-dashboard quality",
      "security plan blocks raw evidence and private id leakage"
    ],
    "open_decisions": [
      "implementation stack after Method Router",
      "first UI slice scope after worker execution",
      "exact status snapshot fixture set for visual proof"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/input-paper.md"
    ]
  },
  "method_contract": {
    "$schema": "https://overkill-factory.dev/schemas/method-contract.schema.json",
    "selected_method": "spec-first",
    "why_this_method": "The cockpit controls operator decisions and must not begin with a visual prototype or implementation before source, UX, security and proof gates are ready.",
    "risk_tier": "R2",
    "required_plans": [
      "product_experience_plan",
      "software_development_plan",
      "security_architecture_plan",
      "data_metrics_plan",
      "agent_eval_plan"
    ],
    "required_gates": [
      "Source Resolution Gate",
      "Product SOT Gate",
      "Method Contract Gate",
      "Product Face Gate",
      "Security Gate",
      "Ready Gate",
      "Review Gate",
      "Done Gate"
    ],
    "waivers": [],
    "work_type": "local-first product surface",
    "selected_methods": [
      "spec-first",
      "product-face-first",
      "security-before-build"
    ],
    "skipped_methods": [
      {
        "method": "prototype-first",
        "reason": "A prototype-first path would risk repeating the generic dashboard failure before the quality bar and data contracts are locked."
      }
    ],
    "required_artifacts": [
      "Product SOT",
      "Method Contract",
      "Product Experience Plan",
      "Product Face Packet",
      "Security Architecture Plan",
      "Status Snapshot fixture contract",
      "Worker packets",
      "Receipt Five after execution"
    ],
    "required_workers": [
      "factory-orchestrator",
      "source-ledger-worker",
      "product-sot-planner",
      "product-face",
      "product-architect",
      "security-orchestrator",
      "appsec-owasp-specialist",
      "decomposition-planner",
      "frontend-builder",
      "qa-verification-worker",
      "independent-reviewer",
      "public-safety-gate",
      "supply-chain-gate"
    ],
    "reviewers": [
      "product-face",
      "independent-reviewer",
      "security-orchestrator"
    ],
    "evidence_requirements": [
      "gate report",
      "worker packets",
      "status snapshot fixture",
      "visual quality review",
      "browser screenshots after implementation",
      "public and secret scans",
      "supply-chain proof",
      "independent review"
    ],
    "authority_limit": "The card may route and generate worker packets; implementation and acceptance require worker evidence.",
    "done_criteria": [
      "required packets generated",
      "implementation remains blocked without Product Face result",
      "Receipt Five remains pending until real execution evidence exists"
    ]
  },
  "capability_pack_contract": {
    "$schema": "https://overkill-factory.dev/schemas/capability-pack-contract.schema.json",
    "record_type": "capability_pack_contract",
    "pack_id": "web-saas-core",
    "status": "ready",
    "covered_surfaces": [
      "frontend",
      "ux",
      "product-face",
      "public-docs",
      "security"
    ],
    "specialist_workers": [
      "product-face",
      "frontend-builder",
      "qa-verification-worker",
      "independent-reviewer",
      "security-orchestrator",
      "public-safety-gate"
    ],
    "activation_evidence_refs": [
      "agents/capability-packs.public.json#web-saas-core",
      "agents/capability-packs.public.json#operator-onboarding-pack"
    ],
    "missing_capabilities": [],
    "execution_rule": "Execution can start only after Product SOT, Product Face, security and ready gates return evidence.",
    "product_pack_id": "local-web-operator-cockpit",
    "product_pack_version": "v1",
    "surface_pack_id": "web-cockpit",
    "risk_addendum": [
      "R2 operator control surface requires independent review and security review"
    ],
    "templates_required": [
      "templates/product-experience-plan.json",
      "templates/product-face-packet.json",
      "templates/factory-status-snapshot.json"
    ],
    "evidence_required": [
      "worker packets",
      "Product Face result",
      "security scan result",
      "Receipt Five"
    ],
    "worker_mapping": {
      "plan": [
        "factory-orchestrator",
        "product-sot-planner",
        "product-face"
      ],
      "build": [
        "frontend-builder"
      ],
      "verify": [
        "qa-verification-worker",
        "public-safety-gate",
        "supply-chain-gate"
      ],
      "review": [
        "independent-reviewer",
        "security-orchestrator"
      ]
    }
  },
  "reasoning_policy": {
    "$schema": "https://overkill-factory.dev/schemas/reasoning-policy.schema.json",
    "record_type": "reasoning_policy",
    "reasoning_class": "deep",
    "allowed_profile_classes": [
      "review-capable-worker",
      "product-face",
      "security-review"
    ],
    "review_intensity": "independent_review",
    "evidence_policy": {
      "durable_summary_required": true,
      "raw_chain_of_thought_forbidden": true,
      "evidence_refs_required": true
    },
    "private_reasoning_policy": "summarize_only",
    "block_when": [
      "implementation starts before Product Face Packet",
      "worker result lacks evidence refs",
      "reviewer is same identity as executor"
    ],
    "derived_from": [
      "R2 operator control surface",
      "Product Face visual quality risk",
      "public/private boundary risk"
    ]
  },
  "reference_quality_packet": {
    "$schema": "https://overkill-factory.dev/schemas/reference-quality-packet.schema.json",
    "record_type": "reference_quality_packet",
    "experience_category": "local operations cockpit",
    "quality_bar": "Dense, calm, professional operations UI that feels purpose-built for repeated supervision, not a generic AI-generated dashboard.",
    "anti_generic_criteria": [
      "no oversized hero sections",
      "no decorative cards as filler",
      "no one-note palette",
      "no vague charts without source state",
      "no marketing layout",
      "no AI-dashboard sameness"
    ],
    "references": [
      {
        "source_id": "linear-issue-views",
        "source_url_or_ref": "external:benchmark-linear-issue-views",
        "use_type": "benchmark",
        "what_to_learn": [
          "dense status hierarchy",
          "fast issue scanning",
          "quiet repeated-use interaction"
        ],
        "copy_policy": "do_not_copy",
        "license_or_terms_ref": "benchmark_only_no_assets_or_code",
        "public_safety_notes": "Benchmark only; no copied code, screenshots or brand assets."
      },
      {
        "source_id": "datadog-incident-views",
        "source_url_or_ref": "external:benchmark-incident-ops-views",
        "use_type": "benchmark",
        "what_to_learn": [
          "incident status clarity",
          "timeline and ownership",
          "alert triage density"
        ],
        "copy_policy": "do_not_copy",
        "license_or_terms_ref": "benchmark_only_no_assets_or_code",
        "public_safety_notes": "Benchmark only; no copied code, screenshots or brand assets."
      }
    ],
    "design_rationale": "The cockpit must optimize supervision and decision safety, not visual novelty.",
    "component_expectations": [
      "portfolio table or list with stable state columns",
      "phase rail",
      "next-action rail",
      "blocker queue",
      "evidence graph",
      "timeline"
    ],
    "interaction_expectations": [
      "filter by blocked/stale/needs approval",
      "open project detail without losing portfolio context",
      "show source snapshot freshness",
      "separate requests from approvals"
    ],
    "visual_constraints": [
      "compact density",
      "clear hierarchy",
      "restrained color",
      "no decorative generated-dashboard filler"
    ],
    "reuse_policy": {
      "allowed": [
        "benchmarking",
        "interaction pattern study"
      ],
      "forbidden": [
        "blind copy",
        "unlicensed code or asset reuse",
        "brand imitation"
      ],
      "license_required_for_code_or_assets": true
    },
    "accessibility_constraints": [
      "keyboard path",
      "visible focus",
      "contrast",
      "semantic labels",
      "status text not color-only"
    ],
    "performance_constraints": [
      "bounded snapshot payload",
      "fast local render",
      "graceful stale/missing data states"
    ],
    "acceptance_criteria": [
      "Product Face visual quality review passes",
      "operator can find next safe action quickly",
      "generic dashboard style is blocked"
    ],
    "product_experience_fields_informed": [
      "design_direction",
      "visual_quality_bar",
      "proof_required"
    ]
  },
  "software_development_plan": {
    "$schema": "https://overkill-factory.dev/schemas/software-development-plan.schema.json",
    "work_units": [
      "define status snapshot fixture set",
      "build local read-only cockpit shell",
      "render portfolio, project detail, blockers, evidence graph and timeline",
      "add Product Face proof harness"
    ],
    "work_unit_contracts": [
      "templates/work-unit-contract.json"
    ],
    "qa_plan": [
      "unit tests for snapshot parsing",
      "browser tests for core states",
      "public safety and secret scans",
      "Product Face proof after implementation"
    ],
    "review_plan": [
      "Product Face review",
      "security review",
      "independent review"
    ],
    "reviewer_selection_plan": "reviewer_selection_plan",
    "release_or_block_rule": "Block if Product Face visual quality, security, public safety, supply chain or independent review fails.",
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ],
    "required_artifacts": [
      "local fixture",
      "implementation PR",
      "Product Face proof",
      "Receipt Five"
    ],
    "skipped_artifacts": [],
    "prd": "Local-first factory cockpit for structured state supervision.",
    "trd": "Read structured snapshots and render local UI without secret or private runtime coupling.",
    "domain_map": [
      "project",
      "run",
      "gate",
      "worker",
      "evidence ref",
      "human decision",
      "release state"
    ],
    "acceptance_examples": [
      "Given a stale snapshot, the cockpit labels state as stale and blocks approval confidence.",
      "Given a blocked gate, the next safe action points to unblock condition and owner.",
      "Given an approval request, the UI distinguishes it from recorded approval."
    ],
    "stories": [
      "As an operator, I can see which project needs attention without reading raw logs.",
      "As a reviewer, I can inspect evidence refs without exposing private evidence."
    ],
    "factory_cards": [
      "LOCAL-WEB-COCKPIT-VFINAL-001"
    ],
    "slice_plan": [
      "planning and worker packet generation first",
      "implementation only after gates"
    ],
    "test_plan": [
      "validate-card",
      "gate-report",
      "worker-packet",
      "status-snapshot",
      "browser/Product Face proof after implementation"
    ],
    "security_architecture_ref": "security_architecture_plan",
    "legacy_migration_decision": "not_needed",
    "platform_devex_decision": "not_needed",
    "release_plan": [
      "no public release until local smoke, Product Face proof, security and review pass"
    ],
    "documentation_plan": [
      "document local run mode and public/private boundary"
    ]
  },
  "product_experience_plan": {
    "$schema": "https://overkill-factory.dev/schemas/product-experience-plan.schema.json",
    "surface_type": "local web app",
    "surface_pack": "web-cockpit",
    "experience_sot": "The operator can understand factory state, risk, blockers, evidence and next safe action from structured snapshots without private context.",
    "user": "external open-source factory operator",
    "job_to_be_done": "Supervise factory execution locally and decide what needs attention without reading raw logs or chat history.",
    "main_flows": [
      "portfolio scan",
      "project/run detail",
      "blocker triage",
      "evidence graph inspection",
      "timeline/replay review",
      "human decision review"
    ],
    "required_states": [
      "empty",
      "fresh",
      "stale",
      "blocked",
      "needs_approval",
      "failed_gate",
      "released",
      "superseded"
    ],
    "design_direction": {
      "visual_tone": "calm, dense and operational",
      "product_fit": "built for repeated supervision of factory state, not a generic dashboard demo",
      "density": "compact but readable",
      "interaction_style": "direct drill-down from portfolio to project detail, with source freshness always visible"
    },
    "visual_quality_bar": {
      "reference_quality_bar": "Professional operations cockpit quality comparable to serious issue, incident and observability tools, adapted to factory state.",
      "anti_generic_criteria": [
        "no generic AI dashboard composition",
        "no decorative gradient hero",
        "no fake metrics",
        "no card clutter without state meaning",
        "no vague pastel admin template",
        "no text-heavy explanation replacing clear hierarchy"
      ],
      "professional_review_required": true,
      "block_when": [
        "mechanical screenshots pass but the interface looks like generic AI output",
        "operator cannot tell request from approval or blocked from done",
        "state freshness is visually unclear",
        "next safe action is not findable"
      ]
    },
    "proof_required": [
      "desktop screenshot",
      "bounded mobile or narrow viewport screenshot when useful",
      "state coverage",
      "staleness behavior",
      "performance note",
      "accessibility basics",
      "visual_quality_result"
    ],
    "reviewers_required": [
      "product-face",
      "qa-verification-worker",
      "independent-reviewer"
    ],
    "done_definition": [
      "all required states covered",
      "visual_quality_result is PASS or PASS_WITH_RESIDUALS with reviewer basis",
      "generic dashboard failure mode is explicitly checked"
    ],
    "human_gate": {
      "required": false,
      "approver": "",
      "reason": "No human release approval in planning slice; implementation may require one if scope changes."
    },
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/input-paper.md"
    ]
  },
  "product_face_packet": {
    "$schema": "https://overkill-factory.dev/schemas/product-face-packet.schema.json",
    "surface": "local_web_cockpit",
    "mode": "planning",
    "user": "external open-source factory operator",
    "job_to_be_done": "Supervise factory state locally, identify blockers and next safe actions, and inspect evidence refs without private leakage.",
    "main_flows": [
      "portfolio scan",
      "project detail",
      "blocker triage",
      "evidence graph",
      "timeline replay",
      "decision review"
    ],
    "required_states": [
      "empty",
      "fresh",
      "stale",
      "blocked",
      "needs_approval",
      "failed_gate",
      "released",
      "superseded"
    ],
    "design_direction": {
      "visual_tone": "quiet operational cockpit",
      "product_fit": "factory-specific state supervision",
      "density": "dense but scannable",
      "interaction_style": "portfolio-to-detail drilldown with persistent freshness and next-action cues"
    },
    "visual_quality_bar": {
      "reference_quality_bar": "High-quality local operations cockpit, not a generic AI dashboard.",
      "anti_generic_criteria": [
        "no generic dashboard filler",
        "no decorative hero or marketing layout",
        "no fake charts",
        "no excessive cards without operational hierarchy",
        "no state ambiguity"
      ],
      "professional_review_required": true,
      "block_when": [
        "looks like a generated dashboard template",
        "request, approval, blocked, done, released or superseded states blur together",
        "next safe action is not obvious",
        "source freshness is hidden"
      ]
    },
    "proof_required": [
      "screenshots",
      "viewports",
      "checked states",
      "a11y",
      "overlap check",
      "performance note",
      "visual quality review"
    ],
    "reviewers_required": [
      "product-face",
      "qa-verification-worker",
      "independent-reviewer"
    ],
    "done_definition": [
      "Product Face proof captures required states",
      "visual quality reviewer approves against reference bar",
      "generic dashboard failure mode is blocked"
    ],
    "human_gate": {
      "required": false,
      "approver": "",
      "reason": "Planning slice does not request release approval."
    }
  },
  "data_metrics_plan": {
    "$schema": "https://overkill-factory.dev/schemas/data-metrics-plan.schema.json",
    "success_metrics": [
      "operator finds next safe action",
      "stale state is labeled",
      "blocked work has owner and unblock condition",
      "required evidence refs are visible"
    ],
    "risk_metrics": [
      "ambiguous approval state count",
      "stale snapshot age",
      "missing evidence ref count",
      "raw private evidence render attempts"
    ],
    "events": [
      "factory.status_snapshot.loaded",
      "factory.gate.blocked",
      "factory.human_decision.required",
      "factory.evidence_ref.opened"
    ],
    "dashboards": [
      "local web cockpit"
    ],
    "logs": [
      "local structured snapshot load result"
    ],
    "alerts": [
      "stale snapshot",
      "contradictory state",
      "private evidence blocked"
    ],
    "privacy_notes": [
      "no raw private logs",
      "safe evidence refs only"
    ],
    "instrumentation_proof": [
      "status snapshot fixture",
      "browser proof after implementation"
    ]
  },
  "agent_eval_plan": {
    "$schema": "https://overkill-factory.dev/schemas/agent-eval-plan.schema.json",
    "agents_or_skills": [
      "factory-orchestrator",
      "product-face",
      "frontend-builder",
      "qa-verification-worker"
    ],
    "eval_cases": [
      "blocks implementation before Product Face Packet",
      "blocks generic AI-dashboard visual quality",
      "rejects raw private evidence refs",
      "separates request from approval"
    ],
    "authority_tests": [
      "operator cannot approve Product Face result",
      "frontend-builder cannot self-approve visual quality",
      "Discord cannot become source of truth"
    ],
    "evidence_tests": [
      "worker packets generated under .tmp",
      "Receipt Five remains pending before execution",
      "PASS requires evidence refs"
    ],
    "regression_policy": "Add tests for every blocked bypass discovered during cockpit execution.",
    "versioning": [
      "factory card version",
      "Product Face Packet version",
      "status snapshot schema version"
    ]
  },
  "security_architecture_plan": {
    "$schema": "https://overkill-factory.dev/schemas/security-architecture-plan.schema.json",
    "trust_boundaries": [
      "local browser",
      "local web server",
      "status snapshot files",
      "public-safe evidence refs",
      "private runtime evidence outside repo"
    ],
    "sensitive_data": [
      "private paths",
      "private Discord ids",
      "raw runtime logs",
      "tokens",
      "webhooks",
      "private URLs"
    ],
    "auth_and_permissions": [
      "local read-only default",
      "no secret access for public slice",
      "operator-owned deployment if published"
    ],
    "threats": [
      "private evidence leak",
      "stale state trusted as fresh",
      "request mistaken for approval",
      "malicious snapshot content rendered unsafely",
      "public repo publishes private runtime refs"
    ],
    "controls": [
      "structured snapshot schema",
      "safe evidence refs only",
      "staleness warnings",
      "state labels",
      "public safety scan",
      "secret safety scan",
      "supply-chain proof",
      "independent review"
    ],
    "security_reviewers": [
      "security-orchestrator",
      "appsec-owasp-specialist",
      "public-safety-gate"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "spec_graph": {
    "$schema": "https://overkill-factory.dev/schemas/spec-graph.schema.json",
    "requirements": [
      "local-first cockpit",
      "structured snapshot input",
      "safe evidence refs",
      "Product Face quality gate",
      "public/private boundary"
    ],
    "outcome_links": [
      "outcome_contract",
      "product_sot"
    ],
    "examples": [
      "stale snapshot warns",
      "blocked gate shows owner",
      "approval request is not recorded approval"
    ],
    "decisions": [
      "spec-first before implementation",
      "Discord remains secondary",
      "web cockpit handles dense state"
    ],
    "risks": [
      "generic UI",
      "private leak",
      "stale state",
      "approval ambiguity"
    ],
    "dependencies": [
      "#80",
      "#82",
      "#83",
      "factory-status-snapshot.schema.json"
    ],
    "access_needs": [
      "local repo and test execution"
    ],
    "security_architecture_refs": [
      "security_architecture_plan"
    ],
    "data_refs": [
      "data_metrics_plan"
    ],
    "gates": [
      "Product Face Gate",
      "Security Gate",
      "Review Gate",
      "Done Gate"
    ],
    "workers": [
      "factory-orchestrator",
      "product-face",
      "frontend-builder",
      "qa-verification-worker",
      "independent-reviewer"
    ],
    "proofs": [
      "worker packets",
      "status snapshot",
      "Product Face result after implementation",
      "Receipt Five"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "loop_plan": {
    "$schema": "https://overkill-factory.dev/schemas/loop-plan.schema.json",
    "unit_of_work": "local web cockpit factory planning slice",
    "work_unit_contract_ref": "examples/local-web-cockpit-factory-slice/card.md",
    "verify": [
      "validate-card",
      "gate-report",
      "worker-packet",
      "status-snapshot"
    ],
    "review": [
      "independent review before any implementation claim"
    ],
    "reviewer_selection_ref": "reviewer_selection_plan",
    "rollback": "remove or revise the planning slice before implementation starts",
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ],
    "lanes": [
      "source",
      "product-face",
      "security",
      "implementation-after-gates",
      "verification"
    ],
    "order": [
      "source resolve",
      "Product SOT",
      "Method Contract",
      "Product Face Packet",
      "Security Plan",
      "worker packets",
      "implementation only after gates"
    ],
    "inputs": [
      "input-paper",
      "status snapshot schema",
      "Discord UX study gate"
    ],
    "workers": [
      "factory-orchestrator",
      "source-ledger-worker",
      "product-sot-planner",
      "product-face",
      "security-orchestrator",
      "frontend-builder",
      "qa-verification-worker",
      "independent-reviewer"
    ],
    "limits": [
      "no manual UI implementation in this card",
      "no private evidence publication",
      "no deployment"
    ],
    "timeouts": [
      "block after missing Product Face or security evidence"
    ],
    "budget": "no material spend",
    "access_required": [
      "repo local execution"
    ],
    "expected_evidence": [
      "gate report",
      "worker packets",
      "status snapshot"
    ],
    "stop_criteria": [
      "ready worker packets generated"
    ],
    "block_criteria": [
      "missing Product Face Packet",
      "missing security plan",
      "generic visual quality accepted",
      "raw private evidence requested"
    ]
  },
  "dependency_map": {
    "$schema": "https://overkill-factory.dev/schemas/dependency-map.schema.json",
    "dependencies": [
      "factory-status-snapshot schema",
      "Product Face Packet",
      "security architecture plan",
      "local browser proof tooling"
    ],
    "integration_points": [
      "factoryctl status-snapshot",
      "factoryctl worker-packet",
      "Product Face proof runner"
    ],
    "owners": [
      "factory-orchestrator",
      "product-face",
      "security-orchestrator"
    ],
    "blocked_when_missing": [
      "status snapshot contract",
      "Product Face visual quality review",
      "safe evidence ref policy"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "access_capability": {
    "$schema": "https://overkill-factory.dev/schemas/access-capability.schema.json",
    "execution_mode": "local_factory_planning",
    "capabilities": [
      "repo read/write in scoped branch",
      "local tests",
      "local browser proof after implementation"
    ],
    "missing_capabilities": [
      "real Product Face implementation evidence",
      "real independent review result"
    ],
    "forbidden_actions": [
      "deploy",
      "secret_access",
      "private_runtime_read"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "autonomy_readiness_packet": {
    "$schema": "https://overkill-factory.dev/schemas/autonomy-readiness-packet.schema.json",
    "execution_mode": "planning_only_until_workers_return",
    "accounts_ready": true,
    "tools_ready": true,
    "environment_ready": true,
    "cost_limit": "no material spend",
    "forbidden_actions": [
      "deploy",
      "secret_access",
      "manual_ui_acceptance"
    ],
    "rollback_path": "revert the planning slice before implementation starts",
    "human_gates": [],
    "required_resources": {
      "local": [
        "repo",
        "python",
        "factoryctl"
      ]
    },
    "resource_statuses": [
      {
        "resource": "factoryctl",
        "status": "available_for_gate_execution"
      }
    ],
    "approval_channel": "explicit human gate only when release or hosting is requested",
    "owners": [
      "factory-orchestrator"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "budget_contract": {
    "$schema": "https://overkill-factory.dev/schemas/budget-contract.schema.json",
    "budget_owner": "factory-orchestrator",
    "spend_limit": "no material spend for local planning",
    "remote_cost_allowed": false,
    "stop_when": [
      "remote proof requested without budget owner",
      "hosted deployment requested without operator approval"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "privacy_compliance_plan": {
    "$schema": "https://overkill-factory.dev/schemas/privacy-compliance-plan.schema.json",
    "privacy_scope": [
      "public-safe local fixtures",
      "structured evidence refs"
    ],
    "compliance_scope": [
      "open-source repo hygiene",
      "private evidence redaction"
    ],
    "data_classes": [
      "public fixture",
      "redacted evidence ref",
      "private runtime evidence outside repo"
    ],
    "forbidden_disclosures": [
      "private paths",
      "private Discord ids",
      "tokens",
      "raw logs",
      "private URLs"
    ],
    "reviewers": [
      "public-safety-gate",
      "security-orchestrator"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "control_tower_contract": {
    "enabled": true,
    "surface": "local_web_cockpit",
    "discord_bridge_required": false,
    "source_of_truth": "factory-status-snapshot",
    "must_show_staleness": true,
    "must_not_require_private_discord": true
  },
  "runtime_state_ref": "examples/local-web-cockpit-factory-slice/card.md#factory-status-snapshot-input",
  "project_projection": {
    "$schema": "https://overkill-factory.dev/schemas/project-projection.schema.json",
    "source_of_truth": "factory-status-snapshot",
    "phase": "F7",
    "blockers": [
      "implementation blocked until worker results exist"
    ],
    "next_steps": [
      "generate worker packets",
      "execute Product Face, security, QA and review workers"
    ],
    "confidence": "planning projection only",
    "pending_approvals": [],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ],
    "discord_is_source_of_truth": false
  },
  "production_readiness_plan": {
    "$schema": "https://overkill-factory.dev/schemas/production-readiness-plan.schema.json",
    "owner": "release-ops-worker",
    "release_boundary": "no release in planning slice",
    "rollback": "revert implementation branch if proof fails",
    "health_checks": [
      "local smoke",
      "Product Face proof",
      "security scan",
      "public safety scan"
    ],
    "monitoring": [
      "local render errors",
      "snapshot staleness warnings"
    ],
    "human_approval": "required before hosted publication"
  },
  "incident_support_plan": {
    "$schema": "https://overkill-factory.dev/schemas/incident-support-plan.schema.json",
    "support_owner": "release-ops-worker",
    "incident_triggers": [
      "private evidence leak",
      "stale state shown as fresh",
      "approval state ambiguity",
      "local server exposure beyond operator intent"
    ],
    "triage_steps": [
      "block release",
      "capture public-safe evidence",
      "revert or disable affected surface",
      "create learnback issue"
    ],
    "escalation": [
      "human gate for private leak or hosted exposure"
    ],
    "learnback_target": "factory_maturity_scorecard"
  },
  "user_docs_onboarding_plan": {
    "$schema": "https://overkill-factory.dev/schemas/user-docs-onboarding-plan.schema.json",
    "audience": [
      "external operator",
      "factory maintainer"
    ],
    "docs_required": [
      "local run guide",
      "snapshot input guide",
      "public/private evidence boundary",
      "troubleshooting stale state"
    ],
    "acceptance": [
      "operator can run locally without private server",
      "operator knows publishing is their responsibility"
    ],
    "public_safety": [
      "no private paths",
      "no private Discord ids",
      "no raw private screenshots"
    ]
  },
  "factory_maturity_scorecard": {
    "$schema": "https://overkill-factory.dev/schemas/factory-maturity-scorecard.schema.json",
    "result": "PENDING",
    "blind_spots": [
      "local web cockpit implementation has not run yet"
    ],
    "missing_coverage": [
      "real Product Face result",
      "real security scan result",
      "real independent review"
    ],
    "learnback_actions": [
      "turn any cockpit execution failure into factory improvement issue"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "verification_plan": {
    "$schema": "https://overkill-factory.dev/schemas/qa-verification-plan.schema.json",
    "checks": [
      "validate-card",
      "gate-report",
      "worker-packet",
      "status-snapshot",
      "public_safety_scan",
      "secret_safety_scan",
      "supply_chain_proof"
    ],
    "evidence_required": [
      "command output",
      "worker packet refs",
      "status snapshot ref"
    ],
    "blocked_when": [
      "card validation fails",
      "worker packets cannot be generated",
      "private evidence appears in public artifact"
    ]
  },
  "completion_audit": {
    "$schema": "https://overkill-factory.dev/schemas/completion-audit.schema.json",
    "result": "PENDING",
    "blocking_findings": [
      "implementation has not run",
      "Product Face result is missing by design for this planning slice",
      "Receipt Five remains pending until worker evidence exists"
    ],
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "reviewer_selection_plan": {
    "record_type": "reviewer_selection_plan",
    "changed_surfaces": [
      "ux",
      "frontend",
      "product-face",
      "security",
      "public-docs"
    ],
    "risk_effective": "R2",
    "executor_identity": "factory-orchestrator",
    "forbidden_reviewers": [
      "factory-orchestrator"
    ],
    "required_reviewers": [
      "product-face",
      "security-orchestrator",
      "independent-reviewer"
    ],
    "reviewer_matrix": [
      {
        "reviewer_worker": "product-face",
        "covers": [
          "visual quality bar",
          "state coverage",
          "anti-generic UI rejection"
        ],
        "reason": "The cockpit is a visible operator product surface.",
        "mandatory": true
      },
      {
        "reviewer_worker": "security-orchestrator",
        "covers": [
          "raw evidence boundary",
          "local server exposure",
          "approval confusion"
        ],
        "reason": "The cockpit can affect operator trust and private data boundaries.",
        "mandatory": true
      },
      {
        "reviewer_worker": "independent-reviewer",
        "covers": [
          "gate completeness",
          "evidence sufficiency",
          "scope discipline"
        ],
        "reason": "Executor cannot be sole reviewer.",
        "mandatory": true
      }
    ],
    "selection_rule": "Use Product Face, security and independent review before accepting implementation or completion.",
    "evidence_refs": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ]
  },
  "receipt_five": {
    "$schema": "https://overkill-factory.dev/schemas/receipt-five.schema.json",
    "changed": [
      "planning slice only"
    ],
    "artifact_paths": [
      "examples/local-web-cockpit-factory-slice/card.md"
    ],
    "verification_commands": [
      "python scripts/factoryctl.py validate-card examples/local-web-cockpit-factory-slice/card.md",
      "python scripts/factoryctl.py gate-report --card examples/local-web-cockpit-factory-slice/card.md",
      "python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/local-web-cockpit-factory-slice/card.md --out .tmp/local-web-cockpit-worker-packets",
      "python scripts/factoryctl.py status-snapshot --card examples/local-web-cockpit-factory-slice/card.md --out .tmp/local-web-cockpit-status-snapshot.json"
    ],
    "verification_result": "PENDING",
    "reviewer_required": true,
    "next_action": "Run worker packets through the factory runtime before implementation."
  }
}
```
