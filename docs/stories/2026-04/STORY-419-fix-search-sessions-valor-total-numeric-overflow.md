# STORY-419: Fix Numeric Overflow em `search_sessions.valor_total`

**Priority:** P1 — Medium (baixa frequência mas bug real em user input)
**Effort:** S (0.5 day)
**Squad:** @data-engineer + @dev
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issue:** https://confenge.sentry.io/issues/7369847734/ (3 eventos)
**Sprint:** Sprint seguinte (48h-1w)

---

## Contexto

`search_sessions.valor_total` foi definido em `supabase/migrations/001_profiles_and_sessions.sql:85-95` como `numeric(14,2)` — permite até **R$ 999.999.999.999,99** (12 dígitos inteiros, 2 decimais).

Usuários com filtros de alto valor (ex: licitações de infraestrutura federal) podem ter `SUM(valor_estimado)` que ultrapassa esse limite e quebra com:

```
{
  "message": "numeric field overflow",
  "code": "22003",
  "details": "A field with precision 14, scale 2 must round to an absolute value less than 10^12."
}
```

**Frontend contribui:** `frontend/app/buscar/hooks/execution/useSearchAPI.ts:226` não valida `filters.valorMax` — usuário pode digitar qualquer valor.

**Evidência:** 3 eventos em `routes.search.buscar_licitacoes` — `Failed to update session 513ceaf7***`. Baixa frequência mas **100% dos users afetados têm UX quebrada** (session fica em erro).

---

## Acceptance Criteria

### AC1: Migration — alargar coluna
- [ ] Criar `supabase/migrations/2026041004_widen_search_sessions_valor_total.sql`:
  ```sql
  ALTER TABLE search_sessions
    ALTER COLUMN valor_total TYPE numeric(18,2);
  ```
- [ ] `NUMERIC(18,2)` permite até ~R$ 9.999.999.999.999.999,99 (16 dígitos inteiros)
- [ ] Revisar se outras tables têm coluna similar com mesmo problema (ex: `search_results_cache`, `pipeline_items`)
- [ ] Se sim, alargar todas no mesmo migration

### AC2: Validação Pydantic no backend
- [ ] Em `backend/schemas.py`, adicionar validator em `BuscarRequest.valor_maximo`:
  ```python
  @field_validator('valor_maximo')
  @classmethod
  def validate_valor_maximo(cls, v: float | None) -> float | None:
      if v is not None and v > 10**15:
          raise ValueError("valor_maximo não pode exceder R$ 1 quatrilhão")
      return v
  ```
- [ ] Mesma validação em `valor_minimo`
- [ ] Retornar HTTP 422 com mensagem clara em português

### AC3: Clamp no frontend
- [ ] Em `frontend/app/buscar/hooks/execution/useSearchAPI.ts:226`, adicionar clamp:
  ```ts
  const VALOR_MAX_LIMIT = 1_000_000_000_000_000;  // R$ 1 quatrilhão
  valor_maximo: Math.min(filters.valorMax ?? Infinity, VALOR_MAX_LIMIT),
  ```
- [ ] Mostrar mensagem amigável se usuário digitar acima do teto: "Valor máximo ajustado para R$ 1 quatrilhão (limite do sistema)"
- [ ] Componente `FilterPanel` — input type=number com `max={VALOR_MAX_LIMIT}`

### AC4: Tratamento gracioso de overflow existente
- [ ] Em `backend/routes/search.py::buscar_licitacoes`, catch `APIError` com code 22003
- [ ] Quando detectar overflow, log warning + truncar valor para o máximo permitido + continuar processamento
- [ ] Marcar session com flag `valor_total_capped=true` para observability

### AC5: Testes
- [ ] Unit test em `backend/tests/test_schemas.py` — validator de `valor_maximo`
- [ ] Unit test em `backend/tests/test_search.py` — caso de overflow com truncamento gracioso
- [ ] Frontend test em `frontend/__tests__/hooks/useSearchAPI.test.ts` — clamp funcionando
- [ ] E2E Playwright test: digitar R$ 999 trilhões no FilterPanel → mensagem amigável + clamp

### AC6: Verificação pós-deploy
- [ ] Monitorar Sentry issue 7369847734 por 6h — zero novos eventos
- [ ] Grep logs: `railway logs --filter "22003"` = vazio
- [ ] Teste manual: abrir `/buscar`, digitar valor máximo extremo, executar busca, validar sem erro

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `supabase/migrations/2026041004_widen_search_sessions_valor_total.sql` | **Nova migration** — alargar colunas numeric |
| `backend/schemas.py` | Validator Pydantic em `valor_maximo` / `valor_minimo` |
| `backend/routes/search.py` | Catch overflow + graceful truncation |
| `backend/tests/test_schemas.py` | Unit test do validator |
| `backend/tests/test_search.py` | Unit test do overflow handling |
| `frontend/app/buscar/hooks/execution/useSearchAPI.ts` | Linha 226 — clamp |
| `frontend/app/buscar/components/FilterPanel.tsx` | Input max + mensagem amigável |
| `frontend/__tests__/hooks/useSearchAPI.test.ts` | Test do clamp |
| `frontend/e2e-tests/filters.spec.ts` | E2E test |

---

## Implementation Notes

- **`NUMERIC(18,2)` é overkill?** Sim em tese, mas deixa margem para futuras licitações megaprojetos (ex: refinarias, hidrelétricas com valores de R$ 100bi+). Melhor futureproof agora que alterar denovo.
- **Migration é segura?** Sim — `ALTER TYPE numeric(14,2) TO numeric(18,2)` é rápido e sem lock longo no PostgreSQL (metadata only, sem rewrite da table).
- **Por que não bigint (centavos)?** `numeric(18,2)` é mais legível em queries e tem suporte nativo a cast para Python `Decimal`. Centavos em bigint exige conversão manual.
- **Cuidado com SUMs:** verificar se há agregações em views materializadas ou RPCs (ex: `search_datalake`) que dependem do tipo — atualizar se necessário.
- **Coordenação com STORY-412:** se STORY-412 adicionar coluna `objeto_resumo`, essa migration pode ser sequencial (não paralela).

---

## Dev Notes (preencher durante implementação)

<!-- @data-engineer: listar outras colunas encontradas com numeric(14,2) -->

---

## Verification

1. **Migration:** aplicar em staging + verificar `\d search_sessions` mostra `numeric(18,2)`
2. **Backend:** `pytest backend/tests/test_schemas.py::test_valor_maximo_validator -v` passa
3. **Frontend:** `npm test -- useSearchAPI` passa
4. **E2E:** Playwright test passa
5. **Produção:** Sentry issue 7369847734 sem novos eventos por 48h após deploy

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO (9/10). Status Draft → Ready. |
| 2026-04-10 | @dev | Implementation. Nova migration `20260410131000_story419_widen_valor_total.sql` — `ALTER COLUMN valor_total TYPE NUMERIC(18, 2)` (metadata-only, no lock). `backend/schemas/search.py` ganha `@field_validator("valor_maximo", "valor_minimo")` rejeitando `> 1e15` (R$ 1 quatrilhão). `backend/quota/session_tracker.py` aplica defensive cap no momento do UPDATE (linha ~192). `frontend/app/buscar/hooks/execution/useSearchAPI.ts` clamp silencioso em `valorMinClamped` / `valorMaxClamped` antes do POST. 7 tests em `tests/test_story419_valor_total_overflow.py` passam. E2E Playwright deferido. Status Ready → InReview. |
