# Evidence and Receipt Five

Overkill Factory treats evidence as the difference between progress and a claim.

## Why evidence matters

Agentic work can sound complete before it is complete.

A worker can say it implemented something. A reviewer can say it looks fine. A model can summarize a run. None of that is enough by itself.

The factory asks: what proves it?

## Evidence by work type

Different work needs different evidence.

### Code

Code evidence may include:

- tests;
- build;
- lint or typecheck;
- diff;
- runtime output;
- regression proof;
- relevant logs.

### Documentation

Documentation evidence may include:

- docs build;
- link validation where available;
- reading order;
- no internal artifacts in public docs;
- source/legacy separation;
- examples that match real commands;
- no stale claims about live proof.

### Product interface

Product interface evidence may include:

- screenshots;
- state coverage;
- viewport coverage;
- accessibility checks;
- loading, error and empty states;
- journey proof;
- product experience review.

### Security

Security evidence may include:

- threat/control notes;
- access review;
- secret scan;
- supply-chain scan;
- dependency review;
- specialist review;
- rollback owner;
- monitoring plan.

### Release

Release evidence may include:

- version;
- deployment target;
- rollback path;
- monitoring;
- owner;
- risk acceptance;
- release gate result.

### Onchain

Onchain evidence may include:

- domain-specific review;
- program/instruction checks;
- signer boundaries;
- funds boundaries;
- devnet/mainnet separation;
- explicit human authority where needed.

## Receipt Five

Receipt Five is the closure receipt.

It answers five questions:

1. What changed?
2. Where does it live?
3. How was it verified?
4. Who or what reviewed it?
5. What remains: release, block, operate, risk or learnback?

A run that lacks Receipt Five is not closed.

## What Receipt Five prevents

Receipt Five prevents vague “done” claims.

It prevents future agents from having to rediscover what happened. It prevents the operator from accepting a result with no evidence trail. It also makes honest blocking normal.

A blocked receipt is better than a fake success.

## Honest examples

Good closure:

```text
Changed: public documentation rewritten and old docs moved to legacy.
Where: docs/ and factory/legacy-docs/.
Verified: docs build, unit tests, public safety scan, secret scan.
Reviewed: automated checks and human review pending.
Remaining: live operator E2E proof not part of this docs PR.
```

Bad closure:

```text
Done. The docs are 100% fixed.
```

The second version hides where the work lives, how it was verified and what remains.
