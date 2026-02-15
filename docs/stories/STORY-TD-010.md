# STORY-TD-010: Decomposicao de search_pipeline.py

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 2: Consolidacao e Refatoracao

## Prioridade
P2 (elevado a HIGH pela QA por bloquear correcoes de pipeline)

## Estimativa
16h

## Descricao

`search_pipeline.py` se tornou um god module com 1318 linhas e 7 stages com helpers inline. Absorveu complexidade da decomposicao de `main.py` (STORY-202), movendo o problema de um arquivo para outro. E o segundo maior arquivo do backend apos `pncp_client.py` (1584 linhas).

**Problema:** Qualquer correcao em um stage individual da pipeline requer navegar por 1318 linhas. Testes de stages individuais sao dificeis. Novos desenvolvedores demoram a entender o fluxo.

**Solucao:** Decompor em modulos separados por stage:

```
backend/
  pipeline/
    __init__.py          # Pipeline orchestrator (entry point)
    stage_1_fetch.py     # PNCP fetch e paginacao
    stage_2_filter.py    # Filtragem fail-fast
    stage_3_dedupe.py    # Deduplicacao
    stage_4_arbiter.py   # LLM Arbiter
    stage_5_enrich.py    # Enriquecimento de dados
    stage_6_cache.py     # Cache de resultados
    stage_7_report.py    # Geracao de relatorio
    helpers.py           # Helpers compartilhados (se houver)
```

Cada stage deve ser independentemente testavel como funcao pura ou com mocks minimos. O orchestrator coordena a sequencia e error handling.

## Itens de Debito Relacionados
- SYS-11 (HIGH): `search_pipeline.py` god module (1318 linhas) -- 7 stages com helpers inline

## Criterios de Aceite

### Decomposicao
- [ ] `search_pipeline.py` original substituido por diretorio `pipeline/`
- [ ] Nenhum arquivo no diretorio `pipeline/` excede 300 linhas
- [ ] Orchestrator (`__init__.py` ou `orchestrator.py`) < 200 linhas
- [ ] Cada stage e um modulo independente com interface clara (input/output tipados)
- [ ] Imports entre stages sao unidirecionais (nenhum import circular)

### Funcionalidade
- [ ] Pipeline de busca funciona identicamente antes e depois da decomposicao
- [ ] Error handling por stage preservado (cada stage pode falhar independentemente)
- [ ] Progress tracking (SSE callbacks) preservado
- [ ] Circuit breaker e retry preservados em stages que os utilizam
- [ ] Performance: pipeline com 500 items executa em < 10s end-to-end

### Testes
- [ ] Testes existentes de `search_pipeline` atualizados para nova estrutura
- [ ] Pelo menos 1 teste unitario por stage
- [ ] Coverage do diretorio `pipeline/` >= 80%

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| PERF-T06 | search_pipeline 7 stages com 500 items < 10s | Benchmark | P2 |
| -- | Cada stage testavel independentemente com mocks | Unitario | P2 |
| -- | Pipeline completa E2E funciona pos-decomposicao | Integracao | P2 |

## Dependencias
- **Blocks:** Nenhuma diretamente, mas facilita TODAS as correcoes futuras de pipeline
- **Blocked by:** Nenhuma (independente)

## Riscos
- **CR-10:** Com 1318 linhas, qualquer decomposicao e inherentemente arriscada. Testar extensivamente.
- Risco de introducao de bugs em imports/interfaces entre stages.
- E2E tests devem servir como safety net durante a decomposicao.

## Rollback Plan
- Manter `search_pipeline.py` original como backup durante decomposicao.
- Se pipeline quebrar: reverter para arquivo monolitico e iterar.
- Feature flag possivel: `USE_NEW_PIPELINE=true/false` para transicao gradual.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + integracao + benchmark)
- [ ] CI/CD green
- [ ] Backend coverage >= 96%
- [ ] Documentacao atualizada (arquitetura da pipeline)
- [ ] Deploy em staging verificado
- [ ] Busca completa testada em producao
