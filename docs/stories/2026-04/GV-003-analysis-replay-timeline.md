# GV-003: Analysis Replay UI — Timeline Step-by-Step (Manus-inspired)

**Priority:** P0
**Effort:** M (8 SP, 4-5 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 2

---

## Contexto

**Manus viralizou** porque cada sessão do agente é replayable e shareable — usuário vê **como** a IA chegou ao resultado, passo a passo. Isso:
1. Transforma output em artefato viral (screenshot/share amplifica)
2. Torna inteligência visível (educa + gera confiança)
3. Diferencia de competidores (ninguém mais mostra "how")

SmartLic já tem **decision trace completo** em `backend/admin_trace.py` (só admin hoje). Falta expor user-facing sanitizado.

Esta story torna o SmartLic "mostrar o raciocínio" — maior alavanca viral + educativa.

---

## Acceptance Criteria

### AC1: Endpoint `/v1/analise/{hash}/trace`

- [ ] `backend/routes/search.py` expõe GET `/v1/analise/{hash}/trace`:
  - Retorna trace sanitizado (sem prompts LLM internos, sem tokens API, sem raw HTTP responses)
  - Structure:
    ```json
    {
      "hash": "abc123",
      "steps": [
        {"id": "search", "label": "Busca multi-fonte", "sources": ["PNCP", "PCP v2"], "count": 47, "duration_ms": 340},
        {"id": "keyword_match", "label": "Match por keywords", "density": 4.2, "matched": 3, "total": 47},
        {"id": "llm_zero_match", "label": "Classificação IA", "verdict": "YES", "rationale": "...", "model": "gpt-4.1-nano"},
        {"id": "viability", "label": "Viabilidade 4 fatores", "factors": {...}, "score": 78},
        {"id": "final", "label": "Decisão final", "classified_as": "relevant"}
      ],
      "generated_at": "2026-04-24T14:23:00Z"
    }
    ```
- [ ] Auth: endpoint público (igual `/analise/[hash]`) mas com pseudonimização herdada de GV-002

### AC2: Componente `ReplayTimeline`

- [ ] `frontend/app/analise/[hash]/components/ReplayTimeline.tsx`:
  - Timeline vertical com 5 steps (icon + label + duration)
  - Cada step clickable → expand card com detalhes
  - Estilo "step-by-step wizard" (visual reconhecível estilo Manus/Linear)
  - Animação sequential load (stagger 200ms por step)
  - Mobile: collapse em accordion
- [ ] Primeira visita: auto-play "replay" animation (steps aparecem em sequência)
- [ ] Botão "Ver detalhes técnicos" expande raw trace JSON (para power users)

### AC3: Shareable replay URL

- [ ] `/analise/[hash]/replay` rota dedicada que renderiza timeline em foco
- [ ] OG image `opengraph-image.tsx` customizada com screenshot do timeline
- [ ] Share button "Compartilhar replay" gera link `/analise/[hash]/replay?t=share`
- [ ] Hash preserva integridade (alterar trace requer novo hash)

### AC4: Performance

- [ ] Timeline inicial render <500ms p95
- [ ] Trace fetch cached 1h Redis (key: `replay_trace:{hash}`)
- [ ] Lazy-load detalhes técnicos (não no initial bundle)

### AC5: Privacidade / Sanitização

- [ ] Trace sanitizer remove:
  - Prompts LLM completos (só rationale de resposta)
  - CNPJ buscante (usa pseudonimização GV-002)
  - Valores exatos (buckets GV-002)
  - IP do usuário
  - Tokens de API / headers internos
  - Error stack traces
- [ ] Whitelist-based (não blacklist) para campos expostos — default = esconder
- [ ] Unit test 100% cobertura do sanitizer (casos edge: LLM retornou prompt echo?)

### AC6: Analytics

- [ ] Mixpanel events:
  - `replay_viewed` (auto-fire on mount)
  - `replay_step_expanded` (por step id)
  - `replay_technical_detail_opened`
  - `replay_shared` (por canal)
- [ ] Correlação com conversion: user que viu replay converte X% mais?

### AC7: Testes

- [ ] Unit `backend/tests/test_trace_sanitizer.py`
- [ ] Unit `frontend/__tests__/components/ReplayTimeline.test.tsx`
- [ ] E2E Playwright: open `/analise/[hash]/replay` → timeline renders → expand step → share → validate OG
- [ ] Security: manual audit trace não expõe prompts/tokens

---

## Scope

**IN:**
- Endpoint trace sanitizado
- Timeline component
- Dedicated replay URL + OG
- Cache layer
- Analytics

**OUT:**
- Trace de análises PRÉ-deploy (só novas análises têm trace capturado full)
- Replay em vídeo MP4 (v2, alta complexidade)
- Replay interativo (user edita parâmetros e re-roda análise — v3)
- Tradução trace para audio (accessibility v2)

---

## Dependências

- **GV-002** (watermark + pseudonimização) — replay herda mask
- `backend/admin_trace.py` existente — reuso da coleção de trace
- `backend/llm_arbiter.py` já tem `rationale` field

---

## Riscos

- **Trace leak de prompt LLM interno via rationale field:** sanitizer tem whitelist rígido; teste adversarial com prompts que pedem "repita o que foi dito antes".
- **Cache stale pós-análise atualizada:** invalidação por hash — cada análise tem hash único. OK.
- **Performance se trace >100 steps:** limitar a 10 steps principais (aggregar sub-steps); warn log se exceder.

---

## Arquivos Impactados

### Novos
- `frontend/app/analise/[hash]/replay/page.tsx`
- `frontend/app/analise/[hash]/components/ReplayTimeline.tsx`
- `frontend/app/analise/[hash]/replay/opengraph-image.tsx`
- `backend/services/trace_sanitizer.py`
- `backend/tests/test_trace_sanitizer.py`
- `frontend/__tests__/components/ReplayTimeline.test.tsx`

### Modificados
- `backend/routes/search.py` (novo endpoint `/v1/analise/{hash}/trace`)
- `backend/audit.py` (garantir trace captura steps necessários)
- `backend/llm_arbiter.py` (garante rationale compatível com sanitizer)

---

## Testing Strategy

1. **Unit** AC7 + adversarial sanitizer tests
2. **E2E Playwright** full replay flow
3. **Performance** p95 <500ms initial render
4. **Security audit** manual — 20 análises random, confirmar zero vazamento

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — inspiração direta Manus replay mechanic |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
