# Estrutura do repositório

A raiz pública deve ficar pequena: README.md, LICENSE, .github/, docs/ e factory/. `docs/` é documentação humana pública. `factory/` é implementação: scripts, schemas, templates, adapters, agents, skills, testes, examples, fixtures e contratos. Documentação antiga fica separada em `factory/legacy-docs/` somente quando ainda tem valor técnico.

## Regra principal

A fábrica deve facilitar confiança. Se algo não foi provado, deve ser dito como pendente. Se algo é reparável pela fábrica, não deve virar pergunta para o operador. Se exige decisão humana real, o gerente deve apresentar contexto, opções, consequências, recomendação e próximo passo.
