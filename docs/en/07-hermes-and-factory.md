# Hermes and the Factory

Hermes and Overkill Factory do not do the same thing.

Hermes is the live runtime. The Factory is the production contract around it.

## What Hermes holds

Hermes holds cards, status, workers, dependencies, comments, attachments, workspaces, blockers, transitions, and completed states.

Living work must appear there. If real execution exists, it belongs in Hermes.

## What the Factory defines

The Factory defines routes, methods, gates, worker packets, worker results, evidence requirements, Receipt Five, forbidden authority, readback, review, and blocking policy.

It must not create a hidden second board. Parallel state becomes a source of lies.

## Why the split matters

If Hermes tries to decide everything alone, it becomes a Kanban board with too much confidence.

If the Factory stores live state outside Hermes, it becomes a hidden mini-Hermes.

The right boundary is: Hermes shows the floor; the Factory defines production discipline.

## No-idle

No-idle detects dangerous silence.

If work is ready, dispatch. If there is a real dependency, wait. If human decision is required and the packet is ready, call the operator. If readback, artifact, review, or evidence is missing, repair.

No-idle does not invent authority, approve gates, complete cards, or use the operator as a trash bin for internal blockers.

## Adapters and gates

Adapters and hooks may carry context and block unsafe transitions. They must not treat file presence as pass, close cards without Receipt Five, or promote workers without routes.

## Hermes profiles

Hermes profiles materialize worker roles. Profile names alone are not enough. A worker needs registry, profile, permission class, binding, packet route, and validation.

The public profile source is `agents/hermes-profile-bindings.public.json`. Live readiness still requires fresh smoke/eval when someone wants to claim runtime readiness.
