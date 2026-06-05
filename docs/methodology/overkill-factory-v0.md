# Overkill Factory V0

Overkill Factory is a product-production line for autonomous agents.

It is designed for hostile inputs: raw papers, ambiguity, conflicting sources,
partial decisions, unfinished architecture, agent mistakes, and real execution
pressure.

## Non-Negotiable Rules

1. Source is not truth until it is resolved.
2. Planning is not execution authority.
3. Architecture must pass specialist review before decomposition.
4. Agents cannot approve their own work.
5. Product has a face: frontend, mobile, wallet, state and UX evidence are part
   of production.
6. Security is a gate, not a paragraph.
7. Onchain work is a separate risk surface.
8. R3/R4 work needs human authority.
9. Done requires Receipt Five.
10. Kanban state is controlled by gates, not confidence.

## Production Line

### F0 Source Intake

Accept the raw product paper and every relevant supporting source. Preserve
provenance. Do not optimize the idea yet.

Output: source ledger.

### F1 Source Resolution

Classify each source as raw, compiled, inference, promoted, rejected, or
backlog. Resolve contradictions explicitly.

Output: claims and conflict matrix.

### F2 Product SOT

Produce the Product Source of Truth. This is the operational product contract,
not a pitch deck.

Output: Product SOT candidate.

### F3 Understanding Alignment

Ask only questions that change the plan, risk, architecture, UX, delivery, or
execution path.

Output: decision packet.

### F4 Architecture Candidate

Design the product architecture from the SOT and constraints.

Output: architecture candidate.

### F5 Product Face

Define screens, states, wallet flows, breakpoints, accessibility, performance
budget, and visual evidence plan.

Why this is better than "frontend later": agents otherwise build invisible
systems and discover product reality too late.

Output: Product Face Packet.

### F6 Specialist Reviews

Route architecture through relevant specialists: security, cybersecurity,
Solana/Quasar, backend, frontend, QA, DevOps, data, compliance context, and CTO.

Output: review matrix and required remediation.

### F7 Onchain Package

For Solana/KAXIS work, create a Quasar-first onchain package: accounts,
instruction ABI, PDA derivation, CPI allowlist, compute-unit budget, authorities,
and Auditor path.

Output: Onchain Work Package.

### F8 Security Scan Plan

Define who scans, when, with which tool, over what scope, and what blocks
promotion.

Output: Security Scan Packet.

### F9 Human Architecture Gate

The human owner approves, rejects, or requests changes. Rework loops until the
architecture can safely become decomposition.

Output: approved architecture record.

### F10 Documentation OS

Turn approved architecture into operating documentation: specs, decisions,
contracts, diagrams, evidence paths, and test strategy.

Output: Documentation OS.

### F11 Decomposition

Break work into Kanban cards with owner worker, executor, reviewer, surfaces,
risk, runtime contract, security contract, forbidden actions, done definition,
verification, and expected evidence.

Output: gated Kanban card graph.

### F12 Execution

Agents execute bounded cards. They cannot expand scope, bypass gates, touch
forbidden surfaces, or mark done without receipts.

Output: implementation and evidence.

### F13 Verification

Run tests, scans, screenshots, Auditor, and domain checks required by the card.

Output: structured verification result.

### F14 Independent Review

A different reviewer validates work and evidence.

Output: approval, rejection, or remediation.

### F15 Human R3/R4 Gate

High-risk work requires explicit human gate records. Production-critical work
also requires rollback and risk owners.

Output: human gate approval or block.

### F16 Promotion

Only promote when evidence, review, security, rollback, and monitoring are
complete for the risk class.

Output: promotion packet.

### F17 Production Monitoring

Observe runtime health and product behavior after release.

Output: monitoring receipt.

### F18 Learning Loop

Update methodology and contracts from the real pilot.

Output: Factory VNext.

## Receipt Five

Every done transition must include:

1. What changed.
2. Where the artifacts are.
3. What was verified.
4. Who reviewed or why review is not required.
5. What happens next.

## Why This Beats a Normal Agile Board

Agile boards usually track work. Overkill Factory controls authority.

That distinction matters because autonomous agents can produce activity faster
than humans can notice weak assumptions. Gates protect the factory from speed
without evidence.
