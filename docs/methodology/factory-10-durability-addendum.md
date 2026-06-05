# KAXIS Factory 10 Durability Addendum

Data: 2026-06-05  
Objetivo: tirar a Factory 10 do estado de patch validado e transformar em codigo versionado, testado e pronto para promocao.

## Resultado

A Factory 10 agora esta commitada no repositorio Hermes da VM.

```text
repo: /srv/hermes/home/hermes-agent
branch: codex/kaxis-factory-10-gates
commit: d297c0c78900d6858384297895ef4392e6fb85b9
summary: Add KAXIS Factory 10 kanban gates
```

Arquivos versionados:

```text
hermes_cli/kanban_db.py
hermes_cli/main.py
tests/hermes_cli/test_kaxis_factory_v35_gate.py
```

Patch de promocao:

```text
/srv/hermes/home/context-lock/kaxis-factory-10-runtime/patches/0001-add-kaxis-factory-10-kanban-gates.patch
sha256: 62dbe4155c0a5e6e9869f62c7104e2db63663ea38aae3a071b803ff369cfd725
```

Copiado tambem para:

```text
C:\Users\felip\OneDrive\Documentos\Kaxis VM\KAXIS_FACTORY_10_RUNTIME_2026-06-05\patches\0001-add-kaxis-factory-10-kanban-gates.patch
```

## Testes Adicionados

Arquivo novo:

```text
tests/hermes_cli/test_kaxis_factory_v35_gate.py
```

Cobertura:

1. Product Face Packet obrigatorio para `ux/frontend/mobile/wallet-ui`.
2. Bloqueio de executor revisando o proprio trabalho.
3. Security surface exigindo pacote Codex Security/Cybersecurity.
4. Done gate exigindo `security_scan_result` quando o card exige scan.
5. Onchain R3 exigindo Auditor ou waiver humano.
6. Onchain R3 com Auditor + scan podendo chegar a `ready`.
7. R4 exigindo `r4_gate`.
8. R4 com `r4_gate` satisfazendo ready contract.
9. `hermes_cli.main.main()` propagando exit code `1` quando o Kanban bloqueia uma promocao.

## Validacao Rodada

Comando:

```bash
venv/bin/python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_kaxis_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py
```

Resultado:

```text
72 passed in 3.53s
```

Outras validacoes:

```text
py_compile hermes_cli/kanban_db.py hermes_cli/main.py tests/hermes_cli/test_kaxis_factory_v35_gate.py: PASS
git diff --check antes do commit: PASS
board kaxis-factory-v35-10 ready tasks: []
negative gate smoke: promoted=false, exit code=1
gateway: active
gateway PID: 915372
```

## Decisao Operacional

Nao fiz push automatico para `origin` porque o remoto aponta para:

```text
https://github.com/NousResearch/hermes-agent.git
```

Empurrar branch para um remoto externo/upstream e uma decisao de promocao. O estado seguro agora e:

1. Commit local na VM criado.
2. Patch formatado e hasheado.
3. Testes adicionados e passando.
4. Board piloto sem cards `ready`.
5. Gateway rodando.

## Proximo Passo Recomendado

Escolher um destes caminhos:

1. Criar fork/remoto KAXIS do Hermes e fazer push da branch `codex/kaxis-factory-10-gates`.
2. Abrir PR contra o repo correto usando o patch `0001-add-kaxis-factory-10-kanban-gates.patch`.
3. Se a KAXIS vai manter Hermes como fork interno, promover esse commit para a branch principal do fork KAXIS depois de uma revisao humana.

Depois disso, o proximo hardening real e automatizar a execucao dos gates que hoje sao contratos:

1. Worker que executa Codex Security quando `security_scan_packet.scan_timing` pedir.
2. Worker que executa `solanabr/Auditor` para onchain/Quasar.
3. Worker Product Face que gera e valida screenshots, mobile, acessibilidade e estados.
4. UI de aprovacao humana para R3/R4 com registro no Kanban.
