# STORY-260: Perfil de Licitante Expandido + Progressive Profiling

**Status:** Draft
**Priority:** P0 — Critical (Landing Page Parity)
**Track:** GTM — Go-to-Market Readiness
**Created:** 2026-02-23
**Depends on:** STORY-259 (análise LLM usa dados do perfil)

---

## Contexto

A landing page promete "analisa cada edital contra o **perfil da sua empresa**". Para que a análise LLM (STORY-259) seja realmente personalizada, o perfil precisa conter mais do que CNAE + UFs + faixa de valor.

### Perfil atual (onboarding GTM-004):

| Campo | Status | Onde |
|-------|--------|------|
| Setor (via CNAE) | ✅ Coletado | Onboarding step 1 |
| UFs de interesse | ✅ Coletado | Onboarding step 2 |
| Faixa de valor (min/max) | ✅ Coletado | Onboarding step 2 |

### Campos novos necessários:

| Campo | Impacto na Análise | Tipo |
|-------|-------------------|------|
| **Porte da empresa** (MEI/ME/EPP/Médio/Grande) | Modalidades elegíveis, faixas competitivas, exigências de habilitação | enum |
| **Atestados/certificações** | Capacidade técnica, editais elegíveis (CREA, CRF, INMETRO, ISO, etc.) | multi-select |
| **Experiência em licitações** | Calibrar recomendações (nunca participou → explicar mais; experiente → direto ao ponto) | enum |
| **Capacidade de atendimento** (funcionários + faturamento anual) | Cruzar com exigências de capacidade técnica e econômica dos editais | structured |

### Abordagem UX: Progressive Profiling

O usuário foca em **buscar editais, não alimentar formulários**. A coleta de dados do perfil deve ser:
- **1 pergunta por vez** — popup no dashboard, não formulário longo
- **Não-intrusiva** — pode ser ignorada/adiada
- **Valor claro** — cada pergunta explica como melhora a análise
- **Parabéns quando completo** — reforço positivo
- **Priorização inteligente** — campo com maior impacto na análise primeiro

---

## Acceptance Criteria

### Backend — Schema do Perfil Expandido

- [ ] **AC1:** Schema `PerfilContexto` em schemas.py ganha 4 campos novos (todos Optional):
  ```python
  # Novos campos
  porte_empresa: Literal["mei", "me", "epp", "medio", "grande"] | None = None
  atestados: list[str] | None = None  # ["crea", "crf", "inmetro", "iso_9001", "iso_14001", ...]
  experiencia_licitacoes: Literal["nunca", "iniciante", "intermediario", "experiente"] | None = None
  capacidade_funcionarios: int | None = None  # número de funcionários
  faturamento_anual: float | None = None  # em R$
  ```

- [ ] **AC2:** Endpoint `PUT /v1/profile/context` aceita os novos campos (já genérico via JSONB — verificar se PerfilContexto é validado no PUT)

- [ ] **AC3:** Novo endpoint `GET /v1/profile/completeness`:
  - Retorna:
    ```json
    {
      "completeness_pct": 60,
      "total_fields": 7,
      "filled_fields": 4,
      "missing_fields": ["porte_empresa", "atestados", "experiencia_licitacoes"],
      "next_question": "porte_empresa",
      "is_complete": false
    }
    ```
  - `next_question` segue prioridade fixa: porte → experiência → capacidade → atestados (campo com maior impacto primeiro)

- [ ] **AC4:** Lista de atestados/certificações predefinida em `config.py` ou `sectors_data.yaml`:
  ```python
  ATESTADOS_DISPONIVEIS = [
      {"id": "crea", "label": "CREA (Engenharia)", "sectors": ["engenharia", "manutencao_predial", "engenharia_rodoviaria"]},
      {"id": "crf", "label": "CRF (Farmácia)", "sectors": ["saude"]},
      {"id": "inmetro", "label": "INMETRO", "sectors": ["vestuario", "materiais_eletricos"]},
      {"id": "iso_9001", "label": "ISO 9001 (Qualidade)", "sectors": ["*"]},
      {"id": "iso_14001", "label": "ISO 14001 (Ambiental)", "sectors": ["*"]},
      {"id": "pgr_pcmso", "label": "PGR/PCMSO (Segurança)", "sectors": ["facilities", "vigilancia"]},
      {"id": "alvara_sanitario", "label": "Alvará Sanitário", "sectors": ["alimentos", "saude"]},
      {"id": "registro_anvisa", "label": "Registro ANVISA", "sectors": ["saude"]},
      {"id": "habilitacao_antt", "label": "Habilitação ANTT", "sectors": ["transporte"]},
      # ... expandir conforme setor
  ]
  ```
  Filtrada por setor do usuário no endpoint de completeness

- [ ] **AC5:** Dados do perfil expandido são passados para `batch_analyze_bids()` e `deep_analyze_bid()` (STORY-259) via `SearchContext.user_profile`

### Backend — Integração com Viability

- [ ] **AC6:** `viability.py` `calculate_value_fit()` usa `user_value_range` (faixa do perfil) com prioridade sobre `sector.viability_value_range`
- [ ] **AC7:** Se `porte_empresa` disponível, viability considera modalidades mais adequadas ao porte:
  - MEI/ME: bonus para Dispensa de Licitação, Pregão ≤ R$80k
  - EPP: bonus para licitações com cota reservada
  - Médio/Grande: bonus para Concorrência de alto valor
- [ ] **AC8:** Justificativas (STORY-259 fallback Python) refletem "do seu perfil" quando campo do perfil usado, "do setor" quando fallback

### Frontend — Progressive Profiling no Dashboard

- [ ] **AC9:** Componente `ProfileCompletionPrompt` (NOVO) no dashboard:
  - Exibe **1 pergunta por vez** baseado em `GET /v1/profile/completeness → next_question`
  - Layout: card com título da pergunta + input + botão "Salvar" + link "Pular por enquanto"
  - Após salvar: animação de sucesso + próxima pergunta no próximo acesso (não imediatamente)
  - Após pular: some com animação, reaparece no próximo acesso ao dashboard
  - Ordem de perguntas (prioridade de impacto):
    1. "Qual o porte da sua empresa?" — select com MEI/ME/EPP/Médio/Grande
    2. "Qual sua experiência com licitações?" — select com 4 níveis
    3. "Quantos funcionários e faturamento anual?" — 2 inputs numéricos
    4. "Quais atestados/certificações sua empresa possui?" — multi-select filtrado por setor

- [ ] **AC10:** Cada pergunta mostra **micro-copy explicando o impacto**:
  - Porte: "Saber seu porte permite filtrar editais com cota reservada para ME/EPP e modalidades adequadas"
  - Experiência: "Calibramos as recomendações ao seu nível — mais explicações para iniciantes, mais diretas para experientes"
  - Capacidade: "Cruzamos com exigências de capacidade técnica e econômica dos editais"
  - Atestados: "Identificamos editais que exigem certificações que você já possui"

- [ ] **AC11:** **Barra de progresso do perfil** — indicador visual discreto:
  - Porcentagem circular (similar ao profile completeness do LinkedIn)
  - Posicionado no header do dashboard ou como badge no menu
  - Cores: vermelho (<40%), amarelo (40-69%), verde (≥70%)
  - Clicável → abre a próxima pergunta

- [ ] **AC12:** **Parabéns (perfil completo)** — quando `is_complete: true`:
  - Card especial no dashboard: "Perfil completo! Suas análises agora são as mais precisas possíveis."
  - Confetti animation sutil (framer-motion, 2s duration)
  - Badge "Perfil Completo" permanente no dashboard (ícone shield/check verde)
  - Dismissível — não aparece novamente após fechar

- [ ] **AC13:** Link "Completar perfil" no dashboard aponta para `/conta` com seção expandida

### Frontend — Página de Perfil (/conta)

- [ ] **AC14:** Seção **"Perfil de Licitante"** na página `/conta`:
  - Todos os 7 campos editáveis (3 existentes + 4 novos)
  - Indicação visual de campos preenchidos vs. vazios
  - Salvar via `PUT /v1/profile/context`
  - Validação em tempo real (faixa valor min ≤ max, funcionários ≥ 0)

- [ ] **AC15:** Seção mostra **impacto do perfil**: "Seu perfil está X% completo. Campos preenchidos melhoram a precisão da análise de compatibilidade."

### Frontend — Indicadores de Personalização na Busca

- [ ] **AC16:** Se perfil incompleto e busca executada, **hint discreto** (não-modal) abaixo dos filtros:
  - "Complete seu perfil para análises mais precisas" + link para `/conta`
  - Dismissível via X, volta após 3 dias via localStorage
  - Não aparece se perfil completo

- [ ] **AC17:** Se perfil completo: badge "Análise personalizada" discreto nos resultados (tooltip: "Resultados otimizados para o perfil da sua empresa")

### Testes

- [ ] **AC18:** Backend: ≥12 testes em `test_profile_completeness.py`:
  - Completeness calculation (0%, 50%, 100%)
  - next_question priority order
  - PUT accepts new fields and validates
  - Atestados filtrados por setor
  - Viability uses user_value_range with priority
  - Porte impacts viability modality scoring
  - Edge cases: all None, partial fill, invalid porte

- [ ] **AC19:** Frontend: ≥10 testes em `progressive-profiling.test.tsx`:
  - ProfileCompletionPrompt renders 1 question
  - Save persists and triggers success animation
  - Skip hides prompt
  - Progress bar shows correct %
  - Congratulations shown when complete
  - ProfileSection in /conta shows all fields
  - Hint in busca shows/hides correctly

- [ ] **AC20:** Zero regressões nos testes existentes

### Backward Compatibility

- [ ] **AC21:** Todos os campos novos são **Optional** — usuários existentes continuam funcionando sem degradação
- [ ] **AC22:** Progressive profiling só aparece se `is_complete: false` — não incomoda quem já completou
- [ ] **AC23:** Se perfil vazio (sem onboarding): batch analysis (STORY-259) ainda funciona com dados do setor como fallback

---

## Architecture

### Progressive Profiling Flow

```
Dashboard
    ↓
GET /v1/profile/completeness
    ↓
{ next_question: "porte_empresa", completeness_pct: 43 }
    ↓
ProfileCompletionPrompt exibe pergunta sobre porte
    ↓
Usuário responde "EPP" → PUT /v1/profile/context { porte_empresa: "epp" }
    ↓
Sucesso! Próxima pergunta no PRÓXIMO acesso (não imediatamente)
    ↓
... repete até completeness_pct = 100 ...
    ↓
🎉 Card de parabéns + badge "Perfil Completo"
```

### Data Flow para Análise

```
profiles.context_data (JSONB)
    ↓
search_pipeline.py → PrepareSearch → carrega profile
    ↓
SearchContext.user_profile = {
    setor, porte, ufs, faixa_valor, atestados,
    experiencia, capacidade
}
    ↓
┌──────────────────────────────────────────┐
│ STORY-259: batch_analyze_bids(profile=…) │
│ STORY-259: deep_analyze_bid(profile=…)   │
│ viability.py: calculate_*(profile=…)     │
└──────────────────────────────────────────┘
    ↓
Análise personalizada com dados do perfil
```

### Priority Order (next_question)

| Prioridade | Campo | Impacto | Razão |
|-----------|-------|---------|-------|
| 1 | porte_empresa | Alto | Afeta modalidades elegíveis e exigências de habilitação |
| 2 | experiencia_licitacoes | Médio | Calibra tom e profundidade das recomendações |
| 3 | capacidade (funcionários + faturamento) | Alto | Cruza com qualificação econômica/técnica |
| 4 | atestados | Alto | Determina editais elegíveis por certificação |

---

## Estimativa

| Componente | Esforço |
|-----------|---------|
| Backend schema expansion | Baixo |
| Backend completeness endpoint | Baixo |
| Backend viability integration | Médio |
| Backend atestados catalog | Baixo |
| Frontend ProfileCompletionPrompt | Médio |
| Frontend progress bar + congrats | Médio |
| Frontend /conta profile section | Médio |
| Frontend busca hints | Baixo |
| Testes backend | Médio |
| Testes frontend | Médio |

---

## File List

| File | Action |
|------|--------|
| `backend/schemas.py` | MODIFY — expand PerfilContexto with 4 new fields |
| `backend/routes/user.py` | MODIFY — add GET /v1/profile/completeness |
| `backend/config.py` | MODIFY — ATESTADOS_DISPONIVEIS list |
| `backend/viability.py` | MODIFY — user_value_range priority, porte modality bonus |
| `backend/search_pipeline.py` | MODIFY — load full profile into SearchContext |
| `backend/search_context.py` | MODIFY — add user_profile field |
| `frontend/components/ProfileCompletionPrompt.tsx` | CREATE |
| `frontend/components/ProfileProgressBar.tsx` | CREATE |
| `frontend/components/ProfileCongratulations.tsx` | CREATE |
| `frontend/app/dashboard/page.tsx` | MODIFY — integrate ProfileCompletionPrompt |
| `frontend/app/conta/page.tsx` | MODIFY — add "Perfil de Licitante" section |
| `frontend/app/buscar/page.tsx` | MODIFY — profile hint |
| `frontend/app/api/profile-completeness/route.ts` | CREATE — API proxy |
| `backend/tests/test_profile_completeness.py` | CREATE |
| `frontend/__tests__/progressive-profiling.test.tsx` | CREATE |
