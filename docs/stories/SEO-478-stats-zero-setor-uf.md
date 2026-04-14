# SEO-478 — Bug: Stats zeradas em combos setor×UF (ex: software/SP)

**Status:** InProgress
**Type:** Bugfix/Investigação — P1
**Prioridade:** Alta — páginas de marketing públicas exibem "0 editais, R$0" para combos ativos

---

## Problema

Sessão beta-testing 044 (2026-04-14): `/blog/licitacoes/software/sp` exibe:
- **Editais Abertos**: 0
- **Valor Médio**: R$0
- **Faixa de Valores**: R$0 a R$0

São Paulo é o maior mercado de TI/software do Brasil. Zero editais é implausível — indica falha de query ou cache.

Além disso, a página exibe o subtítulo: **"O editais publicados nos últimos 30 dias."** — typo: "O" deve ser "Os".

### Hipóteses (investigar em ordem)

**H1 — Slug to sector ID mismatch (mais provável)**
O URL usa slug `software`, mas `sectorId = sectorSlug.replace(/-/g, '_')` → `"software"`.
Se o ID no `sectors_data.yaml` for `"software_e_sistemas"` (não `"software"`), o `_validate_sector("software")` retorna 404 no backend. O frontend então recebe `null` e exibe `total_editais ?? 0` → 0.

Verificar: qual é o ID exato do setor software no YAML? Qual é o slug usado na URL?

**H2 — Cache de backend com zeros**
O in-memory cache do blog stats tem TTL de 6h. Se o cache foi populado quando o datalake não tinha dados (ex: após purge, antes da ingestão), fica com 0 até expirar.

Verificar: endpoint `/v1/blog/stats/setor/software_e_sistemas/uf/SP` retorna quanto? E `/v1/blog/stats/setor/software/uf/SP`?

**H3 — Datalake sem dados de software para SP nos últimos 30 dias**
Possível se os keywords do setor software não matcham os textos das licitações de SP no datalake. Verificar densidade de keywords no datalake para SP × software.

**H4 — ISR cache do Next.js com dados stale**
A página tem `export const revalidate = 86400` (24h). Se foi gerada quando o backend retornava 0, fica assim por até 24h.

---

## Acceptance Criteria

- [x] AC1: Diagnóstico documentado — qual hipótese é a causa raiz
- [x] AC2: `/blog/licitacoes/software/sp` exibe `total_editais > 0` se o datalake tem licitações de software em SP nos últimos 30 dias
- [x] AC3: Se H1 confirmada — slug `software` correto mapeado para `software_desenvolvimento` no frontend via `SECTOR_SLUG_TO_BACKEND_ID`
- [x] AC4: H2 não se aplica — causa raiz é H1 (slug mismatch → 404 → null → 0)
- [x] AC5: Typo "O editais" não existe no código atual; texto linha 295 usa `{stats?.total_editais ?? 0} editais publicados...` (gramaticalmente correto). O "O" visto na sessão beta era ISR stale de versão anterior; fix H1 faz stats != null e exibe valor real.
- [x] AC6: Todos os setores com mismatch corrigidos: `software`→`software_desenvolvimento`, `facilities`→`servicos_prediais`, `saude`→`medicamentos`, `transporte`→`transporte_servicos`. Fix aplicado em 7 funções (5 em programmatic.ts + 2 em contracts-fallback.ts).

---

## Escopo

**IN:**
- Investigação e diagnóstico das 4 hipóteses
- Fix no mapeamento slug → sector ID (se H1)
- Fix no cache ou query (se H2/H3)
- Correção do typo "O editais" → "Os editais"

**OUT:**
- Não alterar lógica de noindex (página com 0 editais legítimos deve permanecer noindex)
- Não modificar estrutura de URLs

---

## Passo de Diagnóstico

```bash
# Testar direto no backend de produção:
curl "https://api.smartlic.tech/v1/blog/stats/setor/software/uf/SP"
curl "https://api.smartlic.tech/v1/blog/stats/setor/software_e_sistemas/uf/SP"

# Ver quantos IDs de setor existem:
curl "https://api.smartlic.tech/setores" | jq '.[].id'
```

Checar também o frontend: `frontend/lib/sectors.ts` — qual é o `slug` do setor Software e Sistemas?

---

## Dependências

- Nenhuma bloqueante. Pode ser investigado em paralelo com SEO-476 e SEO-477.

---

## Complexidade

**P–M** — Depende da hipótese confirmada. H1 é P (renomear slug). H3 é M (ajustar keywords).

---

## File List

- [x] `docs/stories/SEO-478-stats-zero-setor-uf.md` (esta story)
- [x] `frontend/lib/programmatic.ts` (H1 fix — SECTOR_SLUG_TO_BACKEND_ID em 5 funções)
- [x] `frontend/lib/contracts-fallback.ts` (H1 fix — SECTOR_SLUG_TO_BACKEND_ID em 2 funções)
- [ ] `frontend/lib/sectors.ts` (não modificado — IDs de setor no frontend mantidos para preservar URLs)
- [ ] `backend/routes/blog_stats.py` (H2 não confirmada — sem alteração)
- [ ] `backend/sectors_data.yaml` (H3 não confirmada — sem alteração)
- [ ] `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx` (AC5 — typo não encontrado no código atual; resolvido por fix H1)

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-14 | @sm (beta-team 044) | Story criada — bug + typo identificados em produção |
| 2026-04-14 | @po (Pax) | GO 7/10 → Ready. **Refinamento AC1:** diagnóstico deve ser documentado como comentário no PR ou atualização nesta story antes do merge — não apenas na cabeça do @dev. Risco adicional: se H3 (keywords) for a causa, verificar TODOS os setores com 0 editais suspeitos (não só software/SP). Typo do AC5 pode ser commitado separadamente para facilitar review. |
| 2026-04-14 | @dev | **DIAGNÓSTICO CONFIRMADO — H1.** `frontend/lib/sectors.ts` define setor Software com `id: "software"` e `slug: "software"`. O backend (`sectors_data.yaml`) não tem ID `"software"` — tem `software_desenvolvimento` e `software_licencas`. A conversão `sectorSlug.replace(/-/g, '_')` mantém `"software"` inalterado, gerando 404 no endpoint `/v1/blog/stats/setor/software/uf/SP`. O frontend captura o 404 como `null` e exibe `stats?.total_editais ?? 0` → 0. **Fix:** Adicionado `SECTOR_SLUG_TO_BACKEND_ID` (mapa de aliases) exportado de `programmatic.ts`, aplicado em todas as 7 funções que geram sectorId a partir de slug. 4 setores corrigidos: `software`→`software_desenvolvimento`, `facilities`→`servicos_prediais`, `saude`→`medicamentos`, `transporte`→`transporte_servicos`. URLs de produção preservadas. AC5 (typo "O editais") não encontrado no código atual — string `{stats?.total_editais ?? 0} editais publicados...` está gramaticalmente correta e exibirá dados reais após fix H1. |
