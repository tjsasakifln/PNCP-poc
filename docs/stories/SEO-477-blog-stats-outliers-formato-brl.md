# SEO-477 — Bug: Stats infladas por outliers PNCP + formatBRL sem compact notation

**Status:** Done
**Type:** Bugfix — P1 UX/dados
**Prioridade:** Alta — páginas de marketing exibem dados absurdos ao público

---

## Problema

Sessão beta-testing 044 (2026-04-14) identificou que `/blog/licitacoes/engenharia/sp` exibe:

- **Editais Abertos**: 1000 (número suspeito — provavelmente o cap do `limit=2000`)
- **Valor Médio**: R$10.849.085.800 ← R$ 10 **bilhões** de média (absurdo)
- **Faixa de Valores**: R$0 a R$10.000.000.000.000 ← R$ 10 **trilhões** de máximo (dado corrompido)

O PNCP contém registros com erros de entrada de dados (valores como `valorTotalEstimado: 10000000000000`). Um único outlier destrói todas as estatísticas agregadas.

### Bug 1 — Outlier não filtrado no backend

Em `backend/routes/blog_stats.py`, linha ~528:
```python
values = [v for item in uf_results if (v := _extract_value(item)) is not None]
avg_val = sum(values) / len(values) if values else 0.0
min_val = min(values) if values else 0.0
max_val = max(values) if values else 0.0
```

Sem nenhum filtro de outlier. Um contrato com `valorTotalEstimado = 10000000000000` (10 trilhões) entra diretamente no cálculo.

**Fix proposto:** Cap de R$500 milhões (5e8) para qualquer valor individual nos cálculos de stats de blog. Valores acima disso são quase certamente erros de digitação no PNCP. O `viability_value_range` máximo em qualquer setor é R$20M — um cap de 500M é 25x esse valor, cobrindo contratos legítimos mas enormes.

### Bug 2 — formatBRL exibe número inteiro sem compact notation

Em `frontend/lib/programmatic.ts`:
```typescript
export function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}
```

Resultado: `R$10.849.085.800` — 12 dígitos em uma caixa de stats de página de marketing.

**Fix proposto:** Adicionar compact notation para valores ≥ R$1M:
- `< R$1M` → `R$750.000` (formato atual)
- `R$1M–R$999M` → `R$1,5 mi`
- `≥ R$1B` → `R$10,8 bi`

---

## Acceptance Criteria

### Backend (outlier filter)
- [x] AC1: `_extract_value()` ou a agregação de stats aplica cap de R$500M por valor individual
- [x] AC2: `/blog/stats/setor/engenharia_projetos_obras/uf/SP` retorna `avg_value` < 500.000.000 e `value_range_max` < 500.000.000
- [x] AC3: Cap documentado em comentário no código (por quê R$500M)
- [x] AC4: Cache de blog stats invalidado após deploy (InMemory 6h TTL zerado no restart do Railway a cada deploy) (para não servir valores antigos)

### Frontend (compact notation)
- [x] AC5: `formatBRLCompact(10849085800)` retorna `"R$10,8 bi"` — função separada criada (formatBRL tem 39 callers fora do escopo)
- [x] AC6: `formatBRLCompact(1500000)` retorna `"R$1,5 mi"`
- [x] AC7: `formatBRLCompact(750000)` retorna `"R$750.000"` (comportamento preservado para valores < 1M)
- [x] AC8: Compact notation aplicada nos 5 pontos de stats do `blog/licitacoes/[setor]/[uf]` (valor médio e faixa)
- [x] AC9: Testes unitários para `formatBRLCompact` cobrindo 3 ranges + edge cases (8 testes, todos passando)

---

## Escopo

**IN:**
- `backend/routes/blog_stats.py` — cap de outlier em `_extract_value()` ou na agregação
- `frontend/lib/programmatic.ts` — `formatBRL` com compact notation
- Testes para `formatBRL`

**OUT:**
- Não alterar filtro de outliers na busca principal (search pipeline) — só nos blog stats
- Não alterar `formatBRL` na busca/dashboard (somente nas páginas programáticas de blog)
  → **ATENÇÃO**: verificar todos os chamadores de `formatBRL` antes de alterar assinatura. Se usado em múltiplos contextos, criar `formatBRLCompact` separado e usar somente nas stats de blog.

---

## Dependências

- Nenhuma

---

## Complexidade

**P (Pequena)** — 2 arquivos, mudanças cirúrgicas

---

## Notas Técnicas

### Cap recomendado para outlier
```python
_STATS_VALUE_CAP = 500_000_000  # R$500M — acima disso é erro de digitação no PNCP

def _extract_value(item: dict) -> Optional[float]:
    v = item.get("valorTotalEstimado") or item.get("valorEstimado") or item.get("valor_estimado")
    if v and isinstance(v, (int, float)) and 0 < v <= _STATS_VALUE_CAP:
        return float(v)
    return None
```

### compact formatBRL sugerido
```typescript
export function formatBRL(value: number): string {
  if (value >= 1_000_000_000) {
    return `R$${(value / 1_000_000_000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} bi`;
  }
  if (value >= 1_000_000) {
    return `R$${(value / 1_000_000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mi`;
  }
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency', currency: 'BRL',
    minimumFractionDigits: 0, maximumFractionDigits: 0,
  }).format(value);
}
```

---

## File List

- [x] `docs/stories/SEO-477-blog-stats-outliers-formato-brl.md` (esta story)
- [x] `backend/routes/blog_stats.py`
- [x] `frontend/lib/programmatic.ts`
- [x] `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`
- [x] `frontend/__tests__/programmatic.test.ts`

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-14 | @sm (beta-team 044) | Story criada — bugs identificados em produção via screenshots |
| 2026-04-14 | @po (Pax) | GO 7/10 → Ready. **Risco crítico:** `formatBRL` pode ter chamadores em dashboard/busca — `grep -r "formatBRL" frontend/` antes de alterar. Se múltiplos contextos: criar `formatBRLCompact` separado e usar APENAS nas stats do blog. AC8 refinado: verificar TODOS os componentes que recebem `avg_value`/`value_range_*`. |
| 2026-04-14 | @dev (James) | Implementação completa. `formatBRL` tem 39 callers fora do escopo → criado `formatBRLCompact` separado. Backend: `_STATS_VALUE_CAP = 500_000_000` em `_extract_value()`. Frontend: `formatBRLCompact` em 5 pontos de stats. 8 testes unitários passando. 317 testes relacionados passando. Zero regressões. |
