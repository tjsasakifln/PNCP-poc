# CRIT-013 — Migração search_state_transitions Ausente em Produção

**Status:** completed
**Priority:** P2 — Production (dados de auditoria não sendo persistidos)
**Origem:** Consultoria externa — Análise de logs Railway (2026-02-21)
**Componentes:** backend/search_state_manager.py, backend/quota.py, supabase/migrations/

---

## Contexto

Consultoria externa identificou nos logs de produção erros de PostgREST:

1. `PGRST205` — "Could not find the table `search_state_transitions`"
2. `PGRST204` — "Could not find the 'status' column of `search_sessions`" (em ambientes onde a migração lifecycle não foi aplicada)

**Causa raiz:** O backend possui migrações em `backend/migrations/` que **não têm correspondente** no diretório `supabase/migrations/`. Especificamente:

- `backend/migrations/008_search_state_transitions.sql` — cria a tabela de auditoria de transições de estado
- Essa tabela **nunca foi criada** no Supabase de produção

## Análise Técnica

### Estado Atual da Produção

| Componente | Existe em Produção? | Status |
|------------|---------------------|--------|
| `search_sessions` tabela | Sim | migração 001 |
| `search_sessions.search_id` | Sim | migração 20260220120000 |
| `search_sessions.status` | Sim | migração 20260221100000 |
| `search_sessions.pipeline_stage` | Sim | migração 20260221100000 |
| `search_sessions.error_message` | Sim | migração 20260221100000 |
| `search_state_transitions` tabela | **NÃO** | apenas em backend/008 |

### Impacto Funcional

O sistema **continua funcionando** porque os writes para `search_state_transitions` são fire-and-forget (nunca bloqueiam o pipeline). Porém:

| Funcionalidade | Status | Impacto |
|----------------|--------|---------|
| Busca funciona | OK | Pipeline não é bloqueado |
| Histórico de sessões | OK | `search_sessions` lifecycle columns existem |
| Status da busca | OK | `status`/`pipeline_stage` são atualizados |
| **Trilha de auditoria** | **FALHA SILENCIOSA** | Nenhuma transição de estado é registrada |
| **Debug de problemas** | **DEGRADADO** | Sem histórico de transições para investigar problemas |
| **Recovery de startup** | **PARCIAL** | `recover_stale_searches()` funciona mas sem transitions |

### Logs de Erro Observados

```
CRIT-003: Failed to persist state transition: {...} - PGRST205
CRIT-003: Failed to update session state: {...} - PGRST204  (se lifecycle migration não aplicada)
Transient error registering session for user xxx, retrying: {...}
```

## Acceptance Criteria

### Migração de Produção

- [x] **AC1:** Criar migração Supabase `supabase/migrations/YYYYMMDDHHMMSS_create_search_state_transitions.sql` com a tabela `search_state_transitions` (idêntica ao `backend/migrations/008_search_state_transitions.sql`)
- [x] **AC2:** A migração deve incluir: tabela, indexes (`idx_state_transitions_search_id`, `idx_state_transitions_to_state`), RLS policies (user-read, service-role-write)
- [x] **AC3:** Executar `npx supabase db push` para aplicar a migração em produção

### Validação PostgREST Schema Cache

- [x] **AC4:** Após aplicar a migração, forçar reload do schema cache do PostgREST via `NOTIFY pgrst, 'reload schema'` ou restart do serviço Supabase
- [ ] **AC5:** Verificar que `PGRST205` não aparece mais nos logs do backend (monitorar 1h após deploy)

### Limpeza de Migrações Backend

- [ ] **AC6:** Documentar em `backend/migrations/README.md` (ou criar se não existir) que migrações backend são **referência local** e que a fonte de verdade é `supabase/migrations/`
- [ ] **AC7:** Marcar `backend/migrations/007` e `backend/migrations/009` como duplicatas das migrações Supabase correspondentes (adicionar comentário no header de cada arquivo)

### Validação de Script

- [ ] **AC8:** Criar script `scripts/validate_migrations.py` que compara backend/migrations com supabase/migrations e reporta migrações ausentes em produção
- [ ] **AC9:** Script deve ser executável como `python scripts/validate_migrations.py` e retornar exit code 0 (ok) ou 1 (pendentes)

### Verificação de Dados

- [ ] **AC10:** Após aplicar a migração, fazer uma busca de teste em produção e verificar que `search_state_transitions` está sendo populada (query: `SELECT count(*) FROM search_state_transitions WHERE created_at > now() - interval '5 minutes'`)
- [ ] **AC11:** Zero regressões nos testes existentes (baseline: ~35 fail backend, ~50 fail frontend)

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `supabase/migrations/YYYYMMDDHHMMSS_create_search_state_transitions.sql` | NOVO — criar tabela |
| `backend/migrations/007_search_session_lifecycle.sql` | Adicionar comentário de duplicata |
| `backend/migrations/008_search_state_transitions.sql` | Referência (não alterar, apenas documentar) |
| `backend/migrations/009_add_search_id_to_search_sessions.sql` | Adicionar comentário de duplicata |
| `backend/migrations/README.md` | NOVO — documentar relação backend↔supabase |
| `scripts/validate_migrations.py` | NOVO — script de validação |

## Migração Proposta

```sql
-- supabase/migrations/YYYYMMDDHHMMSS_create_search_state_transitions.sql
-- Source: backend/migrations/008_search_state_transitions.sql
-- Story: CRIT-013

CREATE TABLE IF NOT EXISTS public.search_state_transitions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    search_id UUID NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    stage TEXT,
    details JSONB DEFAULT '{}',
    duration_since_previous_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_state_transitions_search_id
    ON public.search_state_transitions(search_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_to_state
    ON public.search_state_transitions(to_state);

ALTER TABLE public.search_state_transitions ENABLE ROW LEVEL SECURITY;

-- Users can read their own transitions (via search_sessions join)
CREATE POLICY "Users can read own transitions" ON public.search_state_transitions
    FOR SELECT USING (
        search_id IN (
            SELECT search_id FROM public.search_sessions
            WHERE user_id = auth.uid()
        )
    );

-- Service role can insert/update
CREATE POLICY "Service role can manage transitions" ON public.search_state_transitions
    FOR ALL USING (auth.role() = 'service_role');

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
```

## Referências

- CRIT-003 (State Machine Busca) — definiu a máquina de estados
- CRIT-001 (Alinhar Schema / Evitar Drift) — problema de schema drift
- `backend/search_state_manager.py` — código que depende desta tabela
- `backend/quota.py` — registro de sessões

## Definition of Done

- [ ] Tabela `search_state_transitions` existe em produção Supabase
- [ ] PostgREST schema cache atualizado (sem PGRST205)
- [ ] Transições de estado sendo persistidas em produção
- [ ] Script de validação de migrações funcional
- [ ] Backend migrations documentados como referência
- [ ] Zero regressões
- [ ] Logs limpos (sem PGRST204/PGRST205) por 24h
