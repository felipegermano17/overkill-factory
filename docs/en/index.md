# Overkill Factory

Overkill Factory is a product factory for agentic work on top of Hermes.

It is not a chatbot, a SaaS wrapper, or a second Hermes. Hermes owns the runtime floor: boards, cards, dependencies, typed blocks, dispatch, worker execution, comments, logs, and state transitions. Overkill Factory owns the production method: intake, source truth, product definition, method selection, gates, worker authority, evidence, review, release decisions, and learnback.

The public kernel in this repository is version `3.0.2`. The executable surface currently contains 26 compiled phases, 14 route classes, 8 method engines, 17 operating-system areas, 40 public workers, 244 schemas, 156 templates, and 97 tests.

## The shortest useful explanation

A request enters the factory. The factory does not immediately ask an agent to build. It first protects the source, understands the material, confirms the product truth, chooses the right method, checks risk and capability, turns the work into bounded units, dispatches specialist workers through Hermes, demands evidence, reviews the result, and only then releases, blocks, or learns.

```text
source -> understanding -> product truth -> method -> plan -> work units
-> Hermes workers -> evidence -> review -> release or block -> learnback
```

The point is not to slow agents down. The point is to make speed trustworthy.

## Who this documentation is for

Read this if you are:

- an operator who wants to run product work through the factory;
- a technical investor or partner trying to understand the system;
- a non-technical reader who wants the idea without internal jargon;
- an engineer who needs to inspect or contribute to the public kernel;
- an agent that must continue work without relying on private chat memory.

## Reading path

1. **Manual** explains the product and mental model.
2. **Operating Model** explains the factory in motion.
3. **Lifecycle** explains every compiled phase.
4. **Trust and Evidence** explains how the factory avoids fake progress.
5. **Technical Model** explains the implementation.
6. **Usage** gives the commands for a first local proof.
7. **Reference** collects terms, commands, paths, and registries.

Portuguese version: [Português](../pt-BR/index.md).

## First local proof

From a checkout of this repository:

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

A passing local proof means the public kernel and example path are coherent. It does not mean a real operator-owned Hermes runtime has delivered a specific product. Real product delivery still requires Hermes runtime state, worker results, readback, review, Receipt Five, and any required human gate.
