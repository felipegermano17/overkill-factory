# Human Gate Delivery

Human gates are artifact-first. A gate package that asks for approval without delivering the actual artifact under review is invalid.

The gerente must send the decision package before asking for a decision. For Product SOT review, architecture review, Product Face review, security/risk review, release review, or any similar artifact review, the package must include the artifact itself or a faithful owner-readable projection plus the complete artifact as attachment/reference. A summary-only approval packet is not a valid operator package.

The primary operator surface must be a one-screen decision memo, not a dump. Attachments may carry the full artifact, but the first Telegram/Desktop message must stand on its own.

A gate is valid only when the operator receives:

- decision requested in the first lines;
- plain-language summary of the artifact under review;
- what approval authorizes next;
- what approval explicitly does NOT authorize;
- allowed replies/options;
- consequences of each option when material;
- evidence refs/attachments as supporting material, not primary UX;
- urgency;
- next safe action;
- Telegram/Desktop-safe fallback;
- delivery receipt requirement.

Invalid gate UX:

- formal approval cover sheet without the reviewed artifact;
- raw JSON as primary content;
- local paths as the main thing the operator must inspect;
- PDF/attachment-first delivery without a readable decision memo;
- long defensive/process explanation before the actual decision;
- asking the operator to inspect Kanban or request the material.

Raw JSON is never the operator-facing gate.

Attachment quality rule:

- The primary attachment for an artifact-review gate must be an operator-grade PDF or equivalent designed artifact.
- JSON manifests are internal evidence/readback, not operator review attachments unless the operator explicitly asks.
- A PDF that is just monospace/plain-text fallback is not acceptable for normal Product SOT, architecture, release or security gates.
- Fallback TXT/PDF renderers are allowed only as emergency accessibility/readback fallback and must be labeled as fallback, not as the primary gate artifact.
- Product-grade gates must preserve hierarchy, sections, decision options, scope-in/scope-out, forbidden authorizations and evidence pointers in a readable designed layout.

The canonical package is:

`factory/templates/human-gate-decision-package.json`

The fallback renderer is:

`python3 factory/scripts/render_human_gate_pdf.py`

A low-risk planning step must not become a human gate by default. A gate is for
material authority, release, secrets, funds, mainnet, production, R3/R4 or other
explicitly authority-bearing decisions.
