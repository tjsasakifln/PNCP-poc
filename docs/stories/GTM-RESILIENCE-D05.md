# GTM-RESILIENCE-D05 — User Feedback Loop para Melhoria Contínua de Classificação

| Campo | Valor |
|-------|-------|
| **Track** | D — Classificação de Precisao |
| **Prioridade** | P1 |
| **Sprint** | 4 |
| **Estimativa** | 6-8 horas (backend 3h + frontend 3h + testes 2h) |
| **Gaps Endereçados** | CL-04 |
| **Dependências** | GTM-RESILIENCE-D02 (confidence_score para contexto), Supabase (persistência) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O sistema atual nao tem mecanismo para o usuario corrigir classificações. Quando uma licitação e incorretamente incluída (falso positivo) ou excluída (falso negativo percebido), nao ha canal de feedback. Os ajustes de keywords e exclusões sao feitos manualmente pela equipe com base em observação, sem dados estruturados de qualidade das classificações.

### Ciclo atual (sem feedback):

```
Keywords definidos pela equipe
  → Classificação automática
    → Resultados entregues ao usuario
      → Usuario percebe FP/FN
        → [NADA ACONTECE]
          → Mesmos FP/FN na próxima busca
```

### Ciclo proposto (com feedback):

```
Keywords definidos pela equipe
  → Classificação automática
    → Resultados entregues ao usuario
      → Usuario marca FP/FN (thumbs up/down)
        → Feedback persistido no Supabase
          → Análise de padrões (semanal)
            → Sugestões de keywords/exclusões
              → Equipe revisa e aplica
                → Classificação melhora
```

### Volume esperado de feedback:
- ~1% dos resultados recebem feedback (benchmark de produtos similares)
- Com ~100 resultados/busca e ~50 buscas/dia = ~50 feedbacks/dia
- Após 30 dias: ~1500 feedbacks = base estatisticamente significativa para detectar padrões

## Problema

Sem user feedback estruturado, o sistema nao tem como detectar degradação de qualidade, identificar padrões de falsos positivos/negativos, ou medir satisfação com as classificações. A equipe opera "no escuro" quanto a precisão real percebida pelos usuarios.

## Solução

Implementar endpoint de feedback por licitação, UI de thumbs up/down nos resultados, persistência no Supabase, e análise de padrões com sugestões de melhoria. O feedback e informativo (nao altera classificações em tempo real), mas alimenta um processo de melhoria contínua.

---

## Acceptance Criteria

### AC1 — Endpoint de Feedback
- [ ] `POST /v1/feedback` com body JSON:
  ```json
  {
    "search_id": "uuid",
    "bid_id": "string",
    "user_verdict": "false_positive" | "false_negative" | "correct",
    "reason": "string (optional, max 500 chars)",
    "category": "wrong_sector" | "irrelevant_modality" | "too_small" | "too_large" | "closed" | "other"
  }
  ```
- [ ] Autenticação obrigatória (require_auth dependency)
- [ ] Rate limit: max 50 feedbacks por usuario por hora (prevenir abuse)
- [ ] Resposta: `201 Created` com `{"id": "uuid", "received_at": "iso8601"}`
- [ ] Validação: `search_id` deve existir no cache ou historico de buscas do usuario
- [ ] Validação: `bid_id` deve existir nos resultados daquela busca (se possível verificar — best effort)

### AC2 — Schema de Persistência (Supabase)
- [ ] Nova tabela `classification_feedback`:
  ```sql
  CREATE TABLE classification_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    search_id UUID NOT NULL,
    bid_id TEXT NOT NULL,
    setor_id TEXT NOT NULL,
    user_verdict TEXT NOT NULL CHECK (user_verdict IN ('false_positive', 'false_negative', 'correct')),
    reason TEXT,
    category TEXT CHECK (category IN ('wrong_sector', 'irrelevant_modality', 'too_small', 'too_large', 'closed', 'other')),
    bid_objeto TEXT,
    bid_valor DECIMAL,
    bid_uf TEXT,
    confidence_score INTEGER,
    relevance_source TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
  );
  ```
- [ ] Index em `(setor_id, user_verdict, created_at)` para queries de análise
- [ ] Index em `(user_id, created_at)` para rate limiting
- [ ] RLS policy: usuario so pode inserir/ler seus proprios feedbacks
- [ ] Migration file: `backend/migrations/0XX_classification_feedback.sql`

### AC3 — Contexto Capturado com Feedback
- [ ] Ao salvar feedback, capturar do contexto da busca: `setor_id`, `bid_objeto` (truncado 200 chars), `bid_valor`, `bid_uf`
- [ ] Capturar do pipeline: `confidence_score`, `relevance_source` (keyword/llm_standard/llm_zero_match/item_inspection)
- [ ] Esses campos permitem análise sem precisar re-consultar a busca original
- [ ] Se contexto nao disponível (busca expirou do cache): salvar com campos null (nao bloquear feedback)

### AC4 — Frontend: Botões de Feedback por Resultado
- [ ] Cada card de resultado da busca ganha ícones de feedback: thumbs-up (correto) e thumbs-down (incorreto)
- [ ] Ao clicar thumbs-down, dropdown aparece com opções de categoria:
  - "Setor errado" (wrong_sector)
  - "Modalidade irrelevante" (irrelevant_modality)
  - "Valor muito baixo" (too_small)
  - "Valor muito alto" (too_large)
  - "Ja encerrada" (closed)
  - "Outro motivo" (other) — abre campo de texto livre (max 200 chars)
- [ ] Ao clicar thumbs-up, feedback "correct" e enviado diretamente (sem dropdown)
- [ ] Após enviar feedback, ícone muda de estado: cinza → verde (correct) ou vermelho (FP) com checkmark
- [ ] Estado de feedback persistido no localStorage por `search_id:bid_id` (evitar re-submit)
- [ ] Toast de confirmação: "Feedback recebido. Obrigado por nos ajudar a melhorar!"

### AC5 — Deduplicação e Idempotência
- [ ] Se usuario envia feedback duplicado para mesmo `search_id + bid_id`: upsert (substitui o anterior)
- [ ] Unique constraint em `(user_id, search_id, bid_id)` — um feedback por bid por busca por usuario
- [ ] Se usuario muda de "correct" para "false_positive": atualiza o registro existente
- [ ] Resposta inclui `updated: true` quando foi upsert em vez de insert

### AC6 — Endpoint de Análise de Padrões (Admin)
- [ ] `GET /v1/admin/feedback/patterns?setor_id=vestuario&days=30` (requer role admin)
- [ ] Resposta:
  ```json
  {
    "total_feedbacks": 150,
    "breakdown": {
      "correct": 120,
      "false_positive": 25,
      "false_negative": 5
    },
    "precision_estimate": 0.83,
    "fp_categories": {
      "wrong_sector": 15,
      "irrelevant_modality": 5,
      "too_small": 3,
      "other": 2
    },
    "top_fp_keywords": [
      {"keyword": "uniformização", "count": 8, "suggestion": "adicionar co-occurrence com 'fachada'"},
      {"keyword": "padronização", "count": 4, "suggestion": "verificar contexto visual/textil"}
    ],
    "suggested_exclusions": [
      "uniformização de fachada",
      "padronização visual"
    ]
  }
  ```
- [ ] `top_fp_keywords` calculado: extrair keywords do setor que aparecem nos `bid_objeto` dos FPs mais frequentes
- [ ] `suggested_exclusions` calculado: bi-grams mais frequentes nos FPs que nao aparecem nos "correct"

### AC7 — Sugestões de Melhoria de Keywords
- [ ] Algoritmo de sugestão analisa feedbacks dos últimos 30 dias por setor
- [ ] Se um keyword aparece em >5 FPs e <2 corrects: sugerir exclusão ou co-occurrence rule
- [ ] Se um termo aparece em >3 FNs (usuario marcou como relevante mas sistema rejeitou): sugerir como novo keyword
- [ ] Sugestões sao apenas recomendações — nao alteram keywords automaticamente
- [ ] Sugestões incluem contagem e exemplos para justificar a recomendação

### AC8 — QA Dashboard Integration
- [ ] Painel admin existente (futuro) pode consumir endpoint de patterns
- [ ] Dados de feedback incluídos no QA audit log existente (10% sampling)
- [ ] Quando bid tem feedback do usuario E decisão do LLM, logar comparação: `"LLM=SIM, user=false_positive"` para calibração

### AC9 — Privacy e LGPD
- [ ] Feedback associado a `user_id` (nao email) para pseudonimização
- [ ] Campo `reason` (texto livre) nao e indexado nem usado em analytics automatizado (evitar PII)
- [ ] Endpoint de delete: `DELETE /v1/feedback/{feedback_id}` para compliance com direito de exclusão
- [ ] Feedback mais antigo que 180 dias automaticamente anonimizado (user_id = null) via cron

### AC10 — Feature Flag
- [ ] `USER_FEEDBACK_ENABLED` env var (default `true`)
- [ ] Quando `false`: frontend nao mostra botões, endpoint retorna 503
- [ ] Flag adicionada ao `_FEATURE_FLAG_REGISTRY`

### AC11 — Testes Backend
- [ ] Teste unitário: POST /v1/feedback cria registro no Supabase
- [ ] Teste unitário: feedback duplicado faz upsert
- [ ] Teste unitário: rate limit de 50/hora funciona
- [ ] Teste unitário: search_id inválido retorna 404
- [ ] Teste unitário: usuario nao autenticado retorna 401
- [ ] Teste unitário: GET /v1/admin/feedback/patterns retorna breakdown correto
- [ ] Teste unitário: sugestão de exclusão gerada quando keyword aparece em >5 FPs
- [ ] Teste unitário: DELETE /v1/feedback/{id} remove registro

### AC12 — Testes Frontend
- [ ] Teste: thumbs-up envia feedback "correct" via API
- [ ] Teste: thumbs-down abre dropdown de categorias
- [ ] Teste: selecionar "Setor errado" envia feedback com category="wrong_sector"
- [ ] Teste: feedback persistido no localStorage impede re-submit
- [ ] Teste: estado visual muda após feedback enviado (cinza → verde/vermelho)
- [ ] Teste: toast de confirmação aparece após envio

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/routes/feedback.py` | **NOVO** — POST /v1/feedback, DELETE /v1/feedback/{id} |
| `backend/routes/admin.py` | GET /v1/admin/feedback/patterns |
| `backend/feedback_analyzer.py` | **NOVO** — lógica de análise de padrões e sugestões |
| `backend/main.py` | Registrar router de feedback |
| `backend/migrations/0XX_classification_feedback.sql` | **NOVO** — tabela + indexes + RLS |
| `backend/schemas.py` | FeedbackRequest, FeedbackResponse, FeedbackPatterns models |
| `backend/config.py` | `USER_FEEDBACK_ENABLED` flag |
| `frontend/app/buscar/components/FeedbackButtons.tsx` | **NOVO** — thumbs up/down + dropdown |
| `frontend/app/buscar/page.tsx` | Integração dos FeedbackButtons nos cards de resultado |
| `frontend/app/api/feedback/route.ts` | **NOVO** — proxy para backend |
| `backend/tests/test_feedback.py` | **NOVO** — testes backend (8+) |
| `frontend/__tests__/feedback-buttons.test.tsx` | **NOVO** — testes frontend (6+) |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Usuarios nao dão feedback (adoption <0.5%) | Alta | Medio | UX nao-intrusiva (1 click); gamification futura |
| Feedback enviesado (power users dominam) | Media | Medio | Ponderar por diversidade de usuarios na análise |
| Abuso de feedback (spam/trolling) | Baixa | Baixo | Rate limit 50/hora + autenticação obrigatória |
| Sugestões automatizadas geram exclusões incorretas | Media | Medio | Sugestões sao manuais — equipe sempre valida |
| Texto livre em "reason" contém PII | Media | Medio | Nao indexar, anonimizar >180 dias |

---

## Métricas de Sucesso

| Métrica | Target Sprint 4 | Target Sprint 8 |
|---------|------------------|------------------|
| Feedback rate (feedbacks / resultados exibidos) | >0.5% | >2% |
| Precision estimate (correct / total feedbacks) | Baseline | +5% vs baseline |
| Keywords melhorados a partir de feedback | 0 (coleta) | 5+ exclusões ou co-occurrence rules |
| Tempo médio para feedback (UI) | <3s | <2s |

---

## Definition of Done

- [ ] Todos os 12 ACs verificados e passando
- [ ] Nenhuma regressão nos testes existentes
- [ ] Coverage dos novos módulos >= 75%
- [ ] Migration de Supabase aplicada com sucesso
- [ ] RLS policy verificada (usuario X nao vê feedback de usuario Y)
- [ ] Frontend acessível (keyboard navigation nos botões de feedback)
- [ ] Feature flag permite desabilitar sem deploy
- [ ] LGPD compliance: delete endpoint funcional, anonimização configurada
- [ ] Code review aprovado por @architect e @ux-design-expert
