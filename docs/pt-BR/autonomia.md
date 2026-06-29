# Autonomia

Autonomia não é memória do modelo. Autonomia é recuperar a próxima ação segura a partir de estado durável. Hermes guarda o estado, contratos dizem o que pode avançar e no-idle acorda a fronteira: consome resultado válido, despacha trabalho pronto, cria reparo recuperável, espera dependência real ou emite bloqueio tipado. Operador só entra quando não existe ação autônoma segura.

## Regra principal

A fábrica deve facilitar confiança. Se algo não foi provado, deve ser dito como pendente. Se algo é reparável pela fábrica, não deve virar pergunta para o operador. Se exige decisão humana real, o gerente deve apresentar contexto, opções, consequências, recomendação e próximo passo.
