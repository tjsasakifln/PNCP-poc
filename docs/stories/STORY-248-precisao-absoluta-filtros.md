# STORY-248: Precisão Absoluta de Filtros — Zero Falsos Positivos

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-248 |
| **Priority** | P2 |
| **Sprint** | Sprint 4 |
| **Estimate** | 12h |
| **Depends on** | STORY-242 (novos setores precisam de filtros precisos), STORY-241 (modalidades corretas) |
| **Blocks** | Nenhuma |

## Problema
O sistema de filtros (LLM arbiter + keywords + exclusões) é bom mas não perfeito. Usuários reportam:
- Falsos positivos: licitações que mencionam o termo mas não são do setor (ex: "uniforme" em contexto de padronização)
- Falsos negativos: licitações relevantes que não foram capturadas (ex: sinônimos regionais)

O objetivo é **zero falsos positivos visíveis ao usuário** e **minimizar falsos negativos**.

## Solução
Auditoria sistemática de todos os 15+ setores com dados reais do PNCP. Ajuste fino de keywords, exclusões, context_required_keywords e thresholds do LLM arbiter. Criação de test suite de "golden samples" por setor.

## Investigação Técnica

### Pipeline de Filtro Atual

```
Licitação bruta (PNCP)
  → UF filter (fail-fast)
  → Value range filter
  → Keyword matching (filter.py:597-743)
    → Normalização Unicode
    → Exclusion check (450+ termos)
    → Primary keyword search
    → Context validation (context_required_keywords)
  → LLM Arbiter (config.py:188-234)
    → Term density calculation
    → High density (>5%): auto-accept
    → Medium density (2-5%): LLM classification
    → Low density (<1%): auto-reject
  → Status/date validation
  → Max contract value check (STORY-179)
```

### Áreas de Fragilidade Identificadas

1. **Termos ambíguos sem context_required_keywords:** "mesa" (mobiliário vs mesa diretora), "banco" (mobiliário vs banco financeiro), "rede" (informática vs rede de proteção)
2. **Exclusões incompletas:** Novos padrões de falso positivo aparecem com novos setores
3. **LLM arbiter thresholds:** Ajustados em 2026-02-10, mas podem precisar refinamento por setor
4. **Sinônimos regionais não cobertos:** Termos usados em regiões específicas (Norte, Nordeste) podem estar ausentes

### Arquivos a Modificar

| Arquivo | Mudança |
|---------|---------|
| `backend/sectors_data.yaml` | Auditoria e ajuste de todos os setores |
| `backend/filter.py:282-497` | KEYWORDS_EXCLUSAO — adicionar novos padrões |
| `backend/config.py:207-219` | Ajustar thresholds se necessário por análise de dados |
| `backend/tests/test_filter.py` | Golden samples: 10 positivos + 10 negativos por setor |
| `backend/tests/test_golden_samples.py` | NOVO: test suite dedicado a golden samples |

### Metodologia
1. Para cada setor, buscar 100 licitações reais no PNCP
2. Classificar manualmente: relevante / irrelevante
3. Rodar filtro atual nos mesmos dados
4. Identificar falsos positivos e falsos negativos
5. Ajustar keywords/exclusões/context
6. Validar com golden samples automatizados

## Acceptance Criteria

### Golden Samples
- [ ] **AC1:** Arquivo `backend/tests/test_golden_samples.py` com pelo menos 5 amostras positivas e 5 negativas para cada setor existente.
- [ ] **AC2:** Todos os golden samples passam (0 falsos positivos, 0 falsos negativos nas amostras).
- [ ] **AC3:** Golden samples incluem casos de borda: termos ambíguos, texto muito longo, texto com erros ortográficos.

### Filtros — Keywords
- [ ] **AC4:** Todos os setores têm `context_required_keywords` para TODOS os termos de 1 palavra ambíguos.
- [ ] **AC5:** `KEYWORDS_EXCLUSAO` expandido com pelo menos 20 novos termos baseados na auditoria.
- [ ] **AC6:** Cada novo setor (STORY-242) tem pelo menos 15 exclusões validadas.

### Filtros — LLM Arbiter
- [ ] **AC7:** Thresholds revisados com base nos dados de auditoria. Se ajustados, documentar justificativa.
- [ ] **AC8:** QA audit sample rate mantido em 10% para monitoramento contínuo.

### Monitoramento
- [ ] **AC9:** Log structured de todos os rejects com reason code: `keyword_miss`, `exclusion_hit`, `llm_reject`, `density_low`, `value_exceed`.
- [ ] **AC10:** Endpoint `GET /v1/admin/filter-stats` retorna contagens de cada reason code nos últimos 7 dias.

### Regressão
- [ ] **AC11:** Testes existentes de filtro continuam passando.
- [ ] **AC12:** Nenhum setor existente tem redução na taxa de match (medido via golden samples).

## Definition of Done
- Todos os ACs checked
- Golden samples passam 100%
- `pytest` sem regressões
- Documentação de ajustes por setor
