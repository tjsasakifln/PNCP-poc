# STORY-BIZ-002: Upsell Plano Consultoria para CNAEs 70.2/74.9/82.9

**Priority:** P1 — ARPU lift 2.5x sobre Pro, zero fricção adicional
**Effort:** S (1-2 dias)
**Squad:** @dev + @data-engineer (detecção CNAE)
**Status:** Ready
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
- [ ] `backend/services/plan_recommender.py` novo módulo com função `detect_consultoria_profile(cnae_primary: str) -> bool`
- [ ] Retorna `True` se CNAE primário começa com `70.2`, `74.9` ou `82.9` (formato "XX.YY-Z" ou "XX.YY")
- [ ] Precisão alvo ≥90% (validar com sample de 20 CNAEs reais do DataLake)
- [ ] Fallback: se CNAE não preenchido no profile, retorna `False` (conservador)

### AC2: Endpoint /v1/user/recommended-plan
- [ ] `backend/routes/user.py` adiciona `@router.get("/user/recommended-plan")`
- [ ] Require auth
- [ ] Retorna `{ "plan_key": "smartlic_consultoria" | "smartlic_pro", "reason": "cnae_consultoria" | "default" }`
- [ ] Cache Redis 24h por `user_id` (não muda frequente)

### AC3: Página /planos destaca plano recomendado
- [ ] `frontend/app/planos/page.tsx` busca `recommended-plan` ao montar
- [ ] Plano recomendado ganha badge "Recomendado para você" + outline border primário
- [ ] Plano recomendado fica em posição destacada (leftmost ou primeiro na ordem mobile)
- [ ] Plano não-recomendado mantém visibilidade plena (não esconder, apenas priorizar visualmente)

### AC4: Banner durante trial (para consultorias)
- [ ] `frontend/components/ConsultoriaUpsellBanner.tsx` novo componente
- [ ] Aparece na topbar do dashboard quando: user em trial + `recommended_plan==='smartlic_consultoria'` + banner não foi dismissed
- [ ] Copy: "Você é uma consultoria. Com o plano Consultoria você atende até 20 CNPJs de clientes por R$ 997/mês — economia de 60% vs múltiplas licenças Pro. Ver detalhes →"
- [ ] Dismiss persistido em `localStorage.consultoria_banner_dismissed_ts` (TTL 7d — re-mostra depois)
- [ ] CTA "Ver detalhes" leva a `/planos?highlight=consultoria`

### AC5: Query param ?highlight=consultoria
- [ ] `/planos` respeita query param `highlight` para destacar plano específico com animação scroll
- [ ] Usado também em links de email / outreach

### AC6: Observabilidade
- [ ] Evento Mixpanel `consultoria_upsell_viewed` (props: `user_id`, `cnae`, `surface: "planos_page" | "banner"`)
- [ ] Evento Mixpanel `consultoria_upsell_dismissed` (props: `user_id`, `seconds_viewed`)
- [ ] Evento Mixpanel `consultoria_upsell_clicked` (props: `user_id`, `cta_label`)
- [ ] Evento Mixpanel `consultoria_plan_selected` no checkout (props: `user_id`, `was_recommended`)

### AC7: Testes
- [ ] `backend/tests/test_plan_recommender.py` — 15+ casos (CNAEs válidos, inválidos, vazios, formatos variados)
- [ ] `frontend/__tests__/components/ConsultoriaUpsellBanner.test.tsx`
- [ ] `frontend/__tests__/planos/page.test.tsx` — com e sem recommended plan

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

_(populado pelo @dev durante execução)_

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Subsídios do plano Board v1.0. |
