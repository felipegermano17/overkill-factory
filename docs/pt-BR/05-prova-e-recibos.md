# Prova e recibos

A pergunta certa é: como eu sei que o agente não está só falando bonito?

A resposta começa por uma verdade incômoda: processo parecendo vivo não é a mesma coisa que progresso.

## Teatro de progresso

Teatro de progresso é quando atividade substitui entrega.

O worker diz “feito”, mas não aponta evidência. O teste passa, mas não cobre o pedido. A tela abre, mas quebra no erro. A revisão aprova, mas não leu o artefato. O humano aprova, mas não recebeu material. O board anda, mas a dependência real ficou fora do grafo.

A fábrica trata isso como falha central.

## Prova fraca e prova boa

Prova fraca:

```text
Teste passou.
```

Prova boa:

```text
O teste test_onboarding_email_error falhou antes da correção, passou depois e cobre exatamente o erro descrito no pedido.
```

Prova fraca:

```text
Screenshot anexado.
```

Prova boa:

```text
Screenshots mostram desktop, mobile, loading, erro, estado vazio e caminho feliz. Console sem erro.
```

Prova fraca:

```text
Review aprovado.
```

Prova boa:

```text
Reviewer independente leu o diff, apontou dois reparos, os reparos foram corrigidos, e a revisão final destravou o gate.
```

## Readback

Readback é reler antes de acreditar.

Se o worker disse que criou um documento, a fábrica lê. Se disse que anexou prova, abre. Se disse que rodou teste, confere comando e saída. Se disse que a interface ficou boa, olha a superfície.

Sem readback, a fábrica só acredita no worker.

## Review consumido

Review não é carimbo. Review bom muda estado.

Se passa, destrava. Se falha, cria reparo. Se aponta risco, registra dono. Se exige decisão, vira pacote humano. Se fica solto em comentário, não foi consumido.

## Receipt Five

No fim, você recebe um recibo de conclusão. Internamente ele pode aparecer como Receipt Five.

Ele responde:

1. O que foi pedido?
2. O que foi feito ou decidido?
3. Que prova sustenta isso?
4. Quem revisou e o que a revisão disse?
5. O que ainda falta, bloqueia ou fica como risco?

Se uma resposta importante está vazia, não está pronto.

## Prova por tipo de trabalho

Bug pede reprodução antes e depois.

Release pede prontidão, rollback, dono, janela e monitoramento.

Interface pede jornada, erro, vazio, loading, mobile, acessibilidade básica e console.

Segurança pede fronteira, ameaça, permissão, segredo, supply chain e risco residual.

Docs pedem clareza, navegação, primeiro sucesso e ausência de claim falsa.

## Prova local não é entrega viva

Um comando local passando prova que o checkout está coerente.

Um Hermes vivo prova que o trabalho existiu naquele runtime.

Um worker result prova que um worker devolveu algo naquele escopo.

Um Receipt Five bem formado prova que a conclusão foi reconciliada.

Essas coisas não são iguais. Smoke local não prova produto entregue. Arquivo existente não prova readback. Aprovação genérica não prova mainnet.
