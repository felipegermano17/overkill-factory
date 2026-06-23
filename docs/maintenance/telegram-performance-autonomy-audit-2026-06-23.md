# Telegram Performance And Autonomy Audit

Status: public-safe factory product audit.
Date: 2026-06-23.

This audit hardens the factory for a Telegram-first operator experience without
weakening source, gate, security or runtime boundaries.

## Findings

1. Start was too contract-first and not conversational enough.
   Rich product material could move toward SOT too quickly, as if the factory
   had understood the product perfectly. Product starts now require a
   conversational start packet and operator understanding confirmation before
   Product SOT.

2. The operator interface was implicitly Discord-shaped.
   The factory now has an `operator_interface_profile` contract. Telegram,
   Discord, Cockpit, Codex bridge, CLI and API are channels. Hermes remains the
   durable runtime source of truth.

3. Telegram status could become passive polling.
   The interface profile now requires proactive notifications for decision
   required, gate blocked, worker batch completed and idle timeout detected.
   The operator must not need to repeatedly ask whether work advanced.

4. Short chat summaries were too shallow for major decisions.
   Important artifacts now need an `operator_briefing_package`: short message
   plus markdown and PDF attachments, with optional diagram, video and audio
   explainer slots. The short message is a projection only, not the decision
   surface.

5. Performance cannot mean global YOLO authority.
   Fast low-risk work remains possible through existing autonomy lanes, but
   production, funds, secrets, destructive actions, mainnet, release and risk
   acceptance still require explicit gates.

6. Solana routing must be deterministic.
   Solana/on-chain product signals route to the `solana-ai-kit-core` capability
   pack and domain-brain requirements before execution. This avoids relying on
   the operator remembering to say which Solana system to use.

7. The manager profile needed a channel-neutral permission class.
   `overkill-factory-gerente` is now an operator-interface profile, not a
   Discord-specific identity. It may talk, receive input, push status and attach
   briefings. It must not execute product work or mark cards done.

## Implemented Controls

- `schemas/operator-interface-profile.schema.json`
- `schemas/factory-start-conversation.schema.json`
- `schemas/operator-briefing-package.schema.json`
- `templates/operator-interface-profile.json`
- `templates/factory-start-conversation.json`
- `templates/operator-briefing-package.json`
- `factoryctl operator-interface`
- `factoryctl start-conversation`
- `factoryctl briefing-package`
- validation commands for all three contracts
- public artifact validation for proactive, polling-free, PDF-backed briefings
- regression tests for Telegram interface, start blocking and deep briefings

## Runtime Rule

Telegram may be the primary human interface, but it is not the source of truth.
The bot should push status and attachments from factory state. It should not
invent state, close gates, approve work, or ask the operator to coordinate
workers, schemas, packets or internal retries.

## Performance Rule

The fastest safe path is:

1. choose primary interface once;
2. hold a conversational start until understanding is confirmed;
3. hand the compiled confirmed material to the factory;
4. let the factory repair non-human blockers itself;
5. push only meaningful state changes or bounded human decisions;
6. send deep briefing packages for decisions instead of shallow chat summaries.

This removes bureaucracy without removing the evidence and gate structure that
keeps high-risk product work safe.
