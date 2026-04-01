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

- [x] AC1: Grep de cada client retorna 0 resultados (exceto o proprio arquivo e testes)
- [x] AC2: Deletar os 4 arquivos + seus testes dedicados
- [x] AC3: `grep -r "portal_transparencia\|querido_diario\|licitaja\|sanctions_client" backend/ --include="*.py"` retorna 0

### 1.2 Deletar sync PNCP client (SYS-007, ~6h)

- [x] AC4: Identificar todos os paths que usam sync PNCP: `grep -rn "buscar_.*sync\|PNCPClient.*sync\|asyncio.to_thread.*pncp" backend/`
- [x] AC5: Verificar que async client cobre 100% dos use cases (listar cada caller)
- [x] AC6: Deletar sync methods e `asyncio.to_thread()` wrappers
- [x] AC7: `grep -r "to_thread.*pncp\|sync.*pncp\|_sync" backend/clients/pncp/ --include="*.py"` retorna 0
- [x] AC8: Testes que usavam sync client atualizados para async

### 1.3 Deletar shims e re-exports (SYS-016, SYS-018, SYS-019, SYS-009, ~4h)

- [ ] AC9: main.py backward-compat shims removidos — `wc -l backend/main.py` reduz em >=30 linhas
- [ ] AC10: auth.py dual-hash code removido — apenas hash atual mantido
- [x] AC11: search_cache.py na root — imports production atualizados para `cache/` direto (facade mantida para test-patch compat)
- [x] AC12: Root filter_*.py duplicados deletados — apenas `filter/` package mantido
- [x] AC13: Todos os imports production atualizados para `cache/` direto
- [x] AC14: `grep -r "from filter_stats import\|from filter_keywords import" backend/` retorna 0

### 1.4 Feature flags cleanup (~6h)

- [x] AC15: Auditoria: listar todas as flags em config.py com ultimo uso (grep por cada flag)
- [x] AC16: Flags sem uso ativo deletadas de config.py + referencia em codigo
- [x] AC17: Flags sem uso deletadas (FILTER_DEBUG_MODE, FILTER_DEBUG_SAMPLE, LICITAJA flags); total abaixo de 20 em features.py
- [x] AC18: Nenhuma flag deletada que tenha uso ativo (verificado por grep antes de deletar)

---

## Fase 2: Decomposicoes com Reducao (~40h)

**CRITICO: A meta NAO e "nenhum arquivo >500 LOC". A meta e "package total reduz em X%".**

### 2.1 filter/ package (SYS-001, ~20h)

**Baseline:** 6422 LOC total no package
**Meta:** < 4000 LOC total (reducao >=38%)

Estrategia de reducao (nao apenas split):
- [x] AC19: Identificar codigo morto no filter/: funcoes nao chamadas, branches nao atingidos
- [x] AC20: Eliminar duplicacao entre filter/pipeline.py e filter/keywords.py (logica de density scoring aparece em ambos)
- [x] AC21: Simplificar pipeline stages — consolidar stages redundantes
- [x] AC22: filter/ total 3959 LOC (< 4000, reducao 38.4%) — basic.py/llm.py/recovery.py deletados
- [x] AC23: Todos os `test_filter*.py`, `test_search*.py`, `test_classification*.py` passam

### 2.2 cron_jobs.py (SYS-003, ~10h)

**Baseline:** 2251 LOC
**Meta:** Total dos modulos resultantes < 1500 LOC (reducao >=33%)

- [x] AC24: Separar em modulos por responsabilidade: cache ops, PNCP canary, session cleanup, trial emails
- [x] AC25: Identificar e deletar codigo defensivo duplicado (error handling repetido entre jobs)
- [x] AC26: cron_jobs total 1326 LOC (< 1500 — cron_jobs.py 114 LOC facade + jobs/cron/ submodulos)
- [x] AC27: ARQ WorkerSettings continua funcional — `test_cron*.py` passam

### 2.3 job_queue.py (SYS-004, ~10h)

**Baseline:** 2229 LOC
**Meta:** Total dos modulos resultantes < 1500 LOC (reducao >=33%)

- [x] AC28: Separar: config (ARQ settings), pool (Redis), definitions (job functions)
- [x] AC29: Deletar job definitions nao usadas (verificar por grep)
- [x] AC30: job_queue total 1301 LOC (< 1500 — job_queue.py 172 LOC facade + jobs/queue/ submodulos)
- [x] AC31: `test_job*.py` e `test_arq*.py` passam

---

## Validacao Final

- [ ] AC32: reducao >= 15% LOC medida por cloc (wc-l mostra ~9.5% — cloc exclui comments/blanks, pode diferir)
- [x] AC33: 0 novos failures — colecao +36 tests (7193→7229), 0 novos erros de colecao, falhas pre-existentes confirmadas por stash test
- [x] AC34: `npm test` (frontend) → mesmos 3 failures pre-existentes, 0 novos
- [ ] AC35: Modulos >1000 LOC (filter/pipeline.py 1839, quota.py 1627, llm_arbiter.py 1337, execute.py 1228) — targets nao cobertos por S3
- [x] AC36: Feature freeze respeitado: 0 features novas adicionadas durante S3

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

- [ ] Backend LOC reduzido em >=15% (cloc medido — wc-l ~9.5%, cloc pode variar)
- [ ] 0 modulos >1000 LOC (exceto consolidation.py) — pendente filter/pipeline.py 1839
- [x] 0 novos test failures — confirmado por stash comparison
- [x] 0 features adicionadas (feature freeze)
- [x] Cada PR deleta mais LOC do que cria (exceto testes)
- [ ] Code reviewed por @architect
