# Official Hermes Head Recheck

Date: 2026-06-06

## Purpose

Check whether the official Hermes repository has moved since the latest
official-main adapter smoke.

## Source

- Repository: `NousResearch/hermes-agent`
- Live command: `git ls-remote https://github.com/NousResearch/hermes-agent.git HEAD`
- Observed HEAD: `56236b16e383cc656bb8c88429902f4de83f1faf`
- Previously tested commit: `56236b16e383cc656bb8c88429902f4de83f1faf`

## Result

`PASS`: official HEAD has not moved since the adapter smoke recorded in
`validation/hermes-live/official-main-patch-smoke.md`.

No new compatibility smoke was required in this pass because the upstream commit
is unchanged. If upstream HEAD changes, rerun the disposable compatibility smoke
before accepting any Hermes runtime update.
