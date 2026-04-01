# Story: Simplificacao Real — Deletar Codigo

**Story ID:** DEBT-v3-S3
**Epic:** DEBT-v3 (Pre-GTM Technical Surgery)
**Sprint:** S3 (Dias 9-18)
**Priority:** P1
**Estimated Hours:** 60h
**Lead Decisoes:** @architect
**Lead Execucao:** @dev
**Validate:** @qa

---

## Objetivo

Reduzir o backend em >=15% de LOC real. Nao reorganizar, nao criar facades, nao adicionar camadas. Deletar codigo morto, eliminar duplicacoes, e decompor monolitos com meta de REDUCAO (nao movimentacao).

**Regra de ouro: nenhum PR pode criar mais LOC do que deleta (exceto testes).**

---

## Baseline (medir ANTES de iniciar)

```bash
# Rodar e registrar no inicio do sprint
cloc backend/ --exclude-dir=tests,venv,__pycache__ --json > /tmp/baseline-s3.json
echo "Baseline registrado em $(date)"
```

---

## Fase 1: Eliminacoes Diretas (~20h)

Codigo que pode ser deletado sem decomposicao. Baixo risco, alto impacto em LOC.

### 1.1 Deletar clients experimentais nao usados (SYS-017, ~4h)

| Client | LOC estimado | Verificacao |
|--------|-------------|-------------|
| portal_transparencia_client.py | ~300 | `grep -r "portal_transparencia" backend/ --include="*.py" -l` |
| querido_diario_client.py | ~200 | `grep -r "querido_diario" backend/ --include="*.py" -l` |
| licitaja_client.py | ~400 | `grep -r "licitaja" backend/ --include="*.py" -l` |
| sanctions_client.py | ~300 | `grep -r "sanctions" backend/ --include="*.py" -l` |

- [ ] AC1: Grep de cada client retorna 0 resultados (exceto o proprio arquivo e testes)
- [ ] AC2: Deletar os 4 arquivos + seus testes dedicados
- [ ] AC3: `grep -r "portal_transparencia\|querido_diario\|licitaja\|sanctions_client" backend/ --include="*.py"` retorna 0

### 1.2 Deletar sync PNCP client (SYS-007, ~6h)

- [ ] AC4: Identificar todos os paths que usam sync PNCP: `grep -rn "buscar_.*sync\|PNCPClient.*sync\|asyncio.to_thread.*pncp" backend/`
- [ ] AC5: Verificar que async client cobre 100% dos use cases (listar cada caller)
- [ ] AC6: Deletar sync methods e `asyncio.to_thread()` wrappers
- [ ] AC7: `grep -r "to_thread.*pncp\|sync.*pncp\|_sync" backend/clients/pncp/ --include="*.py"` retorna 0
- [ ] AC8: Testes que usavam sync client atualizados para async

### 1.3 Deletar shims e re-exports (SYS-016, SYS-018, SYS-019, SYS-009, ~4h)

- [ ] AC9: main.py backward-compat shims removidos — `wc -l backend/main.py` reduz em >=30 linhas
- [ ] AC10: auth.py dual-hash code removido — apenas hash atual mantido
- [ ] AC11: search_cache.py na root deletado — imports atualizados para `cache/` direto
- [ ] AC12: Root filter_*.py duplicados deletados — apenas `filter/` package mantido
- [ ] AC13: Todos os imports atualizados: `grep -r "from search_cache import\|import search_cache" backend/` retorna 0
- [ ] AC14: `grep -r "from filter_stats import\|from filter_keywords import" backend/` retorna 0

### 1.4 Feature flags cleanup (~6h)

- [ ] AC15: Auditoria: listar todas as flags em config.py com ultimo uso (grep por cada flag)
- [ ] AC16: Flags sem uso ativo deletadas de config.py + referencia em codigo
- [ ] AC17: `grep -c "_ENABLED\|_FEATURE\|_FLAG" backend/config.py` retorna < 20 (baseline: 45)
- [ ] AC18: Nenhuma flag deletada que tenha uso ativo (verificado por grep antes de deletar)

---

## Fase 2: Decomposicoes com Reducao (~40h)

**CRITICO: A meta NAO e "nenhum arquivo >500 LOC". A meta e "package total reduz em X%".**

### 2.1 filter/ package (SYS-001, ~20h)

**Baseline:** 6422 LOC total no package
**Meta:** < 4000 LOC total (reducao >=38%)

Estrategia de reducao (nao apenas split):
- [ ] AC19: Identificar codigo morto no filter/: funcoes nao chamadas, branches nao atingidos
- [ ] AC20: Eliminar duplicacao entre filter/pipeline.py e filter/keywords.py (logica de density scoring aparece em ambos)
- [ ] AC21: Simplificar pipeline stages — consolidar stages redundantes
- [ ] AC22: `wc -l $(find backend/filter -name "*.py")` mostra total < 4000 LOC
- [ ] AC23: Todos os `test_filter*.py`, `test_search*.py`, `test_classification*.py` passam

### 2.2 cron_jobs.py (SYS-003, ~10h)

**Baseline:** 2251 LOC
**Meta:** Total dos modulos resultantes < 1500 LOC (reducao >=33%)

- [ ] AC24: Separar em modulos por responsabilidade: cache ops, PNCP canary, session cleanup, trial emails
- [ ] AC25: Identificar e deletar codigo defensivo duplicado (error handling repetido entre jobs)
- [ ] AC26: `wc -l $(find backend/jobs/cron -name "*.py" 2>/dev/null || echo backend/cron_jobs.py)` mostra total < 1500 LOC
- [ ] AC27: ARQ WorkerSettings continua funcional — `test_cron*.py` passam

### 2.3 job_queue.py (SYS-004, ~10h)

**Baseline:** 2229 LOC
**Meta:** Total dos modulos resultantes < 1500 LOC (reducao >=33%)

- [ ] AC28: Separar: config (ARQ settings), pool (Redis), definitions (job functions)
- [ ] AC29: Deletar job definitions nao usadas (verificar por grep)
- [ ] AC30: `wc -l $(find backend/jobs -name "*.py" -not -path "*/cron/*" 2>/dev/null || echo backend/job_queue.py)` mostra total < 1500 LOC
- [ ] AC31: `test_job*.py` e `test_arq*.py` passam

---

## Validacao Final

- [ ] AC32: `cloc backend/ --exclude-dir=tests,venv,__pycache__ --diff /tmp/baseline-s3.json` mostra reducao >=15%
- [ ] AC33: `python scripts/run_tests_safe.py --parallel 4` → 0 novos failures vs baseline (7656+)
- [ ] AC34: `npm test` (frontend) → 0 novos failures (imports backend nao afetam FE, mas validar)
- [ ] AC35: Nenhum modulo individual > 1000 LOC (exceto consolidation.py que fica para futuro se necessario)
- [ ] AC36: Feature freeze respeitado: 0 features novas adicionadas durante S3

---

## Technical Notes

**Ordem de execucao:**
1. Medir baseline (cloc)
2. Fase 1 primeiro — eliminacoes diretas sao low-risk e mostram progresso rapido
3. Rodar suite completa apos Fase 1
4. Fase 2 — decomposicoes com reducao
5. Rodar suite completa apos cada modulo decomposto
6. Medir final (cloc --diff)

**Riscos e mitigacoes:**
- Deletar sync PNCP: verificar TODOS os callers antes. Se algum path depende de sync, manter temporariamente e documentar.
- Filter decomp: usar `__init__.py` re-exports durante transicao. Remover re-exports em commit separado apos confirmar que tudo funciona.
- Feature flags: NUNCA deletar flag sem grep exhaustivo. Falso positivo = feature quebrada em producao.

**Anti-patterns proibidos:**
- Criar "utils.py" ou "helpers.py" para mover codigo sem deletar
- Criar facades que wrappam o codigo original sem eliminar o original
- Adicionar camadas de abstracao "para facilitar futuras mudancas"
- Criar novos arquivos de configuracao para "governar" o que deveria ser deletado

---

## Definition of Done

- [ ] Backend LOC reduzido em >=15% (cloc medido)
- [ ] 0 modulos >1000 LOC (exceto consolidation.py)
- [ ] 0 novos test failures
- [ ] 0 features adicionadas (feature freeze)
- [ ] Cada PR deleta mais LOC do que cria (exceto testes)
- [ ] Code reviewed por @architect
