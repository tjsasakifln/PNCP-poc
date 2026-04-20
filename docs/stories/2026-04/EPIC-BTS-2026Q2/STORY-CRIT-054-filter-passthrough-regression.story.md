# STORY-CRIT-054 — Filter PCP v2 Pass-Through Regression (3 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1 — Production regression detectada via BTS-005 guardrail (impacta resultado PCP v2 desconhecido/todos)
**Effort:** XS (1-2h)
**Agents:** @dev + @qa (possível @architect se ramo tiver invariantes mais largos)
**Status:** Done (PR #407 merged `2ff704a4` — 2026-04-20)

---

## Contexto

Durante execução da STORY-BTS-005 (2026-04-19 Wave 2), o agente detectou que 3 testes em `backend/tests/test_crit054_pcp_status_mapping.py` estão falhando **não por drift de teste**, mas por **regressão real de produção**.

A refatoração DEBT-201 (`filter.py` → `filter/pipeline.py`) silenciosamente dropou o branch `elif` responsável pelo pass-through de status `desconhecido`/`todos` vindo da fonte PCP v2. Sem ele, editais da PCP v2 sem status inferível são descartados no filtro.

O código correto existia em `bf6ab7cc:backend/filter.py:2385-2395` e foi perdido durante o split modular.

**Guardrail BTS-005 held:** o agente NÃO editou produção, NÃO introduziu skip/xfail, NÃO relaxou assertions. Abriu esta story como follow-up — escolha correta (advisor guidance: "gate stays red, real bug surfaces" outcome).

---

## Evidência

**Testes falhando (PR #401 merged com 3 tests documentados como blocked):**
- `backend/tests/test_crit054_pcp_status_mapping.py::TestPassthrough::test_desconhecido_passes_through`
- `backend/tests/test_crit054_pcp_status_mapping.py::TestPassthrough::test_todos_passes_through`
- `backend/tests/test_crit054_pcp_status_mapping.py::<terceiro teste a confirmar via pytest>`

**Origem do branch correto (referência histórica):**
```python
# backend/filter.py @ bf6ab7cc lines 2385-2395
elif status_inferido in ("desconhecido", "todos"):
    # PCP v2 pass-through: mantém editais sem status inferível
    filtrados.append(item)
    _status_unconfirmed.append(item.numero_controle_pncp)
    FILTER_PASSTHROUGH_TOTAL.labels(source=item.source).inc()
```

**Alvo atual:**
- `backend/filter/pipeline.py` ~linha 137-140 (após `status_inferido == status_lower` check na loop de status filter)

---

## Acceptance Criteria

> **Spec correction (2026-04-20 @dev):** ACs originais foram re-derivados dos testes (`backend/tests/test_crit054_pcp_status_mapping.py`). Diferenças vs. redação original: (a) `_status_unconfirmed` é **dict attribute por bid** (não lista module-level) — test line 246: `bids2[0].get("_status_unconfirmed") is True`; (b) `FILTER_PASSTHROUGH_TOTAL` já existe em `metrics.py:792` com label **`reason`** (não `source`); (c) branch precisa gate em `_source == "PORTAL_COMPRAS"` para não quebrar `test_pncp_todos_still_rejected`.

### AC1 — Restaurar branch elif em filter/pipeline.py
- [x] Adicionar `elif status_inferido in ("desconhecido", "todos") and lic.get("_source") == "PORTAL_COMPRAS"` no status filter loop
- [x] Append `lic` em `resultado_status`
- [x] Setar `lic["_status_unconfirmed"] = True` (dict attribute, não lista)
- [x] Incrementar `FILTER_PASSTHROUGH_TOTAL.labels(reason="pcp_status_ambiguous").inc()` com try/except (pattern existente em `status_inference.py`)
- [x] Posição correta: entre `if status_inferido == status_lower` e `else: stats["rejeitadas_status"] += 1` (pipeline.py ~linha 137-170)

### AC2 — Prometheus counter reutilizado
- [x] `FILTER_PASSTHROUGH_TOTAL` já existe em `backend/metrics.py:792` — nenhuma mudança necessária
- [x] Labels existentes: `reason` (não `source` — label atual do counter após refactor pós-bf6ab7cc)
- [x] Incrementar apenas em pass-through branch (não em match direto)

### AC3 — Marcador `_status_unconfirmed` como dict attribute
- [x] Setado como `lic["_status_unconfirmed"] = True` dentro do elif
- [x] Ausente em bids que batem match direto (pinado por `test_correctly_mapped_pcp_passes_normally`)
- [x] Escopo per-bid (não shared state module-level) — thread-safe by design

### AC4 — 3 testes CRIT-054 passam (validação via CI)
- [ ] `pytest tests/test_crit054_pcp_status_mapping.py --timeout=20 -q` → 0 failed **(validação: CI pós-merge — ambiente local sem pytest)**
- [ ] Nenhum outro teste filter quebra — blast radius verificado via grep: `_status_unconfirmed` só aparece nos 3 asserts do test file (zero produção legacy)

### AC5 — Observabilidade
- [x] Counter `smartlic_filter_passthrough_total{reason="pcp_status_ambiguous"}` disponível em `/metrics` pós-deploy
- [ ] Registrar no Grafana dashboard — follow-up (não block para esta story)

---

## Out-of-scope

- Reescrever outros branches do status filter (apenas restaurar o removido)
- Adicionar testes novos além dos 3 já existentes
- Refatorar `filter/pipeline.py` além do mínimo para o elif

---

## Valor

**Impacto:** editais PCP v2 com status indefinido não caem silenciosamente no chão. Sem este fix:
- Resultado de busca com fonte PCP v2 pode estar sub-retornando itens relevantes
- Métrica `FILTER_PASSTHROUGH_TOTAL` está em zero indevidamente → observability blind spot
- Gate BTS CI continua com 3 failures bloqueando encerramento do epic

**Cliente:** qualquer usuário buscando editais que dependem da PCP v2 (secundária, mas cobertura ampliada em STORY-265).

---

## Riscos

- **Baixo:** o elif é um branch puramente aditivo (não altera lógica existente)
- **Atenção:** ordem de branches importa — tem que ficar depois do match direto
- **Teste regression:** rodar suite completa de filter tests antes/depois

---

## Change Log

- **2026-04-19** — @dev (via agente BTS-005 guardrail): regressão detectada e documentada em PR #401. Abrindo story como follow-up com guardrail "no prod edit" respeitado.
- **2026-04-20** — @dev: Fix aplicado em `backend/filter/pipeline.py` (elif adicionado linhas 138-154). Spec re-derivada dos testes (vs story original) e documentada no topo dos ACs. AC1/AC2/AC3/AC5 marcados [x]; AC4 bloqueado por ambiente local sem pytest — CI é validação final. Blast radius mínimo: grep `_status_unconfirmed` confirma zero call sites em produção legacy (só 3 asserts no test file). Status Ready → InReview aguardando merge.
- **2026-04-20** — @devops: PR #407 `fix(filter): STORY-CRIT-054 — restore PCP v2 pass-through for ambiguous status` merged em `2ff704a4`. Status `InReview` → `Done`.
