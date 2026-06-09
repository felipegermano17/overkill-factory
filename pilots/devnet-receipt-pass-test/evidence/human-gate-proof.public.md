# Human Gate Proof Boundary

Decision recorded: validation-only approval.

Public-safe proof:

- The public repository records the approved and forbidden scope.
- The active operator authorization exists outside this public artifact set.
- The gate is not reusable for production, deploy, signing, write access,
  custody, funds or secrets.

Why this shape is better than embedding the source authorization:

- It avoids publishing private conversation or identity data.
- It keeps the public artifact honest about what can be replayed.
- It prevents future agents from treating this pilot as production approval.
