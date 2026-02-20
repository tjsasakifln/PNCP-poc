# CRIT-011: Migration search_sessions.search_id — Coluna Ausente

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 5: Resiliencia de Producao

## Prioridade
P1

## Estimativa
4h

## Descricao

O backend loga `CRIT-003: Startup recovery failed` a cada restart porque a tabela `search_sessions` nao possui a coluna `search_id`:

```
CRIT-003: Startup recovery failed: {'code': '42703', 'message': 'column search_sessions.search_id does not exist'}
```

### Impacto

- **Startup recovery de buscas stale:** Falha silenciosamente. Buscas que estavam em andamento quando o backend reiniciou nao sao recuperadas — ficam em estado "in_progress" para sempre na tabela.
- **Observabilidade:** Log de erro CRIT-003 aparece a cada restart, poluindo logs e criando ruido em alertas.
- **Correlacao de buscas:** Sem `search_id` na tabela `search_sessions`, nao e possivel correlacionar sessoes de busca com o SSE progress tracker, ARQ jobs, e cache entries.

### Contexto

A coluna `search_id` foi adicionada ao schema `BuscaRequest` (backend/schemas.py) como campo Optional na story GTM-FIX-031, mas a migration correspondente para a tabela `search_sessions` nunca foi criada. O codigo de startup recovery (`main.py` lifespan) tenta consultar essa coluna e falha.

### Evidencia

Log capturado ao vivo no Railway em 2026-02-20:
```
CRIT-003: Startup recovery failed: {'code': '42703', 'message': 'column search_sessions.search_id does not exist'}
```

O erro `42703` e o codigo PostgreSQL para "undefined_column".

## Criterios de Aceite

### Migration

- [ ] AC1: Criar migration `backend/migrations/008_add_search_id_to_search_sessions.sql`:
  ```sql
  -- Migration: Add search_id column to search_sessions table
  -- Reason: CRIT-003 startup recovery requires search_id for correlation
  -- Related: GTM-FIX-031 (search_id added to BuscaRequest schema)

  ALTER TABLE search_sessions
    ADD COLUMN IF NOT EXISTS search_id UUID DEFAULT NULL;

  -- Index for startup recovery query (find stale sessions by search_id)
  CREATE INDEX IF NOT EXISTS idx_search_sessions_search_id
    ON search_sessions (search_id)
    WHERE search_id IS NOT NULL;

  -- Index for cleanup of old sessions
  CREATE INDEX IF NOT EXISTS idx_search_sessions_status_created
    ON search_sessions (status, created_at)
    WHERE status = 'in_progress';

  COMMENT ON COLUMN search_sessions.search_id IS
    'UUID linking session to SSE progress tracker, ARQ jobs, and cache entries. Optional for backward compatibility.';
  ```

- [ ] AC2: Criar migration Supabase correspondente:
  ```bash
  npx supabase migration new add_search_id_to_search_sessions
  ```
  - Conteudo identico ao AC1
  - Arquivo destino: `supabase/migrations/YYYYMMDDHHMMSS_add_search_id_to_search_sessions.sql`

- [ ] AC3: Migration deve ser **idempotente** (`IF NOT EXISTS` em todos os statements)
  - Deve poder ser executada multiplas vezes sem erro
  - Deve funcionar em banco que ja tem a coluna (noop)

### Backend: Persistir search_id na Sessao

- [ ] AC4: O handler `/buscar` deve salvar `search_id` ao criar/atualizar a sessao de busca:
  - Identificar onde `search_sessions` e inserido/atualizado no fluxo de busca
  - Incluir `search_id` do `BuscaRequest` na operacao de insert/update
  - Se `search_id` nao fornecido pelo cliente (Optional), gerar um com `uuid.uuid4()`

- [ ] AC5: Startup recovery deve funcionar apos migration aplicada:
  - Verificar que o codigo de recovery em `main.py` lifespan consulta `search_id` corretamente
  - Recovery deve marcar sessoes stale (status='in_progress', created_at > 30min) como 'failed'
  - Log deve mudar de `CRIT-003: Startup recovery failed` para `Startup recovery: marked N stale sessions as failed`

- [ ] AC6: Startup recovery deve tratar coluna ausente gracefully (backward compatibility):
  - Se migration ainda nao foi aplicada: log warning e pular recovery (sem crashar)
  - Nao bloquear startup por causa de coluna ausente
  - Implementar com try/except no query, fallback para recovery sem search_id

### Limpeza de Sessoes Stale

- [ ] AC7: Adicionar cron job (ou startup task) para limpar sessoes stale:
  - Sessoes com `status='in_progress'` e `created_at` > 1 hora → marcar como `'timeout'`
  - Sessoes com `status IN ('failed', 'timeout')` e `created_at` > 7 dias → deletar
  - Frequencia: a cada startup + a cada 6 horas (alinhado com cache cleanup existente)
  - Log: `Session cleanup: marked {N} stale, deleted {M} old`

## Testes Obrigatorios

### Backend (pytest)

```bash
cd backend && python -m pytest tests/test_search_sessions.py -v --no-header
```

- [ ] T1: Migration SQL e valida (parse sem erro)
- [ ] T2: `search_id` salvo corretamente ao criar sessao de busca
- [ ] T3: Startup recovery marca sessoes stale como 'failed' (com search_id)
- [ ] T4: Startup recovery funciona sem coluna search_id (backward compatible — warning, nao crash)
- [ ] T5: Cleanup de sessoes stale: marca in_progress > 1h como timeout
- [ ] T6: Cleanup de sessoes stale: deleta failed/timeout > 7 dias
- [ ] T7: Migration idempotente (executar 2x sem erro)

### Pre-existing baselines
- Backend: ~35 fail / ~3924 pass
- Nenhuma regressao permitida

## Definicao de Pronto

- [ ] Todos os ACs implementados e checkboxes marcados
- [ ] 7 testes novos passando
- [ ] Zero regressoes no baseline
- [ ] Migration aplicada em producao (`npx supabase db push`)
- [ ] Log CRIT-003 desaparece apos deploy
- [ ] Startup recovery funcional (verificar nos logs)
- [ ] Story file atualizado com `[x]` em todos os checkboxes

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/migrations/008_add_search_id_to_search_sessions.sql` | Criar — migration |
| `supabase/migrations/YYYYMMDDHHMMSS_add_search_id_to_search_sessions.sql` | Criar — migration Supabase |
| `backend/main.py` | Modificar — startup recovery graceful, log melhorado |
| `backend/routes/search.py` ou `search_state_manager.py` | Modificar — persistir search_id na sessao |
| `backend/cron_jobs.py` | Modificar — adicionar session cleanup task |
| `backend/.env.example` | Nenhuma mudanca necessaria |
| `backend/tests/test_search_sessions.py` | Criar — testes T1-T7 |

## Notas Tecnicas

### Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|----------|
| Migration falha em producao | `IF NOT EXISTS` garante idempotencia; testar em staging primeiro |
| Coluna search_id NULL para sessoes antigas | NULL e esperado (campo Optional); recovery trata NULL gracefully |
| Lock na tabela durante ALTER TABLE | `ADD COLUMN ... DEFAULT NULL` e operacao leve no PostgreSQL (nao reescreve tabela) |
| Cron de cleanup deleta sessoes em uso | Guard: so deleta sessoes com created_at > 7 dias E status terminal |

### Ordem de Deploy
1. Aplicar migration no Supabase (`npx supabase db push`)
2. Verificar que coluna existe: `SELECT column_name FROM information_schema.columns WHERE table_name='search_sessions' AND column_name='search_id'`
3. Deploy backend com codigo atualizado
4. Verificar nos logs: CRIT-003 nao aparece mais

### Investigacao Previa
- [ ] Confirmar schema atual da tabela `search_sessions` em producao
- [ ] Verificar se ha outras colunas ausentes mencionadas em erros CRIT-*
- [ ] Verificar se `search_state_manager.py` ja tenta salvar search_id (e falha silenciosamente)

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Nenhuma bloqueante | — | Pode ser implementada independentemente |
| Habilitadora | CRIT-004 | search_id na sessao facilita correlacao ponta a ponta |
