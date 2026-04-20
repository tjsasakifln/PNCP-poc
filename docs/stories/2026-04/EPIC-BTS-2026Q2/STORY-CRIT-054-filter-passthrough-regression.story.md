# STORY-CRIT-054 — Filter PCP v2 Pass-Through Regression (3 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1 — Production regression detectada via BTS-005 guardrail (impacta resultado PCP v2 desconhecido/todos)
**Effort:** XS (1-2h)
**Agents:** @dev + @qa (possível @architect se ramo tiver invariantes mais largos)
**Status:** Ready

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

### AC1 — Restaurar branch elif em filter/pipeline.py
- [ ] Adicionar `elif status_inferido in ("desconhecido", "todos")` no status filter loop
- [ ] Append item em `filtrados`
- [ ] Append `numero_controle_pncp` em `_status_unconfirmed`
- [ ] Incrementar `FILTER_PASSTHROUGH_TOTAL.labels(source=item.source).inc()`
- [ ] Posição correta: depois do match direto (`status_inferido == status_lower`), antes do descarte final

### AC2 — Restaurar Prometheus counter
- [ ] `FILTER_PASSTHROUGH_TOTAL` deve existir em `backend/metrics.py` (ou módulo equivalente)
- [ ] Labels: `source` (`pncp`, `pcp`, `comprasgov`)
- [ ] Incrementar apenas em pass-through branch (não em match direto)

### AC3 — Restaurar `_status_unconfirmed` marker
- [ ] Lista/set module-level em `filter/pipeline.py` (ou state equivalente)
- [ ] Exposto como atributo para introspecção em testes
- [ ] Limpo entre calls via contexto apropriado

### AC4 — 3 testes CRIT-054 passam
- [ ] `pytest tests/test_crit054_pcp_status_mapping.py --timeout=20 -q` → 0 failed
- [ ] Nenhum outro teste quebra (regression check em pipeline tests)

### AC5 — Observabilidade
- [ ] Counter `smartlic_filter_passthrough_total{source="pcp"}` visível em `/metrics`
- [ ] Registrar no Grafana dashboard se aplicável (ou documentar em story de follow-up)

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
