# Source Capture Policy

Overkill Factory studies external material, but the public repository stores
only public-safe decisions and reusable methodology.

## Source Order

Use this order before recapturing anything:

1. Existing local source artifacts.
2. Existing extraction folders or source ledgers.
3. Project memory, wiki or durable context.
4. Authenticated browser recapture only for missing, stale or disputed sources.

## Public Repository Boundary

Do not store these in the public repository:

- raw social-post extraction;
- screenshots of private sessions;
- private source ledgers;
- private board ids, task ids, paths or runtime names;
- internal product names;
- local machine paths;
- private Whimsical workspace links;
- full copied source text when a public URL and distilled decision are enough.

The public repository may store:

- source URLs;
- source status;
- distilled operational implications;
- rejection reasons;
- reusable gates, worker contracts and checklists.

## Claim Discipline

Every claim must be labeled as one of:

- `confirmed_source`: directly supported by a public source or durable private
  source ledger;
- `inference`: a conclusion drawn from sources;
- `factory_decision`: an adopted Overkill rule;
- `rejected`: studied but not adopted.

If a source had access problems, do not present its contents as confirmed until
the source or prior extraction is resolved.

## Why This Is Better

This protects the open-source project from leaking internal context while still
keeping decisions traceable. Agents can use the public repo safely, and private
research can remain richer without becoming public baggage.
