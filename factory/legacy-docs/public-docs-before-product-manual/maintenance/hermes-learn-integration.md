# Hermes /learn Integration

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: Hermes `/learn`, `factory_learning_proposal`,
> `skill-eval-distiller`, Factory Mechanic, tests.
> Runtime boundary: `/learn` can draft or stage a skill candidate. It does not
> activate factory behavior, approve gates, dispatch Hermes or rewrite the
> methodology by itself.

## Purpose

Hermes `/learn` is useful when a repeated workflow, correction or operational
path should become a reusable skill. It turns a described source into a
standards-guided skill-writing turn: a directory, URL, pasted notes or the
current conversation can become one `SKILL.md` through Hermes `skill_manage`.

Inside Overkill Factory, `/learn` is not a second self-improvement system. It is
a capture lane for a possible skill. Factory Mechanic and
`skill-eval-distiller` still own promotion, validation, review and activation.

## Safe Role

Use `/learn` only for candidate skill distillation:

```text
operator or worker observes repeated workflow
-> learnback or plan-review finding
-> factory_learning_proposal classification=skill
-> optional Hermes /learn draft or staged skill write
-> tests or eval fixtures
-> independent review
-> public-safety and secret-safety checks
-> explicit activation policy
-> activation or rejection
```

The output of `/learn` may be attached to a learning proposal as a candidate
artifact reference. The proposal remains the factory source of truth for why
the skill should exist, how it is validated and whether it can become active.

## Hard Boundaries

`/learn` must not:

- auto-activate a skill;
- create or change gates, hooks, workers, MCP/tool bindings, install profiles or
  route registries;
- dispatch Hermes cards or close human gates;
- publish private source material, local paths, raw logs, screenshots,
  Discord/Telegram ids or secrets;
- turn one successful run into a general factory rule without evidence;
- bypass `factory_learning_proposal`, independent review or activation policy.

Sensitive domains such as production, credentials, custody, mainnet, funds,
legal, privacy, billing, hardware, hooks, MCP/tooling and install profiles need
explicit human gate before mutation.

## Gateway Configuration

For operator-facing profiles, keep Hermes skill writes gated:

```yaml
skills:
  write_approval: true
```

With this enabled, `/learn` can still prepare the candidate, but writes land in
Hermes pending skill review instead of silently changing the active skill set.
The operator or maintainer reviews with the Hermes `/skills pending`,
`/skills diff <id>`, `/skills approve <id>` and `/skills reject <id>` flow.

In short: `/learn` must not activate skills; it only prepares reviewable
candidates, and operator profiles should enforce `skills.write_approval: true`.

## Telegram And Bridge Behavior

When the primary interface is Telegram, `/learn` is acceptable only when the
operator explicitly asks the factory to learn from a bounded workflow or when a
reviewed Factory Mechanic proposal asks for a skill draft.

The bridge may forward a learning signal, but it must not run `/learn` as an
implicit background habit. Proactive status updates should report that a skill
candidate is pending review; they should not ask the operator to approve broad
methodology changes from a chat summary.

## Verification

A `/learn` integration is acceptable only when these checks pass:

```bash
python factory/scripts/validate_public_json_artifacts.py
python -m unittest tests.test_factory_self_improvement -q
python -m unittest tests.test_open_source_docs -q
python factory/scripts/public_safety_scan.py
python factory/scripts/secret_safety_scan.py
```

Runtime owners should also verify Hermes itself:

```bash
hermes version
hermes doctor
hermes gateway status --system
python -m pytest -q factory/tests/agent/test_learn_prompt.py
```

Those Hermes commands prove the runtime supports `/learn`. They do not replace
factory proposal validation or activation review.
