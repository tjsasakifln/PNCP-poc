# EXT-007: Integração no Search Pipeline

**Status:** Ready
**Origem:** EPIC-EXT-001 — Fontes Externas de Licitações
**Prioridade:** P1 — Alta (sem esta story, editais externos nunca aparecem para o usuário)
**Complexidade:** M (Medium) — ~10h
**Sprint:** EXT-sprint-03
**Owner:** @dev + @architect
**Tipo:** Backend + Frontend

---

## Problema

As stories EXT-001 a EXT-006 constroem o pipeline de ingestão de fontes externas, mas os resultados ficam em `external_bids` sem jamais aparecerem na busca do usuário. Esta story integra `external_bids` como camada de fallback no search pipeline, preservando a latência atual para a maioria dos usuários.

**Lógica de ativação:** `external_bids` é consultado APENAS quando o datalake principal (`pncp_raw_bids`) retornar menos de 10 resultados para a query do usuário. Isso garante zero impacto em buscas comuns que já têm cobertura adequada via PNCP.

---

## Critérios de Aceite

- [ ] **AC1:** Feature flag `EXTERNAL_BIDS_ENABLED` (padrão `False`) controla toda a integração — quando False, comportamento atual é 100% preservado
- [ ] **AC2:** Quando `EXTERNAL_BIDS_ENABLED=True` e datalake retorna < 10 resultados: `search_external_bids` RPC é chamada com mesmos filtros (query_text, uf, data_inicio, data_fim)
- [ ] **AC3:** Timeout de 3s para a query de `external_bids` — se exceder, retorna apenas os resultados do datalake sem erro para o usuário
- [ ] **AC4:** Merge de resultados: dedup por `content_hash` — se mesmo edital existe em datalake e external_bids, manter versão do datalake (`source_priority` menor)
- [ ] **AC5:** `LicitacaoItem` no schema de response inclui campo `source_type: Literal['datalake', 'external', 'live_api']`
- [ ] **AC6:** Endpoint SSE inclui novo event `external_ready` quando query de external_bids completa (pode chegar depois do `results_ready`)
- [ ] **AC7:** Frontend: resultado com `source_type='external'` exibe badge visual distinto (ex: "Fonte externa" em cinza claro) — implementar em componente `LlmSourceBadge` existente ou novo componente `ExternalSourceBadge`
- [ ] **AC8:** Métrica `smartlic_external_bids_served_total` incrementada quando external_bids contribui com resultados
- [ ] **AC9:** Métrica `smartlic_external_bids_query_latency_seconds` histogram para latência da query
- [ ] **AC10:** Testes backend: `pytest tests/test_search_external_integration.py` cobrindo cenários: flag off (sem consulta), flag on + < 10 datalake results, timeout de 3s, merge dedup
- [ ] **AC11:** Testes frontend: componente `ExternalSourceBadge` renderiza corretamente para `source_type='external'`

### Anti-requisitos

- Não consultar `external_bids` quando datalake retorna ≥ 10 resultados — preservar latência
- Não bloquear a response principal aguardando `external_bids` — usar timeout de 3s com fallback silencioso
- Não exibir `source_type` no UI para `source_type='datalake'` — apenas para 'external' (não introduzir complexidade visual desnecessária)
- Não alterar o search pipeline para fontes existentes (PNCP, PCP, ComprasGov)

---

## Tarefas

### Backend
- [ ] Adicionar `EXTERNAL_BIDS_ENABLED` a `backend/config.py`
- [ ] Criar `backend/search_external.py` com função `query_external_bids(query, filters, timeout=3.0) → list[LicitacaoItem]`
- [ ] Integrar em `backend/datalake_query.py` (ou `search_pipeline.py`) — após query datalake, se len < 10 e flag ativo, consultar external
- [ ] Adicionar `source_type` a `LicitacaoItem` em `backend/schemas.py`
- [ ] Adicionar event `external_ready` em `backend/progress.py`
- [ ] Adicionar métricas em `backend/metrics.py`
- [ ] Criar `backend/tests/test_search_external_integration.py`

### Frontend
- [ ] Adicionar `source_type` a tipo `LicitacaoItem` em `frontend/app/types.ts`
- [ ] Criar componente `ExternalSourceBadge` em `frontend/app/buscar/components/ExternalSourceBadge.tsx`
- [ ] Integrar badge em `SearchResults` — exibir apenas quando `source_type === 'external'`
- [ ] Lidar com event SSE `external_ready` (se resultados chegarem após `results_ready`, fazer append na lista)
- [ ] Adicionar teste do componente `ExternalSourceBadge`

---

## Referência de Implementação

```python
# backend/search_external.py

async def query_external_bids(
    query: str,
    filters: dict,
    timeout: float = 3.0,
) -> list[LicitacaoItem]:
    if not config.EXTERNAL_BIDS_ENABLED:
        return []
    try:
        async with asyncio.timeout(timeout):
            supabase = get_supabase()
            result = supabase.rpc("search_external_bids", {
                "query_text": query,
                "filters": filters,
            }).execute()
            items = [_to_licitacao_item(row, source_type="external") for row in result.data]
            metrics.external_bids_query_latency.observe(elapsed)
            return items
    except asyncio.TimeoutError:
        logger.warning("external_bids query timeout after %.1fs", timeout)
        return []
```

```typescript
// frontend/app/buscar/components/ExternalSourceBadge.tsx
export function ExternalSourceBadge() {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
      Fonte externa
    </span>
  );
}
```

- `datalake_query.py`: ver `query_datalake()` — integrar `query_external_bids()` após a chamada existente
- `schemas.py`: ver `LicitacaoItem` — adicionar `source_type: Literal['datalake', 'external', 'live_api'] = 'datalake'`
- SSE events: ver `backend/progress.py` — pattern de `emit_event(search_id, event_type, data)`
- Pydantic → TypeScript sync: após alterar `schemas.py`, rodar `npm --prefix frontend run generate:api-types` (conforme CLAUDE.md)

---

## Riscos

- **R1 (Médio):** Append de resultados `external_ready` no frontend após `results_ready` pode causar layout shift se lista já estiver visível. Mitigação: exibir spinner discreto "buscando fontes adicionais..." até `external_ready`; se não chegar em 3s, ocultar spinner silenciosamente.
- **R2 (Baixo):** `source_type` adicionado a `LicitacaoItem` quebra API types check CI se não rodar `generate:api-types` antes do commit. Incluir nas tarefas de dev.
- **R3 (Baixo):** Flag `EXTERNAL_BIDS_ENABLED=False` em produção no início — deploy seguro. Habilitar gradualmente após validar qualidade dos dados em external_bids.

---

## Dependências

- **EXT-001** — tabela `external_bids` com RPC `search_external_bids`
- **EXT-006** — `ExternalBidLoader` — external_bids deve ter dados para testar integração
- **EXT-003 ou EXT-004** — pelo menos um crawler ativo para popular external_bids em staging

---

## Arquivos Relevantes

| Arquivo | Ação |
|---------|------|
| `backend/config.py` | Atualizar (EXTERNAL_BIDS_ENABLED) |
| `backend/schemas.py` | Atualizar (source_type em LicitacaoItem) |
| `backend/datalake_query.py` | Atualizar (integrar query_external_bids) |
| `backend/search_external.py` | Criar |
| `backend/progress.py` | Atualizar (event external_ready) |
| `backend/metrics.py` | Atualizar |
| `backend/tests/test_search_external_integration.py` | Criar |
| `frontend/app/types.ts` | Atualizar (source_type) |
| `frontend/app/api-types.generated.ts` | Regenerar (npm run generate:api-types) |
| `frontend/app/buscar/components/ExternalSourceBadge.tsx` | Criar |
| `frontend/app/buscar/components/SearchResults.tsx` | Atualizar (exibir badge) |

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — EPIC-EXT-001 |
| 2026-04-23 | @po | Validação 10-pontos: **10/10 → GO** — melhor story do epic; business value explícito, ACs backend+frontend, feature flag de segurança. Status: Draft → Ready |
