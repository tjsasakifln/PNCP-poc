# TFIX-000: Eliminação de Dívida Técnica de Testes Frontend

**Status:** Pending
**Prioridade:** Alta
**Objetivo:** Resolver ~50 testes falhando persistentes no frontend

## Resumo Executivo

Investigação de causa raiz concluída para 14 grupos de testes falhando. As falhas se consolidam em **5 categorias raiz**:

| Categoria | Stories | Testes afetados | Esforço |
|-----------|---------|-----------------|---------|
| **Acentos PT-BR ausentes no source** | TFIX-001 | ~7 | 1h |
| **EventSource mock incompleto** | TFIX-002 | ~2 | 2h |
| **Test-vs-code drift (textos)** | TFIX-005, 006, 007, 008, 012, 013 | ~12 | 2.5h |
| **Null safety / mocks incompletos** | TFIX-004, 009, 011 | ~15 | 1.5h |
| **Import-time failures (env/form)** | TFIX-003, 010 | ~13 | 1.5h |
| **Total** | **13 stories** | **~50 testes** | **~8.5h** |

## Ordem de Execução Recomendada

### Sprint 1 — Alta prioridade (impacto máximo, risco mínimo)

| # | Story | Falhas | Complexidade | Tipo |
|---|-------|--------|-------------|------|
| 1 | TFIX-001 | 7 | Baixa | Fix componente (acentos) |
| 2 | TFIX-005 | 1 | Trivial | Fix teste (1 linha) |
| 3 | TFIX-009 | 7 | Baixa | Fix componente + teste |
| 4 | TFIX-013 | 1 | Trivial | Fix teste (1 linha) |
| 5 | TFIX-010 | ? | Baixa | Fix teste (mock Supabase) |

### Sprint 2 — Média prioridade (mais contexto necessário)

| # | Story | Falhas | Complexidade | Tipo |
|---|-------|--------|-------------|------|
| 6 | TFIX-003 | 13 | Média | Reescrever helper teste |
| 7 | TFIX-011 | 4 | Média | Fix componente + teste |
| 8 | TFIX-004 | 4 | Média | Fix mock pattern |
| 9 | TFIX-002 | 2+ | Alta | Reescrever EventSource mock |

### Sprint 3 — Atualizações de texto

| # | Story | Falhas | Complexidade | Tipo |
|---|-------|--------|-------------|------|
| 10 | TFIX-006 | 5 | Baixa | Atualizar expectativas |
| 11 | TFIX-007 | 4 | Média | Investigar + atualizar |
| 12 | TFIX-008 | 6 | Média | Fix heading + timeouts |
| 13 | TFIX-012 | 1 | Trivial | Fix teste (1 texto) |

## Mapa de Falhas → Stories

| Grupo de Teste | Falhas | Story |
|----------------|--------|-------|
| download | 4 | TFIX-004 |
| error-messages | 1 | TFIX-005 |
| sector-sync | 1 | TFIX-003 |
| signup | 12 | TFIX-003 |
| degraded-visual | 3 | TFIX-001 |
| ux-transparente | 3 | TFIX-002 (2) + TFIX-012 (1) |
| sse-resilience | 1 | TFIX-013 (depende TFIX-001 para acentos) |
| operational-state | 4 | TFIX-011 |
| EnhancedLoadingProgress | 3 | TFIX-001 |
| BuscarHeader | 7 | TFIX-009 |
| InstitutionalSidebar | 5 | TFIX-006 |
| source-indicators | 4 | TFIX-007 |
| HistoricoPage | 6 | TFIX-008 |
| SearchForm | suite fail | TFIX-010 |

## Notas Importantes

1. **Todas as falhas são em testes, não em produção** — a aplicação funciona corretamente
2. **Componentes com acentos errados (TFIX-001)** são o único fix que melhora a UX real (accessibility)
3. **TFIX-009 (null safety)** previne potencial crash em produção se `saveSearchName` for undefined
4. **TFIX-011 (CoverageBar null guard)** previne crash se coverageMetadata for undefined
5. Após resolver todos os 13 stories, o baseline de falhas frontend deve cair de ~50 para ~0
