# STORY-362 — Extend Result TTLs & Add Supabase L3 Persistence

**Status:** pending
**Priority:** P1 — Production (PDF/Excel "busca expirada" para buscas bem-sucedidas)
**Origem:** Conselho CTO Advisory — Analise de exports quebrados (2026-03-03)
**Componentes:** backend/routes/search.py, backend/config.py, supabase/migrations/
**Depende de:** nenhuma
**Bloqueia:** STORY-364 (Excel Resilience)
**Estimativa:** ~4h

---

## Contexto

Mesmo quando a busca completa com sucesso, os resultados expiram rapido demais:
- **L1 (in-memory):** `_RESULTS_TTL = 600` (10 minutos)
- **L2 (Redis):** `RESULTS_REDIS_TTL = 1800` (30 minutos)

Um usuario que demora mais de 10 minutos para clicar "PDF" ou "Excel" recebe "Busca nao encontrada ou expirada". Em cenarios reais, usuarios frequentemente analisam os resultados na tela por 15-30 minutos antes de exportar.

Adicionalmente, nao existe persistencia L3 (Supabase) para resultados de busca. Se o backend reiniciar (deploy), L1 e esvazia. Se o Redis reiniciar, L2 se esvazia. O usuario perde acesso aos resultados.

### Evidencia no Codigo

| Arquivo | Linha | Valor Atual | Problema |
|---------|-------|-------------|----------|
| `backend/routes/search.py` | 157 | `_RESULTS_TTL = 600` | 10 min in-memory — muito curto |
| `backend/config.py` | 888 | `RESULTS_REDIS_TTL = 1800` | 30 min Redis — curto para export flow |
| `backend/routes/reports.py` | 84-89 | `get_background_results_async()` → None → 404 | PDF falha se TTL expirou |
| `backend/routes/search.py` | 255-277 | L1 → L2 → L3(ARQ) fallback | Nao tem fallback Supabase |

## Acceptance Criteria

### TTL Extension

- [ ] **AC1:** Aumentar `_RESULTS_TTL` de 600 para 3600 (1h in-memory)
- [ ] **AC2:** Aumentar `RESULTS_REDIS_TTL` de 1800 para 14400 (4h Redis) via env var (manter retrocompatibilidade)
- [ ] **AC3:** Documentar novos TTLs no `.env.example`

### Supabase L3 Persistence

- [ ] **AC4:** Criar tabela `search_results_store` via migration:
  ```sql
  CREATE TABLE search_results_store (
    search_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    results JSONB NOT NULL,
    sector TEXT,
    ufs TEXT[],
    total_filtered INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT now() + INTERVAL '24 hours'
  );
  CREATE INDEX idx_search_results_user ON search_results_store(user_id);
  CREATE INDEX idx_search_results_expires ON search_results_store(expires_at);
  ALTER TABLE search_results_store ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Users can read own results" ON search_results_store
    FOR SELECT USING (auth.uid() = user_id);
  ```
- [ ] **AC5:** Apos `store_background_results()` + `_persist_results_to_redis()`, persistir tambem no Supabase (fire-and-forget, nao bloqueia resposta)
- [ ] **AC6:** `get_background_results_async()` ganha fallback L3: L1 → L2 → ARQ → Supabase
- [ ] **AC7:** Criar cron job para limpar resultados expirados (`expires_at < now()`) — rodar a cada 6h

### Validacao

- [ ] **AC8:** PDF funciona 2h apos a busca original (L1 expirou, L2 ativo)
- [ ] **AC9:** PDF funciona 6h apos a busca original (L1 e L2 expiraram, L3 Supabase ativo)
- [ ] **AC10:** Apos restart do backend, resultados ainda acessiveis via L2/L3
- [ ] **AC11:** Testes existentes passam sem regressao (patch de mocks se necessario)
- [ ] **AC12:** RLS impede usuario A de acessar resultados do usuario B

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/routes/search.py` | Aumentar `_RESULTS_TTL`, adicionar persist L3, fallback L3 em `get_background_results_async()` |
| `backend/config.py` | Aumentar `RESULTS_REDIS_TTL` default, adicionar `RESULTS_SUPABASE_TTL` |
| `supabase/migrations/XXXXXX_create_search_results_store.sql` | **NOVO** — tabela + RLS |
| `backend/cron_jobs.py` | Adicionar job de limpeza de resultados expirados |
| `.env.example` | Documentar novos env vars |

## Notas Tecnicas

- O JSONB `results` pode ser grande (~500KB para buscas com 200+ licitacoes). Monitorar tamanho medio e considerar compressao se necessario.
- Fire-and-forget para L3 persist: usar `asyncio.create_task()` como ja feito para `_update_session_on_complete()` em `search.py:1082`
- RLS policy usa `auth.uid()` — o endpoint `get_background_results_async()` e chamado com `require_auth`, entao o user_id esta disponivel
- Para o endpoint de reports/PDF que chama `get_background_results_async()`, o user_id do `require_auth` deve ser passado para o fallback L3 (necessario para RLS)
