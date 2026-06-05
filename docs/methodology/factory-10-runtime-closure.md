# KAXIS Factory 10 Closure - Hermes Runtime Proof

Data: 2026-06-05  
Board piloto: `kaxis-factory-v35-10`  
Board corrente preservado: `kaxis-factory-pilot-v342b`  
Escopo: fechar a fabrica KAXIS/Hermes como linha de producao operacional, com gates reais no Kanban, sem depender de boa vontade do agente.

## Veredito

Nota honesta da fabrica depois desta rodada: 10/10 para metodologia + contrato operacional + enforcement no Hermes real.

Isso nao significa que um produto KAXIS real ja foi entregue em producao. Significa que a fabrica agora tem bloqueios objetivos suficientes para impedir os erros que derrubariam execucao autonoma: card fraco, front-end sem Product Face, onchain sem Auditor, R4 sem gate humano, agente revisando a si mesmo, seguranca virando texto solto, conclusao sem Receipt Five e scripts tratando falha como sucesso.

## O Que Mudou

### 1. Gate KAXIS V3.5 opt-in no Hermes

Arquivo remoto alterado: `/srv/hermes/home/hermes-agent/hermes_cli/kanban_db.py`

Cards com `factory_method_version` igual a `KAXIS_V3_5_AGENT_WORKFORCE` ou `KAXIS_V3_5_FACTORY_10` passam por contrato forte antes de `ready` e antes de `done`.

Campos obrigatorios no ready:

- `phase`
- `surfaces`
- `risk_initial`
- `risk_effective`
- `authority_max`
- `owner_worker`
- `executor_identity`
- `reviewer_identity`
- `runtime_decision`
- `runtime_contract`
- `security_contract`
- `forbidden_actions`
- `done_definition`
- `transition_event_required`
- `kanban_transition_event_ref`

Por que isso e melhor: agentes executam melhor com contrato explicito do que com metodologia narrada. O gate transforma a metodologia em bloqueio de estado.

### 2. Product Face virou contrato obrigatorio

Para `ux`, `frontend`, `mobile` ou `wallet-ui`, o card precisa de `product_face_packet`.

Campos exigidos:

- inventario de telas
- matriz de estados
- referencia de design contract
- breakpoints mobile
- acessibilidade
- budget de performance
- plano de evidencia visual
- fluxo de wallet quando houver `wallet-ui`

Por que isso e melhor: produto nao e so backend. Sem cara, estados, wallet flow e evidencia visual, a fabrica gera sistema incompleto.

### 3. Onchain/Solana virou pacote proprio

Para surfaces onchain como `solana-quasar`, `account-pda`, `cpi`, `compute-units`, `token-kx`, `custody`, `signer-authority`, `funds` ou `mainnet`, o card precisa de `onchain_work_package`.

Campos exigidos:

- `quasar_source_ref`
- `framework_default`
- `account_map`
- `instruction_abi`
- `pda_derivation`
- `cpi_allowlist`
- `compute_unit_budget`

Para R3/R4 onchain: `auditor_required=true` ou waiver humano estruturado.

Por que isso e melhor: Solana/Quasar nao pode cair em review generico. O programa sera coracao da KAXIS, entao Auditor e pacote onchain precisam entrar antes do trabalho virar execucao.

### 4. Segurança virou scan obrigatorio, nao opiniao

Para R3/R4, onchain ou surfaces de seguranca, o ready gate exige `security_scan_packet`.

Campos exigidos:

- `security_owner`
- `scanner_agent`
- `scan_timing`
- `scan_scope`
- `required_tools`
- `acceptance_policy`

`required_tools` precisa referenciar Codex Security ou cybersecurity.

No done gate, a metadata precisa ter `security_scan_result` quando o card exige scan.

Campos exigidos no resultado:

- `scanner_agent`
- `tool`
- `scope`
- `result`
- `findings_summary`
- `evidence_refs`

`result` precisa ser `PASS` ou `WAIVED`. Se houver `blocking_findings=true`, precisa existir `security_exception`.

Por que isso e melhor: "fazer seguranca" como texto e fraco para agentes. O timing do scan agora esta no card, e a evidencia do scan agora trava a conclusao.

### 5. Anti-auto-revisao

O gate bloqueia `executor_identity == reviewer_identity`.

Por que isso e melhor: em execucao autonoma, self-review e uma das formas mais rapidas de inflar confianca falsa. A fabrica agora exige separacao de papeis como contrato.

### 6. R4 exige pacote humano

Para R4, o gate exige `r4_gate` com:

- `human_approval_ref`
- `rollback_plan`
- `risk_owner`
- `security_owner`

Por que isso e melhor: R4 nao pode depender de "parece seguro". Precisa de dono humano, rollback e autoridade explicita antes de entrar na esteira.

### 7. Done exige Receipt Five e evento de transicao

Antes de `done`, cards V3.5 exigem metadata com:

- `receipt_five`
- `kanban_transition_event`

Se `reviewer_required=true`, tambem precisa de `reviewer_result`.

Por que isso e melhor: o Kanban deixa de ser "marquei como feito" e vira cadeia de custodia. O agente precisa dizer o que mudou, onde esta a evidencia, como verificou, quem revisou e qual e a proxima acao.

### 8. Exit code do CLI corrigido

Arquivo remoto alterado: `/srv/hermes/home/hermes-agent/hermes_cli/main.py`

Antes, o `kanban_command` devolvia falha internamente, mas o dispatcher principal descartava o retorno. Resultado perigoso: `promoted:false` podia sair com exit code `0`.

Agora `main()` retorna `int(code or 0)` quando executa comandos com `args.func`.

Por que isso e melhor: agentes e scripts nao leem intencao, leem exit code. Falha com exit code `0` e bypass operacional.

## Evidencia Tecnica

Remote head base:

```text
baafc2ef85748c2689f8c57e1aad7508fe146063
```

Hashes finais remotos:

```text
kanban_db.py  9a6e2a11964162bd7c0a8d715af354ca9d0574da7c65b2db318ff397e476e235
main.py       64a70af84a45b22b91071b501680683280054aa843bdf24088df75ecb96599ec
```

Diff final:

```text
hermes_cli/kanban_db.py | 347 insertions
hermes_cli/main.py      | 4 changed lines
2 files changed, 350 insertions(+), 1 deletion(-)
```

Validacoes finais:

```text
py_compile kanban_db.py/main.py: PASS
git diff --check: PASS
gateway: active
gateway PID novo: 915372
board piloto ready tasks: []
```

Backups remotos:

```text
/srv/hermes/home/context-lock/kaxis-factory-10-runtime/backups/kanban_db.py.before-v35-20260605T210525Z
/srv/hermes/home/context-lock/kaxis-factory-10-runtime/backups/kanban_db.py.before-v35-security-scan-20260605-212024
/srv/hermes/home/context-lock/kaxis-factory-10-runtime/backups/main.py.before-v35-exit-code-20260605-211532
```

## Matriz de Prova no Hermes

| ID | Prova | Esperado | Resultado |
|---|---|---|---|
| `t_201f4277` | Front/Product Face sem packet | bloqueia ready | bloqueou |
| `t_f92257bc` | Product Face valido | passa ready, falha done sem metadata, passa com Receipt Five | passou |
| `t_d7da4299` | Onchain R3 sem Auditor | bloqueia ready | bloqueou |
| `t_746864ee` | R4 sem `r4_gate` | bloqueia ready | bloqueou |
| `t_9858eb7c` | Completion exit code | falha sem metadata com exit `1`, passa com metadata | passou |
| `t_3851cf14` | R3/security sem scan packet | bloqueia ready | bloqueou com erro exato |
| `t_cf251e3a` | R3/security com scan packet | passa ready; nao fecha sem gates humanos V2 | passou ready, estacionado em blocked |
| `t_20ebfb05` | Self-review | bloqueia ready | bloqueou com exit `1` |
| `t_f8b16892` | R1/security com scan obrigatorio | passa ready, falha done sem scan result, passa com scan result | passou |
| `t_c2bf297b` | Onchain Quasar + Auditor + scan | passa ready | passou ready, estacionado em blocked |

Exit code smoke final:

```text
promote t_20ebfb05 -> promoted:false
exit code -> 1
```

## Estado Seguro do Board

Board piloto: `kaxis-factory-v35-10`

Estado final:

```text
blocked: 9
done: 3
ready: 0
```

Nenhum card ficou `ready` ao final. Os cards que provaram ready em R3/onchain foram estacionados em `blocked` para evitar despacho acidental.

## Revisao Critica

### O que ainda pode quebrar

1. O patch esta aplicado na VM, mas ainda precisa ser promovido para o repositorio de origem do Hermes se quisermos durabilidade fora desta VM.
2. O gate foi provado por CLI e gateway reiniciado, mas ainda falta teste via UI/API do Hermes se a interface de Kanban criar/promover cards por outro caminho.
3. A metodologia esta forte no contrato de card e transicao, mas ainda precisa de um produto real para calibrar volume de campos, friccao e tempo de ciclo.
4. R3/R4 reais continuam exigindo aprovacoes humanas reais. Isso e correto. Nao foi falsificado no teste.
5. O gate valida existencia de pacote de scan e resultado de scan, mas nao executa automaticamente o Codex Security. A execucao automatica do scanner precisa entrar no dispatcher/worker como proximo hardening.

### O que um agente poderia interpretar errado

1. Confundir `ready` de teste com autorizacao de execucao real. Mitigacao: cards de prova R3 foram estacionados em `blocked`.
2. Tratar `security_scan_packet` como scan realizado. Mitigacao: o done gate exige `security_scan_result`.
3. Usar `WAIVED` como saida facil. Mitigacao ainda parcial: precisa de politica mais forte para waiver humano em cards reais.
4. Achar que Auditor substitui Codex Security. Mitigacao: onchain R3/R4 agora pede Auditor e scan packet.
5. Achar que Product Face e opcional para backend. Mitigacao: front/mobile/wallet surfaces obrigam Product Face Packet.

### O que esta sofisticado demais

O contrato V3.5 ficou pesado para cards pequenos. Isso e aceitavel para a fabrica porque o V3.5 e opt-in; cards antigos e R0/R1 simples continuam menos pesados. Para produto real, o Hermes deve gerar esses campos automaticamente a partir do paper/SOT, nao pedir que humano escreva tudo.

### O que esta simples demais

1. O scan security ainda e validado por contrato, nao disparado automaticamente.
2. O Product Face Packet valida campos, mas ainda nao valida screenshots, Playwright, mobile ou acessibilidade de fato.
3. O Onchain Package valida presenca de mapa/ABI/PDA/CPI/CU, mas ainda nao roda Auditor automaticamente.
4. O R4 gate valida pacote humano, mas ainda nao amarra isso a uma UI de aprovacao assinada pelo Felipe.

## Decisao

A fabrica KAXIS/Hermes esta fechada como metodologia operacional validada em runtime para o nivel atual: paper/SOT -> arquitetura -> especialidades -> Product Face -> onchain/Auditor -> security scan -> decomposition -> execution -> evidence -> review -> done.

O salto que falta para alem de nota 10 teorica e o primeiro produto real passando pela esteira. Esse teste deve medir se os contratos ajudam ou viram atrito, e deve alimentar a V3.6.

## Proximo Hardening Recomendado

1. Criar worker/gate automatico para executar Codex Security no timing definido em `security_scan_packet.scan_timing`.
2. Criar worker/gate automatico para executar `solanabr/Auditor` em cards onchain.
3. Criar validador de Product Face com screenshots, mobile, a11y e estados via browser/Playwright.
4. Criar UI de aprovacao humana para R3/R4 com registro imutavel no Kanban.
5. Transformar este patch local em PR/commit do Hermes KAXIS.
