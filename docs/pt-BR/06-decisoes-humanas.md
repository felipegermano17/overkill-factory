# Decisões humanas

A fábrica não deve chamar o humano porque ficou preguiçosa. Ela deve chamar o humano quando a autoridade é humana.

## Quando o humano é obrigatório

Humano entra para produção, mainnet, fundos, segredos, orçamento, release, waiver, risco residual, mudança de autoridade e qualquer ação em que a consequência não pode ser delegada ao worker.

Nesses casos, a Factory prepara um pacote de decisão. O operador decide. A fábrica registra.

## Quando não é decisão humana

Não é decisão humana quando falta readback, anexo, worker result, revisão consumida, prova formatada, status atualizado ou reparo interno.

Isso é obrigação da fábrica. Jogar isso no operador transforma controle em teatro.

## Pedido ruim

```text
Posso seguir para produção?
```

Esse pedido não diz o que está sendo aprovado, que prova existe, que risco sobra nem o que acontece se a pessoa disser não.

## Pedido bom

```text
Você está aprovando o deploy do onboarding v2 para staging.

Inclui:
- cadastro;
- validação de email;
- tela de erro;
- fallback de loading.

Não inclui:
- KYC;
- pagamento;
- convite por equipe;
- produção.

Provas:
- build 1842;
- testes de onboarding;
- screenshots desktop/mobile;
- revisão independente sem bloqueio.

Risco restante:
analytics de abandono ainda não instrumentado.

Se aprovar:
faço deploy em staging.

Se recusar:
mantenho bloqueado e abro reparo de escopo.
```

Isso é gate humano de verdade.

## O que aprovação autoriza

A aprovação autoriza o próximo passo declarado, naquele escopo, com aquelas provas e riscos.

Ela não autoriza escopo novo, produção se o pedido era staging, mainnet se o pedido era devnet, gasto se o pacote não mostrou custo, nem risco que não foi apresentado.

## Registro

Decisão humana precisa deixar rastro: quem decidiu, quando, sobre qual artefato, com que opções, com que consequência e com que risco residual.

Sem isso, a operação depende de memória de chat. Memória de chat não é gate.
