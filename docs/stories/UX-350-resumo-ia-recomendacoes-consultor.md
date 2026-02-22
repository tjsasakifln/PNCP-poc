# UX-350 — Resumo por IA com Timeout + Recomendacoes do Consultor com Contexto

**Status:** pending
**Priority:** P1 — Conteudo IA sem fechamento + sem contexto
**Created:** 2026-02-22
**Origin:** Auditoria UX area logada (2026-02-22-ux-audit-area-logada.md)
**Dependencias:** CRIT-027
**Estimativa:** M

---

## Problema

### Resumo por IA eterno
"Resumo por IA sendo preparado..." persiste indefinidamente. O usuario espera algo que nunca chega. O fallback (`gerar_resumo_fallback`) existe no backend mas o frontend nao faz timeout para usa-lo.

### Recomendacoes do Consultor sem contexto
- Nao deixa claro que sao inferencias de IA baseadas em perfil possivelmente INCOMPLETO
- Sem CTA para preencher perfil (que melhoraria a precisao)
- Sem link para ver edital na fonte oficial
- Texto sem acentuacao: "Recomendacoes do Consultor"

---

## Solucao

### Criterios de Aceitacao

**Resumo por IA**
- [ ] **AC1:** "Resumo por IA sendo preparado..." tem timeout de 30 segundos
- [ ] **AC2:** Apos timeout, exibir resumo fallback (puro Python, ja existe) com label "Resumo automatico"
- [ ] **AC3:** Se IA completar depois (SSE `llm_ready`), atualizar silenciosamente para "Resumo por IA"
- [ ] **AC4:** Se IA falhar, nenhuma mensagem de "preparando" permanece — fallback e o resultado final

**Recomendacoes do Consultor**
- [ ] **AC5:** Titulo corrigido: "Recomendacoes" → "Recomendacoes Estrategicas" (com acentuacao correta)
- [ ] **AC6:** Se perfil incompleto, banner amarelo: "Complete seu perfil para recomendacoes mais precisas" com link para /conta
- [ ] **AC7:** Cada oportunidade recomendada tem link "Ver edital na fonte oficial" (mesma logica de UX-348 AC4)
- [ ] **AC8:** Label discreto: "Analise gerada por IA com base no seu perfil e no edital" (transparencia)

**Testes**
- [ ] **AC9:** Teste: timeout de 30s mostra fallback
- [ ] **AC10:** Teste: SSE `llm_ready` apos timeout atualiza resumo
- [ ] **AC11:** Teste: perfil incompleto mostra banner com CTA
- [ ] **AC12:** Zero regressoes

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---------|---------|
| `frontend/hooks/useSearch.ts` | Timeout de 30s para `llm_ready`; fallback automatico |
| `frontend/app/buscar/components/SearchResults.tsx` | AC5-AC8 recomendacoes com contexto |
| `frontend/app/buscar/page.tsx` | Verificar se perfil esta completo |
| `frontend/__tests__/` | Testes AC9-AC12 |

---

## Referencias

- Audit: C04, H03
- GTM-RESILIENCE-F01: ARQ job para LLM summary
