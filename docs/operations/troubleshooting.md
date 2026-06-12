# Troubleshooting

When something fails, keep the factory moving by narrowing the failing contract.
Do not bypass a gate just to get a green status.

## `validate-card` Fails

Run:

```bash
python scripts/factoryctl.py validate-card <card>
```

Fix missing required fields first:

- `factory_method_version`;
- `phase`;
- `surfaces`;
- `risk_initial` and `risk_effective`;
- `runtime_contract`;
- `security_contract`;
- `forbidden_actions`;
- `done_definition`;
- `kanban_transition_event_ref`.

Then rerun `gate-report` to see which workers are required.

## Worker Packet Exists But Card Cannot Close

A worker packet is an assignment, not evidence. A done transition needs worker
results and Receipt Five.

Check:

- required worker result files exist;
- each result has `PASS` or a structured waiver where allowed;
- current evidence is not superseded by a later failing result;
- Receipt Five points to the same current evidence;
- reviewer and executor are different when review is required.

## Public Safety Scan Fails

Run:

```bash
python scripts/public_safety_scan.py
```

Remove or redact the reported public-boundary residue. Do not add allowlists for
real private material. Public docs should use role names, placeholders and
repo-relative paths.

## Secret Scan Fails

Run:

```bash
python scripts/secret_safety_scan.py
```

Rotate any real credential that was committed. Replace public examples with
short placeholders such as `example`, and keep real values in your private
runtime environment.

## Test Runner Or Sandbox Launch Fails

Keep the worker result blocked until the same command is proven. Record the
command as an argv list and rerun through the safest available local runner:

```bash
python -m unittest tests.test_factoryctl -q
```

Do not turn a shell launcher failure into a PASS. If the environment reports a
runner error such as `CreateProcessAsUserW failed: 5`, use the pattern in
`scripts/safe_shell.py` and record the result as `BLOCKED` with remediation.
Only a later successful run of the same argv can supersede that blocker.

## Hermes Patch Does Not Apply

Read `adapters/hermes/README.md` and rerun the patch check from a clean Hermes
checkout:

```bash
git apply --check <path-to-overkill-factory>/adapters/hermes/patches/0001-overkill-factory-v35-gates-official-main.patch
```

If it fails, compare the tested Hermes commit and your local Hermes version.
Treat that as adapter drift and run focused Hermes tests after rebasing the
patch.

## Discord Shows Progress But Repo Evidence Is Missing

Trust the repo evidence. Discord is only a cockpit. Rebuild the missing worker
result, human gate record or Receipt Five artifact, then point the Control Tower
message to that repo-relative ref.

## Release Readiness Looks Good But Completion Audit Fails

Run:

```bash
python scripts/factory_completion_audit.py --no-write --require-complete
```

The audit is allowed to be stricter than a status summary. Fix the missing lane,
stale evidence, wrong receipt field or public-safety blocker before claiming
completion.
