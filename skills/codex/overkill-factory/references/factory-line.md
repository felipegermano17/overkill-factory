# Factory Line

## Phases

F0 Source Intake: collect raw product paper and supporting material.

F1 Source Resolution: classify raw facts, claims, conflicts, decisions, and
inferences.

F2 Product SOT: create the Product Source of Truth.

F3 Understanding Alignment: ask only questions that affect risk, architecture,
product, or execution.

F4 Architecture Candidate: design the product from SOT and constraints.

F5 Product Face: define screens, states, wallet flows, mobile, accessibility,
performance, and visual evidence.

F6 Specialist Reviews: route architecture to relevant specialists.

F7 Onchain Package: for Solana/Quasar, define accounts, ABI, PDA, CPI,
compute-unit budget, authorities, and Auditor path.

F8 Security Scan Plan: define scanner, timing, scope, required tools, and
blocking policy.

F9 Human Architecture Gate: human approval loop before decomposition.

F10 Documentation OS: turn approved architecture into durable specs and
evidence paths.

F11 Decomposition: create gated Hermes cards.

F12 Execution: agents execute bounded work.

F13 Verification: tests, scans, screenshots, Auditor, and domain checks.

F14 Independent Review: reviewer must differ from executor.

F15 Human R3/R4 Gate: high-risk approval and rollback ownership.

F16 Promotion: promote only with evidence, review, security, rollback, and
monitoring.

F17 Production Monitoring: observe release health.

F18 Learning Loop: generate Factory VNext.

## Gate Principle

Every phase produces an artifact that the next phase can inspect. If the next
phase depends on unstated assumptions, the previous phase is incomplete.
