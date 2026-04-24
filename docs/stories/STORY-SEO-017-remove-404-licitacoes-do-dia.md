# Story SEO-017: Remover 404s de `/blog/licitacoes-do-dia/*` do Sitemap

**Epic:** EPIC-SEO-RECOVERY-2026-Q2
**Priority:** 🟠 P1
**Story Points:** 2 SP
**Owner:** @dev
**Status:** Ready

---

## Problem

HTTP sweep de 1269 URLs no sitemap (2026-04-24) encontrou **43 URLs retornando 404**:

- **42 URLs** em `/blog/licitacoes-do-dia/{data}` (ex: `/blog/licitacoes-do-dia/2026-03-26`)
- **1 URL** em `/blog/panorama/*` OR `/observatorio/raio-x-marco-2026` (verificar qual)

### Causa em código

`frontend/app/sitemap.ts:668-679` gera hardcoded últimos 30 dias:

```typescript
const licitacoesDoDialRoutes: MetadataRoute.Sitemap = Array.from({ length: 30 }, (_, i) => {
  const d = new Date();
  d.setDate(d.getDate() - i);
  const dateStr = d.toISOString().slice(0, 10);
  const freq: 'hourly' | 'daily' = i === 0 ? 'hourly' : 'daily';
  return {
    url: `${baseUrl}/blog/licitacoes-do-dia/${dateStr}`,
    lastModified: i === 0 ? today : d,
    changeFrequency: freq,
    priority: i === 0 ? 0.9 : 0.7,
  };
});
```

Essa lógica assume que toda data dos últimos 30 dias tem uma página `/blog/licitacoes-do-dia/{data}` renderizável. Mas a rota em `frontend/app/blog/licitacoes-do-dia/[date]/page.tsx` depende de dados do backend (`pncp_raw_bids` filtrado por data). Se para uma data específica não há dados (ex: fim de semana, feriado, ou backend timeout no build), a página retorna 404.

**Impacto SEO:** Google crawlea, encontra 404, marca domínio como "baixa qualidade" (many broken links reduzem trust). GSC reporta "Submitted URL not found (404)" — penalidade.

---

## Acceptance Criteria

- [ ] **AC1** — Modificar `frontend/app/sitemap.ts:668-679`:
  - Opção A: Fetch de endpoint backend `/v1/sitemap/licitacoes-do-dia-indexable` que retorna apenas datas com ≥N bids (N=configurable, default 5)
  - Opção B: Se backend endpoint inviável, gerar apenas últimos 7 dias (janela curta, menor probabilidade de 404) + check síncrono antes de adicionar (aguarda request HEAD em cada URL — lento, não recomendado)
  - Preferir Opção A. Documentar decisão.
- [ ] **AC2** — Criar endpoint backend `/v1/sitemap/licitacoes-do-dia-indexable` (se Opção A) retornando `{"dates": ["2026-04-23", "2026-04-22", ...]}` — apenas datas com ≥N bids em `pncp_raw_bids` WHERE `data_publicacao::date = X`. Cache TTL 1h (dia corrente muda).
- [ ] **AC3** — Rota `/blog/licitacoes-do-dia/[date]` deve retornar 200 + noindex (ou 410 Gone) para datas sem dados — nunca 404. Check em `page.tsx`:
  ```typescript
  if (bids.length === 0) {
    return {
      robots: { index: false, follow: false },
      // render "Nenhuma licitação publicada em {data}"
    };
  }
  ```
- [ ] **AC4** — Verificar rota `/observatorio/raio-x-marco-2026` (sitemap `id:0` linha 399-403):
  - Se página existe e dados indisponíveis: implementar fallback 200+noindex
  - Se rota não existe mais: remover do sitemap
- [ ] **AC5** — HTTP sweep pós-deploy:
  ```bash
  python3 /tmp/sitemap_sweep.py  # usa unique_urls.txt
  ```
  Resultado: 0 URLs retornando 404 (vs 43 baseline).
- [ ] **AC6** — GSC Coverage: em 14 dias após deploy, "Submitted URL not found (404)" deve reduzir de ~43 → 0 (ou decay natural conforme Google re-crawl).

---

## Scope IN

- Refatorar geração de `/blog/licitacoes-do-dia/*` no sitemap
- Endpoint backend `licitacoes-do-dia-indexable` (se Opção A)
- Fix fallback em page.tsx para datas sem dados
- Verificar + fixar `/observatorio/raio-x-marco-2026`

## Scope OUT

- Outros 404s não listados no sweep (seriam escopo novo se surgirem)
- Redesign da página `/blog/licitacoes-do-dia/[date]` — apenas fallback
- Backfill histórico de dados (data passada sem bid não vai ter agora)

---

## Implementation Notes

### Opção A (recomendada)

```typescript
// frontend/app/sitemap.ts
async function fetchLicitacoesDoDiaIndexable(): Promise<string[]> {
  const result = await fetchSitemapJson<string[]>(
    '/v1/sitemap/licitacoes-do-dia-indexable',
    (d) => ((d as { dates?: string[] }).dates ?? []),
    'licitacoes-do-dia-indexable',
  );
  return result ?? [];
}

// Em case 3:
const indexableDates = await fetchLicitacoesDoDiaIndexable();
const licitacoesDoDialRoutes: MetadataRoute.Sitemap = indexableDates.slice(0, 30).map((dateStr) => {
  const d = new Date(dateStr);
  const freq: 'hourly' | 'daily' = dateStr === today.toISOString().slice(0, 10) ? 'hourly' : 'daily';
  return {
    url: `${baseUrl}/blog/licitacoes-do-dia/${dateStr}`,
    lastModified: d,
    changeFrequency: freq,
    priority: dateStr === today.toISOString().slice(0, 10) ? 0.9 : 0.7,
  };
});
```

Backend:
```python
# backend/routes/sitemap_licitacoes_do_dia.py (NOVO)
@router.get("/sitemap/licitacoes-do-dia-indexable", response_model=...)
async def sitemap_licitacoes_do_dia_indexable():
    # Cache InMemory 1h
    # Query: SELECT DISTINCT data_publicacao::date FROM pncp_raw_bids
    #        WHERE data_publicacao >= NOW() - INTERVAL '30 days'
    #          AND is_active = true
    #        GROUP BY data_publicacao::date
    #        HAVING COUNT(*) >= 5
    #        ORDER BY data_publicacao::date DESC
    ...
```

### Fix fallback

```typescript
// frontend/app/blog/licitacoes-do-dia/[date]/page.tsx
export async function generateMetadata({ params }: Props) {
  const { date } = await params;
  const bids = await fetchBidsForDate(date);
  if (bids.length === 0) {
    return {
      title: `Sem licitações publicadas em ${formatDate(date)} | SmartLic`,
      robots: { index: false, follow: false },
    };
  }
  // ... metadata normal
}
```

Page body renderiza mensagem graceful ao invés de 404. Google já inferiu a data via sitemap; noindex remove da fila de indexação sem 404 penalty.

---

## Dependencies

- **Pre:** Nenhum (independente de SEO-013). Pode rodar em paralelo.
- **Unlocks:** GSC health melhora → crawl budget redirecionado para entity pages

---

## Change Log

| Date | Agent | Action |
|------|-------|--------|
| 2026-04-24 | @sm (River) | Story criada. 43 URLs 404 identificados via HTTP sweep. Root cause isolado em `sitemap.ts:668` hardcoded 30d. |
| 2026-04-24 | @po (Pax) | *validate-story-draft 8/10 → GO. Status Draft → Ready. Independente de SEO-013 — pode executar em paralelo. Preferir Opção A (endpoint backend) per AC1. |
