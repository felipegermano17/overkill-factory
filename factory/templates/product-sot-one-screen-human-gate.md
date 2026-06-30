# Product SOT one-screen human gate template

Use this as the primary operator-facing message before/with attachments.

```text
Decisão pendente:
Aprovar ou corrigir a Product SOT de <produto>.

O que a SOT diz:
- <ponto essencial 1>
- <ponto essencial 2>
- <ponto essencial 3>
- <ponto essencial 4>

Se você aprovar:
<o que a fábrica pode fazer em seguida>.

Aprovar NÃO autoriza:
<ações sensíveis ainda proibidas: implementação/deploy/mainnet/fundos/secrets/custody/signing/etc>.

Responda uma destas:
1. Aprovo a SOT.
2. Não aprovo. Corrigir: ...
3. Ainda falta: ...

Anexos/ref:
- SOT completa
- manifest/readback
```

Rules:
- Keep the primary message one-screen and decision-grade.
- Attachments support review; they are not the primary UX.
- Do not lead with receipt, JSON, file paths, or process apology.
- Do not hide what approval does and does not authorize.
