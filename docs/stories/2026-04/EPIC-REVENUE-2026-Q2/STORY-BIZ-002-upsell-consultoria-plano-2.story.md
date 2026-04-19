# STORY-BIZ-002: Upsell Plano Consultoria para CNAEs 70.2/74.9/82.9

**Priority:** P1 — ARPU lift 2.5x sobre Pro, zero fricção adicional
**Effort:** S (1-2 dias)
**Squad:** @dev + @data-engineer (detecção CNAE)
**Status:** InReview
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Sprint:** Wave Receita D+8 a D+21

---

## Contexto

Plano **Consultoria R$ 997/mês** (R$ 897 semestral, R$ 797 anual) já existe em `plan_billing_periods` (Stripe + Supabase sincronizados). Mas:

- Não há CTA visível para ele dentro do app
- `/planos` mostra apenas SmartLic Pro como padrão
- Consultorias que usam SmartLic para atender múltiplos CNPJs economizam 60%+ com Consultoria vs N licenças Pro

Usuários com **CNAE primário de consultoria** são facilmente detectáveis:
- 70.20 — Atividades de consultoria em gestão empresarial
- 74.90 — Outras atividades profissionais científicas e técnicas
- 82.99 — Outras atividades de serviços prestados combinadas a empresas

Oferecer Consultoria como "Recomendado para você" + banner discreto durante trial cria upsell natural **zero friction**, sem alterar pricing geral.

**Impacto esperado:** 10-15% dos signups são consultorias. Se conversão trial→paid desta cohort for 20% (vs 3% geral) e ARPU é R$ 997 (vs R$ 397), lift em MRR: ~R$ 1.800-2.400 adicional em D+90.

---

## Acceptance Criteria

### AC1: Detecção de perfil consultoria
- [x] `backend/services/plan_recommender.py` implementa `detect_consultoria_profile(cnae_primary: str | None) -> bool` + `recommend_plan` + `_normalize_cnae`
- [x] Matching prefixo em `70.2`, `74.9`, `82.9` após normalização para `XX.YY` (aceita formatos `XX.YY-Z/NN`, `XX.YY-Z`, `XX.YY`, `XXYY-Z/NN`, `XXYY`)
- [x] Precisão validada em sample de 14 CNAEs (7 positivos + 7 negativos) — `test_detect_consultoria_sample_precision` exige >=90%
- [x] Fallback: CNAE vazio/None/malformado → `False` (user vê Pro como default — conservador)

### AC2: Endpoint /v1/user/recommended-plan
- [x] `backend/routes/user.py` adiciona `GET /user/recommended-plan` (via `@router.get("/user/recommended-plan")`)
- [x] `Depends(require_auth)` + `Depends(get_db)`
- [x] Retorna `{ "plan_key": "consultoria" | "smartlic_pro", "reason": "cnae_consultoria" | "default" }` (ajuste vs story original: o plan_id em Stripe é `consultoria`, não `smartlic_consultoria`)
- [x] Cache Redis 24h via `redis_pool.get_sync_redis().setex(...)` — fallback gracioso para sem-cache se Redis indisponível
- [x] Profile lookup em `profiles.cnae_primary` (nova coluna via migration `20260420000002_add_profiles_cnae_primary`)

### AC3: Página /planos destaca plano recomendado
- [x] `/planos?highlight=consultoria` aciona scroll-to + ring ring-indigo-400 de 3 segundos no card Consultoria (anchor `#plano-consultoria`)
- [ ] **(escopo reduzido nesta PR)** Badge "Recomendado para você" + outline no card recomendado — requer redesign dos componentes `PlanProCard`/`PlanConsultoriaCard` atuais. Ficará em story futura de polish visual. O banner no dashboard cobre o upsell primário; o highlight via query param cobre o deep-link de outreach.

### AC4: Banner durante trial (para consultorias)
- [x] `frontend/components/ConsultoriaUpsellBanner.tsx` novo componente
- [x] Renderizado no topo do dashboard (via `app/dashboard/layout.tsx`) apenas quando `isTrialing && recommended_plan==='consultoria' && reason==='cnae_consultoria' && !dismissed`
- [x] Copy textual exato: "Você é uma consultoria. Com o plano Consultoria você atende até 20 CNPJs de clientes por R$ 997/mês — economia de 60% vs múltiplas licenças Pro. Ver detalhes →"
- [x] Dismiss persistido em `localStorage.consultoria_banner_dismissed_ts` com TTL 7 dias — após TTL, banner re-aparece
- [x] CTA link para `/planos?highlight=consultoria` (scroll-to + ring via AC5)

### AC5: Query param ?highlight=consultoria
- [x] `/planos?highlight=consultoria` detectado via `useEffect` + `URLSearchParams` no `PlanosPage`
- [x] Scroll suave para `#plano-consultoria` + ring destacado por 3s (smooth behavior, block start)
- [x] Usado pelo CTA do `ConsultoriaUpsellBanner` — pronto para reuso em links de email/outreach

### AC6: Observabilidade
- [x] `consultoria_upsell_viewed { surface: 'banner' }` disparado no mount quando banner é visível
- [x] `consultoria_upsell_dismissed { surface: 'banner' }` disparado no click do botão Dispensar
- [x] `consultoria_upsell_clicked { cta_label: 'ver_detalhes' }` disparado no click do CTA
- [ ] **(escopo reduzido)** `consultoria_plan_selected { was_recommended }` no checkout — requer integração com fluxo de Stripe Checkout (gancho em `handleConsultoriaCheckout` em `/planos`). Fica para polish futuro; o evento `consultoria_upsell_clicked` + tracking de conversão Stripe já cobre o funil essencial.

### AC7: Testes
- [x] `backend/tests/test_plan_recommender.py` — 28 casos parametrizados (normalização CNAE, positivos, negativos, sample precision ≥90%, recommend_plan)
- [x] `backend/tests/test_recommended_plan_endpoint.py` — 6 casos (consultancy CNAE, non-consultancy, null, DB error, cache hit, cache miss write-through)
- [x] `frontend/__tests__/ConsultoriaUpsellBanner.test.tsx` — 8 casos (render, Mixpanel events, no-trial, non-consultancy, loading, dismiss + TTL)
- Nota: `frontend/__tests__/planos/page.test.tsx` não adicionado — escopo do highlight é só scroll behavior (testável por e2e Playwright em story futura); componentes visuais não mudaram.

---

## Arquivos

**Backend (novos + modificados):**
- `backend/services/plan_recommender.py` (novo)
- `backend/routes/user.py` (modificar — novo endpoint)

**Frontend (novos + modificados):**
- `frontend/components/ConsultoriaUpsellBanner.tsx` (novo)
- `frontend/app/planos/page.tsx` (modificar — highlighting + query param)
- `frontend/app/layout.tsx` ou `app/dashboard/layout.tsx` (modificar — render banner condicional)

**Tests:**
- `backend/tests/test_plan_recommender.py` (novo)
- `frontend/__tests__/components/ConsultoriaUpsellBanner.test.tsx` (novo)
- `frontend/__tests__/planos/page.test.tsx` (modificar ou novo)

---

## Riscos e Mitigações

**Risco 1:** CNAE primário não preenchido para muitos users (legado)
- **Mitigação:** AC1 `cnae_primary == None` retorna `False` (exibe Pro como default) — zero downside

**Risco 2:** Consultoria não adotar o plano (uso genuíno de Pro apenas para si)
- **Mitigação:** Banner dismissível com TTL 7d — não é aggressive

**Risco 3:** Falso positivo detecta empresa não-consultoria
- **Mitigação:** CNAEs 70.2/74.9/82.9 são específicos; se precisão <90% na validação de sample, refinar lista

---

## Definition of Done

- [ ] AC1-AC7 todos marcados `[x]`
- [ ] Deploy em produção
- [ ] ≥10 users classificados como consultoria ativos (via Mixpanel `consultoria_upsell_viewed`)
- [ ] ≥1 conversão ao plano Consultoria via surface Pro → Consultoria (via `consultoria_plan_selected { was_recommended: true }`)
- [ ] PR mergeado, CI verde

---

## Dev Notes

**Validação CNAE:**
- BrasilAPI `/api/cnpj/v1/{cnpj}` retorna `cnae_fiscal` (primário)
- Profile já armazena `cnae_primary` após onboarding (STORY-170)
- Se profile sem CNAE, chamar BrasilAPI no `recommended-plan` endpoint (com cache 30d)

**Sample de CNAEs para validar precisão AC1:**
```python
SAMPLE_CONSULTORIAS = ["70.20-4/00", "74.90-1/04", "82.99-7/00", "70.20-4/99"]
SAMPLE_NAO_CONSULTORIAS = ["62.01-5/01", "41.20-4/00", "47.71-7/01"]  # TI, construção, varejo
```

---

## File List

**Backend (novos):**
- `backend/services/plan_recommender.py` (pure functions: normalize, detect, recommend)
- `backend/tests/test_plan_recommender.py` (28 casos, sample precision ≥90%)
- `backend/tests/test_recommended_plan_endpoint.py` (6 casos, TestClient + dependency_overrides)

**Backend (modificados):**
- `backend/routes/user.py` (+`GET /user/recommended-plan` com Redis cache 24h)

**Frontend (novos):**
- `frontend/components/ConsultoriaUpsellBanner.tsx` (dismissible, localStorage TTL 7d)
- `frontend/hooks/useRecommendedPlan.ts` (fetch + cancel-on-unmount)
- `frontend/app/api/user/recommended-plan/route.ts` (Next proxy authenticated)
- `frontend/__tests__/ConsultoriaUpsellBanner.test.tsx` (8 casos)

**Frontend (modificados):**
- `frontend/app/dashboard/layout.tsx` (+ render do banner para trial users)
- `frontend/app/planos/page.tsx` (+ `useEffect` scroll-to-highlight + anchor `#plano-consultoria`)

**Database:**
- `supabase/migrations/20260420000002_add_profiles_cnae_primary.sql` (+ partial index p/ consultancy prefixes)
- `supabase/migrations/20260420000002_add_profiles_cnae_primary.down.sql`

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Subsídios do plano Board v1.0. |
| 2026-04-19 | @dev | Implementação code-side. 39 testes backend + 8 testes frontend passando. Resolvido gap vs story original: `profiles.cnae_primary` não existia — adicionado via migration nullable. Endpoint retorna `default` até onboarding persistir CNAE (story futura). Visual polish do `/planos` (badge/border) reduzido a scroll-to-highlight; banner é o surface primário do upsell. Status → InReview. |
