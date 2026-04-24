# GV-015: "Concorrente Ganhou" Alert + Compare CTA

**Priority:** P2
**Effort:** M (8 SP, 4 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 4

---

## Contexto

User B2G tem forte interesse em monitorar concorrência. Se concorrente ganhou edital próximo ao perfil do user, é sinal de "perdida oportunidade" → FOMO acionável.

Loop viral secundário: se concorrente também é user SmartLic (possível em setor competitivo), AMBOS recebem alerts cruzados = FOMO compounding.

**Aviso:** copy sensível em B2G. Alto potencial backfire ("seu rival te derrotou" = agressivo demais). A/B test mandatório antes de broadcast.

---

## Acceptance Criteria

### AC1: Cadastro de competidores

- [ ] `frontend/app/settings/competidores/page.tsx`:
  - Form: CNPJ (max 5 free, ilimitado Pro+) + nickname opcional
  - Validação CNPJ formato + existe em `supplier_contracts`
  - Lista atual + remove action
- [ ] Migration:
  ```sql
  CREATE TABLE user_competitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    competitor_cnpj TEXT NOT NULL,
    nickname TEXT,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, competitor_cnpj)
  );
  ALTER TABLE user_competitors ENABLE ROW LEVEL SECURITY;
  ```

### AC2: Scanner diário

- [ ] `backend/jobs/cron/competitor_win_scanner.py`:
  - Trigger diário 6h BRT
  - Para cada (user, competitor): query `supplier_contracts` últimas 24h por CNPJ
  - Filter matches contra perfil user (setor, UF, valor range compatível)
  - Se match + ainda não alertado: trigger email + log
- [ ] Rate limit: max 1 alert por (user, competitor) por semana (não spam)

### AC3: Email alert

- [ ] `backend/templates/emails/competitor_won.html`:
  - Variants A/B subject line (mandatório, registrado em GV-001):
    - `control`: "{competitor_nickname} venceu uma licitação nesta semana"
    - `opportunity`: "Oportunidade perdida: empresa similar venceu {sector}"
    - `observatory`: "Movimento do mercado: {sector} em {UF}"
  - Body:
    - Dados do edital vencido (público)
    - Comparação: "Seu perfil matcha com X% deste edital"
    - 2 CTAs: "Ver compare completo" (→ `/compare?us=X&them=Y`) + "Configurar alertas similares"
- [ ] **A/B test obrigatório** com N mínimo 100 users antes de broadcast >100

### AC4: Página compare

- [ ] `frontend/app/compare/page.tsx`:
  - Query params `?us={cnpj1}&them={cnpj2}`
  - Pseudonimizada se acessada sem auth (pattern GV-002)
  - Lado-a-lado: histórico contratos, setores, valor total, UF distribution
  - Insights via LLM: "Concorrente tem 3x mais contratos em {setor}"
  - CTA "Tenha análise contínua — SmartLic Pro"

### AC5: Opt-out fácil

- [ ] Todo email tem footer "Desativar alertas de concorrente" — link 1-click
- [ ] Backend respeita opt-out granular por competidor ou global

### AC6: Tracking + Sentry alerting

- [ ] Mixpanel: `competitor_alert_sent`, `competitor_alert_opened`, `competitor_compare_viewed`, `competitor_alert_unsubscribed`
- [ ] Sentry alerta se unsubscribe rate > 10% (copy muito agressivo — halt broadcast)

### AC7: Testes

- [ ] Unit scanner logic
- [ ] Integration scanner end-to-end
- [ ] E2E Playwright: add competitor → simulate win (fixture) → receive email mock → open compare
- [ ] **Copy review manual** com @pm antes deploy (sensibilidade B2G)

---

## Scope

**IN:**
- Cadastro competidores
- Scanner diário
- Email alert A/B subject lines
- Compare page
- Opt-out 1-click
- Sentry alerting

**OUT:**
- Analytics profundos concorrente (histórico 10 anos) — v2
- Predição "concorrente vai ganhar próxima licitação" (ML futuro) — v3
- Compare múltiplos concorrentes simultâneos — v2

---

## Dependências

- **GV-001** (A/B framework) — variants subject line
- **GV-002** (pseudonimização) — compare page
- `supplier_contracts` tabela (~2M rows) existente

---

## Riscos

- **Copy backlash "seu rival te derrotou":** A/B test mandatório + manual review + unsubscribe 1-click + Sentry threshold
- **Privacy CNPJ terceiro:** CNPJ é dado público (Receita) mas agregações podem expor padrão — disclaimer "dados públicos do PNCP"
- **Scanner false positives:** match threshold conservative (só setor + UF exatos); não inflar alerts
- **LGPD — rastreamento CNPJ sem consentimento:** CNPJ empresa ≠ dado pessoal; mas notificar via termos explicitamente

---

## Arquivos Impactados

### Novos
- `frontend/app/settings/competidores/page.tsx`
- `frontend/app/compare/page.tsx`
- `backend/routes/competitors.py`
- `backend/jobs/cron/competitor_win_scanner.py`
- `backend/templates/emails/competitor_won.html`
- `supabase/migrations/YYYYMMDDHHMMSS_user_competitors.sql` (+ down)
- `backend/tests/test_competitor_scanner.py`

### Modificados
- `frontend/config/experiments.ts` (registra `gv_015_subject_line`)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — FOMO mechanic B2G; copy sensível, A/B mandatório |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. A/B subject mandatório + manual copy review @pm antes broadcast >100. Status Draft → Ready. |
