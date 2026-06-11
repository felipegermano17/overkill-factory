# Operator Control Tower Private Evidence Kit

This kit describes the private evidence needed to pass the Operator Control
Tower production gate without leaking Discord, runtime, URL, path, token or raw
log material into the public repository.

It does not replace the canonical method. It only explains how to collect the
private proof for the current production blocker.

## Required Private Files

Create these files outside the public repository:

```text
discord-control-tower-mapping.json
runtime-approval-event.json
bridge-health.json
```

To initialize the private bundle without hand-writing the files:

```bash
python scripts/operator_control_tower_private_evidence_init.py \
  --out-dir /private/path/to/operator-control-tower-evidence
```

The initializer creates schema-valid placeholders. They are not production
proof. The doctor must still block until real cockpit/runtime evidence replaces
the placeholder values.

The public command accepts their private paths:

```bash
python scripts/operator_control_tower_proof.py \
  --mapping /private/path/to/discord-control-tower-mapping.json \
  --runtime-registration-event /private/path/to/runtime-approval-event.json \
  --bridge-health /private/path/to/bridge-health.json
```

The command writes only public-safe receipts.

Before running the production proof, use the private evidence doctor:

```bash
python scripts/operator_control_tower_private_evidence_doctor.py \
  --mapping /private/path/to/discord-control-tower-mapping.json \
  --runtime-registration-event /private/path/to/runtime-approval-event.json \
  --bridge-health /private/path/to/bridge-health.json
```

The doctor writes only a public-safe readiness report:

```text
validation/control-tower/operator-control-tower-private-evidence-doctor.json
```

If the doctor is `BLOCKED`, do not run the production proof as if the gate had
passed. Fix the private evidence first.

## File 1: Mapping

Use:

```text
templates/discord-control-tower-mapping.json
```

The private mapping must prove:

- the real owner cockpit exists;
- the project id is real and matches the runtime approval event;
- the runtime or board reference is real;
- the dashboard message exists;
- the approval channel exists;
- the bot health channel exists;
- the mapping points back to the selected runtime or board;
- placeholder values such as `redacted-*`, `example-*`, `todo`, `tbd` or
  `unknown` were not used as proof.

## File 2: Runtime Approval Event

Use:

```text
templates/control-tower-event.json
```

For the production proof, the private event must show a structured owner
decision that can be registered by the runtime:

```json
{
  "event_type": "approval_recorded",
  "source": "bridge"
}
```

The event must represent a real registration path. A message that exists only
in Discord is not enough.

The event must also have:

- a real event id;
- a project id equal to the mapping project id.

## File 3: Bridge Health

Use:

```text
templates/operator-control-tower-bridge-health.json
```

To pass, the private file must use:

```text
schemas/operator-control-tower-bridge-health.schema.json
```

And all checks must be true:

- bot reachable;
- bridge reachable;
- runtime readback reachable;
- approval registration path reachable;
- Discord is not the source of truth;
- public receipt contains no private material.

The file must also include non-empty external evidence refs. Placeholder refs
such as `redacted-*`, `example-*`, `todo`, `tbd` or `unknown` do not prove
production readiness.

A generic JSON file with only `result: PASS` is not valid proof.

## Expected Public Outputs

When the evidence is real and passes, the harness writes:

```text
validation/control-tower/operator-control-tower-production-readiness.json
validation/hermes-production-proof/operator-control-tower.json
```

If any real proof is missing, the public readiness receipt must stay
`BLOCKED`.

## Safety Rules

- Do not commit the private evidence files.
- Do not paste raw Discord ids, private runtime ids, URLs, webhooks, tokens or
  logs into public docs.
- Do not treat Discord as canonical state.
- Do not mark the production update receipt as `PASS` until this proof passes.
- Rerun public-safety and secret-safety scans before publishing.
