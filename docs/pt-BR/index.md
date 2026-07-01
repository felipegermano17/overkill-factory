# Overkill Factory

A Overkill Factory é uma fábrica para trabalho com agentes. Ela existe para uma situação bem concreta: você pede algo importante, o agente começa a trabalhar, tudo parece andar, mas ninguém consegue provar com segurança que o produto certo ficou pronto.

A fábrica tenta resolver isso sem transformar o operador em fiscal. O pedido entra. A fonte é preservada. A fábrica entende o produto, escolhe o caminho, divide o trabalho, roda pelo Hermes, cobra prova, revisa e só então entrega, bloqueia ou aprende.

O objetivo é tornar a velocidade confiável. Não é fazer o agente correr mais; é fazer a corrida deixar rastro, prova e responsabilidade.

Isso é produção controlada.

## Leia como uma conversa

Se você só quer entender o produto, leia assim:

1. [Manual](manual.md): o que é a fábrica e por que ela existe.
2. [Como a fábrica trabalha](operating-model.md): o que acontece com um pedido por dentro.
3. [Confiança e evidência](trust-and-evidence.md): como saber que "pronto" não é teatro.
4. [Ciclo da fábrica](lifecycle.md): o caminho simples da ideia até entrega, bloqueio ou aprendizado.

Depois disso, se quiser rodar ou manter o projeto:

- [Uso](usage.md): comandos locais e fronteira do que eles provam.
- [Modelo técnico](technical-model.md): como Hermes, workers, bindings, schemas e validadores se encaixam.
- [Referência](reference.md): nomes, caminhos e comandos para consulta rápida.

## A versão curta

A fábrica não deixa um agente sair fazendo só porque a tarefa parece clara.

Ela precisa saber:

- qual era a fonte;
- que produto está sendo construído;
- que tipo de trabalho é;
- quem pode executar;
- quem pode aprovar;
- que prova precisa voltar;
- o que acontece se a prova não vier.

Sem isso, velocidade vira chute.

## A fronteira honesta

O kernel público atual está na versão `3.0.2`. Ele expõe 26 fases compiladas, 14 classes de rota, 8 motores de método, 17 áreas de sistema operacional da fábrica, 40 workers públicos, 244 schemas JSON, 156 templates JSON e 97 arquivos de teste.

Esses números não são promessa de que qualquer produto privado foi entregue. Eles provam que existe um kernel público testável. Entrega real ainda precisa de Hermes vivo, worker results atuais, evidência específica do produto, revisão consumida e decisão humana quando o risco pedir.

## Primeira prova local

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

Se isso passa, o checkout local está coerente. Ainda não significa que uma execução real terminou.

## O que ficou fora da navegação principal

A documentação antiga continua em `factory/legacy-docs/`. Ela tem histórico e detalhe técnico útil, mas não é mais a explicação pública principal. A ideia desta seção em português é ser legível primeiro. O detalhe vem depois.
