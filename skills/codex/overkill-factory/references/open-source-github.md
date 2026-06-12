# Open Source GitHub Stewardship

Use this reference when the Overkill Factory public repository itself is the
product surface: README, quickstart, folder architecture, examples, CI,
release hygiene, public safety, or comparisons with other open-source repos.

## Core Standard

The public repository must help an external operator understand and run the
factory without private context.

Treat GitHub as product onboarding, not as proof storage. The repo is for
understanding, installing, running, validating, contributing and extending the
factory. It is not for raw evidence, historical test output, internal journey
notes, screenshots, private ledgers, local paths, or context-lock material.

## First-Value Bar

A professional open-source repo should make first value binary and fast:

- clone or install path is visible from the README;
- one minimal runnable example exists;
- one validation command proves the example path;
- the user can tell what Hermes provides and what the factory provides;
- optional runtime integrations are clearly optional;
- first useful output should be reachable in about ten minutes on a clean
  machine, or the README must honestly say why not.

## Folder Burden Test

For every top-level folder, answer these before keeping it public:

| Question | Keep Only If |
| --- | --- |
| Why does this folder exist? | It has a clear public product purpose. |
| Who opens it first? | A real user, contributor, operator, or maintainer has a reason. |
| What is its source of truth? | It is executable, canonical, or generated from a canonical source. |
| How is it validated? | CI, tests, scanners, schema validation, or documented manual check cover it. |
| Can it drift? | Drift is prevented by tests, generation, or a single-maintainer rule. |

If a folder fails the test, choose one: merge it into a clearer folder, generate
it from a contract, move it to examples, move it to private/local artifacts, or
delete it.

## Public Surface Rules

- Prefer a small number of strong public surfaces over many weak folders.
- Do not commit evidence archives, generated run outputs, old pilot proof,
  private history, local workspace paths, or raw extraction material.
- Do not create partial manual mirrors of registries, schemas, workers, or
  templates. Partial mirrors rot. If human docs are needed, cover the full
  public set or generate them from the canonical contract.
- Examples must be representative, public-safe and runnable. They should not
  feel like leftover internal validation artifacts.
- Scripts should converge toward the public CLI or documented maintainer tools.
  Avoid making users browse many script names to discover the product.
- Schemas and templates are allowed to be numerous only when grouped, named and
  documented through a user path. Raw contract mass is not onboarding.
- Public docs must answer external-user questions before internal process
  questions.

## Professional Open-Source Checklist

Check these when assessing quality:

- README states what it is, who it is for, what it does, what it does not do,
  and how to get first value.
- Quickstart is linear and tested.
- Minimal example is small, public-safe and aligned with real gates.
- License, security policy, contributing guide and issue/PR templates exist.
- CI runs the real public path, not old pilot evidence.
- Secrets and public-boundary scans pass.
- Folder map matches actual usage.
- Agent/worker docs are complete, generated, or explicitly secondary to the
  registry.
- Release state is verified on `origin/main` when publishing or merging matters.

## Hard Blockers

Block or revise when:

- the README cannot get a newcomer to first value;
- a top-level folder cannot justify its public existence;
- generated proof or historical evidence is committed as product content;
- private paths, names, board links, raw logs or secrets leak;
- CI passes only because it avoids the real public path;
- agent docs are partial mirrors of registry data;
- a public claim is not supported by code, tests, schema, CI, or a current
  source reference.
