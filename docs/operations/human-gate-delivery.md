# Human Gate Delivery

Human gates are artifact-first.

The gerente must send the decision package before asking for a decision. A gate
is valid only when the operator receives:

- executive summary;
- context;
- decision requested;
- options;
- consequences;
- approved scope;
- forbidden scope;
- evidence refs;
- urgency;
- next safe action;
- Telegram/Desktop-safe fallback;
- delivery receipt requirement.

Raw JSON is never the operator-facing gate.

The canonical package is:

`factory/templates/human-gate-decision-package.json`

The fallback renderer is:

`python3 factory/scripts/render_human_gate_pdf.py`

A low-risk planning step must not become a human gate by default. A gate is for
material authority, release, secrets, funds, mainnet, production, R3/R4 or other
explicitly authority-bearing decisions.
