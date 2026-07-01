# Status, boundaries, and proof

This page separates public contract, local proof, live runtime, and real delivery.

## What the public repo proves

The public repo proves a verifiable kernel: compiled workflow, route classes, method engines, operating-system areas, schemas, templates, worker registries, scripts, fixtures, examples, docs, and tests.

In the current checkout, registries expose 26 compiled phases, 14 route classes, 8 method engines, 17 operating-system areas, and 40 public workers. The filesystem currently contains 249 JSON schemas, 161 JSON templates, and 101 test files.

Those numbers should be updated by tools, not guessed.

## What documentation proves

Documentation proves the explained contract and public navigation. It does not prove private execution.

## What the visual map proves

The visual map is conceptual support. It helps explain the factory. It is not the runtime source of truth, does not prove delivery, and does not replace Hermes.

## What local tests prove

local tests prove checkout coherence. `factoryctl doctor` and `factoryctl run minimal` indicate that the public kernel can operate locally.

That does not prove a real board ran, a current worker delivered, review was consumed, or a human approved.

## What live Hermes proves

Live Hermes proves runtime state: cards, transitions, dependencies, attachments, comments, and workers in that environment.

Even that still needs evidence and Receipt Five to become a conclusion.

## What worker result proves

Worker result proves a worker returned something in a scope. The factory still needs readback, review, and reconciliation.

## What Receipt Five proves

Receipt Five proves request, delivery, evidence, review, and remaining risk were reconciled. If a human gate was required, it must point to real human decision.

## Forbidden claims

Do not claim public documentation is runtime proof. Do not say the map proves production. Do not say local tests prove delivery. Do not say file creation proves readback. Do not say generic approval proves mainnet.
