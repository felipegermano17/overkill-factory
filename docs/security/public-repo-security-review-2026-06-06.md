# Public Repository Security Review - 2026-06-06

Scope: public open-source repository review for methodology docs, factory
contracts, worker packet generation, public safety controls, adapter packaging,
and CI. This is a bounded single-agent review. It is not a full Codex Security
repository scan with separate threat-model, discovery, validation, attack-path
and final HTML artifacts.

## Executive Result

The repository is directionally strong for a public methodology project: it has
explicit security workers, public artifact rules, preflight tests, compatibility
markers, and a public-safety denylist scan in CI.

It is not yet a 10/10 public security posture. The main issue is proof depth:
current automation proves that key strings and contracts exist, not that every
security-sensitive path is robust under adversarial use, dependency risk,
workflow abuse, secret leakage, or adapter patch drift.

## Real Threats In This Repo

1. Private-context leakage into a public repo.
   The repo contains many generated docs, worker packets, pilot artifacts and
   screenshots. The real threat is not just a leaked credential; it is a local
   path, private source extraction, private board link, internal project name or
   personal identifier becoming durable public metadata.

2. False security approval.
   Worker results can carry `PASS` or `WAIVED`. The code has checks requiring
   evidence refs, but the wider repo still needs stronger proof that a waiver is
   time-bounded, owned, reviewed, and not treated as a pass.

3. Adapter drift.
   The Hermes adapter check is marker-based. It confirms the patch still
   contains important symbols, but it does not prove the patch applies cleanly to
   a fresh target or that transition gates still block real state changes.

4. Supply-chain and CI abuse.
   CI currently runs useful preflight commands, but it does not pin action SHAs,
   declare least-privilege workflow permissions, scan dependencies, produce an
   SBOM, or run a dedicated secret scanner.

5. Generated artifact sprawl.
   Worker packets and validation outputs are generated across many folders. A
   small redaction gap in a generator can create many public artifacts with the
   same unsafe value.

6. Agentic and memory poisoning.
   The methodology correctly identifies source separation and memory trust, but
   the public repo still needs executable checks that prevent raw source text or
   untrusted instructions from being promoted into worker contracts.

## Findings

### OF-SEC-001 - Angle-bracket source references can bypass path redaction

Severity: Medium

Affected surface: `scripts/factoryctl.py`, `source_card_ref`.

The source-card reference helper returns any value wrapped in angle brackets as
raw text. Normal outside-repo paths are converted to `external:<name>`, but an
angle-bracketed local path would be emitted unchanged into generated worker
packets.

Impact: a user or automation path can leak into public worker packet artifacts.
This is especially risky because packet generation is a high-volume operation.

Recommended fix: unwrap angle-bracket values, apply the same repo-relative or
`external:<name>` redaction logic, and add regression tests for angle-bracketed
absolute paths and benign symbolic placeholders.

Status: fixed after this review. Angle-bracket placeholders are now converted
to public-safe `external:<label>` references, and angle-bracketed paths or
drive-like strings are reduced to `external:source-card`.

### OF-SEC-002 - Public safety scan is useful but denylist-only

Severity: Medium

Affected surface: `scripts/public_safety_scan.py`, CI public-safety step.

The scanner catches known forbidden strings and local path markers in text
files, which is valuable. It does not detect unknown private names, high-entropy
secrets, private URLs, metadata in binary assets, or sensitive content inside
screenshots.

Impact: a clean public-safety scan is not a clean secret scan or privacy scan.

Recommended fix: keep the denylist, but add generic local-path patterns, private
URL patterns, token-like entropy checks, optional allowlist annotations for
intentional fixture terms, and a separate policy for binary assets.

### OF-SEC-003 - CI lacks supply-chain hardening

Severity: Medium

Affected surface: `.github/workflows/ci.yml`.

CI runs unit tests, adapter marker compatibility, and public-safety scan. It
does not set explicit workflow permissions, pin actions to immutable SHAs, run a
secret scanner, run dependency review, or produce SBOM/provenance evidence.

Impact: the repo can claim a supply-chain gate conceptually while the public CI
does not yet enforce the same control depth.

Recommended fix: add `permissions: contents: read`, pin or periodically audit
actions, add secret scanning, add dependency review, and add SBOM generation
once packaging metadata exists.

### OF-SEC-004 - Adapter compatibility proof is marker-only

Severity: Medium

Affected surface: `adapters/hermes/compatibility-check.py`.

The compatibility check searches for required markers in the patch and control
script. This prevents accidental deletion of core symbols, but it does not prove
patch application, importability after patch, or gate behavior in a disposable
runtime fixture.

Impact: a future patch can pass marker checks while failing to apply or enforce
blocking behavior.

Recommended fix: add a CI job that applies the patch to a known-compatible
fixture or checkout, runs transition gate tests, and records explicit failure
cases for ready and done transitions.

### OF-SEC-005 - Schema validation is not yet a first-class CI gate

Severity: Low

Affected surface: `schemas/`, generated validation artifacts.

Unit tests compare some enums and contract behavior, but CI does not validate
every JSON card, worker packet, result and receipt against its schema.

Impact: schema drift can hide in generated artifacts until a downstream runtime
or worker consumes them.

Recommended fix: add a repo-local schema validation command and run it in CI
over `examples/`, `validation/`, and pilot evidence that is intended to stay
public.

## Gaps To Reach 10/10

1. Full Codex Security scan artifacts for the public repo.
   Required: threat model, discovery worklist, validation notes, attack-path
   analysis, markdown report and HTML report.

2. Real supply-chain gate.
   Required: workflow permissions review, pinned action policy, dependency
   review, secret scan, SBOM/provenance or explicit waiver.

3. Disposable adapter proof.
   Required: apply patch, run gate tests, prove blocked transitions fail closed.

4. Stronger public-safety automation.
   Required: denylist plus generic patterns, secret-like token detection, private
   URL detection, binary asset policy, and regression tests for known leak
   shapes.

5. Exhaustive schema validation.
   Required: validate all public JSON artifacts against schemas in CI.

6. Waiver lifecycle enforcement.
   Required: owner, reason, evidence, compensating control, expiry and reviewer
   for every waiver.

7. Generated artifact controls.
   Required: generator tests that prove output paths are repo-relative or
   redacted before packet files are written.

## CI Checks To Add

- `python scripts/public_safety_scan.py`
- `python -m unittest discover -s tests -p "test_*.py" -q`
- `python adapters/hermes/compatibility-check.py`
- `python -m compileall -q scripts adapters/hermes tests`
- Schema validation over public JSON artifacts.
- Secret scan with a reviewed baseline.
- Dependency review and SBOM generation.
- Workflow permission check for least privilege.
- Adapter patch-apply and transition-gate regression test.
- Public binary asset policy check.

## Evidence From This Review

Commands run successfully:

- `python -m unittest discover -s tests -p "test_*.py" -q`
- `python adapters/hermes/compatibility-check.py`
- `python scripts/public_safety_scan.py`
- `python -m compileall -q scripts adapters/hermes tests`
- `python scripts/factoryctl.py validate-card validation/cards/public-repo-release-r2.md`
- `python scripts/factoryctl.py validate-card validation/cards/solana-quasar-r3.md`
- `python scripts/factoryctl.py validate-completion --card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md --receipt pilots/quasar-vault-guard-test/evidence/receipt-five-first-slice.json`

The generated gate report for `validation/cards/public-repo-release-r2.md`
correctly blocks missing security, cloud, release, supply-chain and monitoring
inputs. That is a good sign: the factory model routes risk. The remaining issue
is that public CI does not yet execute all those routed controls.

## Priority Recommendations

1. Add secret scan, dependency review, SBOM and workflow permission checks to CI.
2. Add schema validation for public JSON artifacts.
3. Replace marker-only adapter proof with a patch-apply gate test.
4. Expand `public_safety_scan.py` beyond known-name denylisting.
5. Keep generator redaction tests in place for worker packets and transition plans.
