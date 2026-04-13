# SEO-471 — Sitemap licitacoes-indexable v2: incluir combos com contratos históricos

**Status:** Ready  
**Type:** Feature  
**Prioridade:** Alta — coerência entre noindex e sitemap  
**Depende de:** SEO-470 (noindex lógica deve estar alinhada)  
**Bloqueia:** —

## Problema

O endpoint `/v1/sitemap/licitacoes-indexable` retorna apenas combinações setor×UF onde `bids ≥ MIN_ACTIVE_BIDS_FOR_INDEX` (padrão: 5) nos últimos 30 dias. Com a mudança de noindex introduzida em SEO-470, páginas com `contracts ≥ 1` passam a ser indexáveis — mas o sitemap não as inclui. Resultado: Google não descobre nem crawla centenas de páginas com conteúdo válido.

**Exemplo concreto:** "Limpeza e Conservação no Amazonas" pode ter 0 editais abertos agora mas 240 contratos firmados no último ano. A página tem conteúdo rico (SEO-470), mas não aparece no sitemap → Google não crawla → não indexa.

## Solução

Expandir `_compute_indexable_combos` para retornar a **união** de dois conjuntos:
1. Combos com `bids ≥ MIN_BIDS_FOR_INDEX` no datalake (critério atual)
2. Combos com `contracts ≥ MIN_CONTRACTS_FOR_INDEX` em `pncp_supplier_contracts` (novo)

O desafio: `pncp_supplier_contracts` não tem coluna `setor_id` — apenas `objeto_contrato` (texto livre). A solução é uma nova RPC PostgreSQL que faz contagem via `ilike ANY(keywords)` por UF.

## Acceptance Criteria

- [ ] AC1: Endpoint retorna combos onde `bids ≥ MIN_BIDS_FOR_INDEX OR contracts ≥ MIN_CONTRACTS_FOR_INDEX`
- [ ] AC2: Nova RPC `count_contracts_by_setor_uf` criada no Supabase via migration
- [ ] AC3: RPC aceita `keywords text[], uf text` e retorna `count bigint`
- [ ] AC4: Backend executa 15 queries de setor (todas as UFs por setor) em paralelo via `asyncio.gather`
- [ ] AC5: Threshold `MIN_CONTRACTS_FOR_INDEX` configurável via env var (padrão: 1)
- [ ] AC6: Tempo de resposta total do endpoint ≤ 8s (build-time — tolerância maior que runtime)
- [ ] AC7: Cache 24h e endpoint admin de refresh mantidos e funcionais
- [ ] AC8: Response schema mantém backward compatibility (`combos`, `total`, `threshold`, `updated_at`)
- [ ] AC9: Log INFO reporta quantos combos vieram de bids e quantos de contratos
- [ ] AC10: `sitemap.ts` não requer mudança — consome o mesmo endpoint sem alterações

## Escopo

**IN:**
- `backend/routes/sitemap_licitacoes.py` — função `_compute_indexable_combos`
- `supabase/migrations/YYYYMMDD_rpc_count_contracts_setor_uf.sql` — nova RPC

**OUT:**
- Mudanças em `sitemap.ts` (frontend) — nenhuma necessária
- Mudanças nas páginas programáticas — SEO-470, SEO-472, SEO-473
- Outros endpoints de sitemap (cnpjs, orgaos) — fora do escopo

## Implementação — RPC

```sql
-- count_contracts_by_setor_uf(keywords text[], uf text) → bigint
-- Conta contratos em pncp_supplier_contracts cujo objeto_contrato
-- contém pelo menos uma das keywords E pertence à UF especificada.
CREATE OR REPLACE FUNCTION count_contracts_by_setor_uf(
    p_keywords text[],
    p_uf       text
)
RETURNS bigint
LANGUAGE sql
STABLE SECURITY DEFINER
SET search_path = public
AS $$
    SELECT COUNT(*)
    FROM pncp_supplier_contracts
    WHERE is_active = TRUE
      AND upper(uf) = upper(p_uf)
      AND EXISTS (
          SELECT 1 FROM unnest(p_keywords) AS kw
          WHERE objeto_contrato ILIKE '%' || kw || '%'
      );
$$;
```

## Implementação — Backend

```python
# Em _compute_indexable_combos:
# 1. Executar queries de bids (existente) → set de combos
# 2. Para cada setor, executar count_contracts_by_setor_uf por UF
#    → adicionar combos acima de MIN_CONTRACTS_FOR_INDEX
# 3. União dos dois conjuntos (dedup por setor+uf)
```

## Riscos

- **Performance da RPC:** `ilike` sem index de texto completo pode ser lento para 2M+ linhas. Mitigação: query executada por UF (limita escopo), cache 24h (executado apenas 1×/dia via ISR rebuild)
- **Keywords muito genéricas:** Setor "Serviços Gerais" pode ter keywords como "serviço" que matcham quase tudo. Mitigação: usar os primeiros 20 keywords mais específicos de cada setor (como o código atual de bids já faz)
- **False positives:** Contratos de outros setores podem ser matchados. Mitigação: aceitável — o objetivo é garantir que a página tenha algum dado relevante, não precisão perfeita

## Complexidade

**M** (2–3 dias) — nova RPC + lógica paralela no backend existente

## Critério de Done

- `GET /v1/sitemap/licitacoes-indexable` retorna > N combos que antes não retornava (validar com curl antes/depois)
- Combos novos têm `total_contracts ≥ 1` mas `total_bids < MIN_ACTIVE_BIDS_FOR_INDEX`
- Nenhum combo duplicado no response
- Testes unitários de `sitemap_licitacoes.py` passam

## File List

- [ ] `docs/stories/SEO-471-sitemap-licitacoes-indexable-v2-contratos.md` (esta story)
- [ ] `backend/routes/sitemap_licitacoes.py`
- [ ] `supabase/migrations/YYYYMMDD_rpc_count_contracts_setor_uf.sql`
